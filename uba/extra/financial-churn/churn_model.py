"""Predict which UBA passengers are about to churn.

Pipeline:
  1. pull per-passenger RFM features from the database (same logic as
     churn_features.sql),
  2. if there isn't enough real history, generate a realistic synthetic
     population so the technique can still be demonstrated,
  3. train a transparent logistic-regression model,
  4. report honest metrics and — crucially — WHICH features drive churn,
  5. list the live passengers most at risk.

Run:  python churn_model.py          # real data, synthetic fallback if sparse
      python churn_model.py --demo   # force synthetic data

Transparent on purpose: a churn score a retention team can act on must be
explainable. See this track's README.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURES = ["recency_days", "frequency", "monetary_ttd", "avg_fare_ttd",
            "cancellations", "thumbs_down", "tenure_days"]

FEATURE_SQL = """
WITH pax AS (SELECT id FROM users WHERE role='pax'),
trips AS (
  SELECT pax_id, count(*) AS frequency, sum(fare) AS monetary_ttd,
         round(avg(fare),1) AS avg_fare_ttd, max(created_at) AS last_trip,
         min(created_at) AS first_trip,
         count(*) FILTER (WHERE rating='down') AS thumbs_down
  FROM bookings WHERE status='completed' GROUP BY pax_id),
cancels AS (
  SELECT pax_id, count(*) AS cancellations FROM bookings
  WHERE status='cancelled' GROUP BY pax_id)
SELECT p.id AS pax_id,
       coalesce(t.frequency,0) AS frequency,
       coalesce(t.monetary_ttd,0) AS monetary_ttd,
       coalesce(t.avg_fare_ttd,0) AS avg_fare_ttd,
       coalesce(c.cancellations,0) AS cancellations,
       coalesce(t.thumbs_down,0) AS thumbs_down,
       CASE WHEN t.last_trip IS NOT NULL THEN extract(day FROM now()-t.last_trip)::int END AS recency_days,
       CASE WHEN t.first_trip IS NOT NULL THEN extract(day FROM now()-t.first_trip)::int END AS tenure_days,
       CASE WHEN t.last_trip IS NULL THEN NULL
            WHEN now()-t.last_trip > interval '30 days' THEN 1 ELSE 0 END AS churned
FROM pax p LEFT JOIN trips t ON t.pax_id=p.id LEFT JOIN cancels c ON c.pax_id=p.id
"""


def load_real() -> pd.DataFrame:
    from sqlalchemy import create_engine, text

    url = os.environ.get("UBA_DATABASE_URL",
                         "postgresql+psycopg://uba:uba-dev-password@postgres:5432/uba")
    engine = create_engine(url)
    df = pd.read_sql(text(FEATURE_SQL), engine)
    return df.dropna(subset=["churned"])  # drop never-active passengers


def make_synthetic(n: int = 2000, seed: int = 7) -> pd.DataFrame:
    """A believable population: loyal riders churn less than lapsing ones."""
    rng = np.random.default_rng(seed)
    frequency = rng.poisson(6, n) + 1
    tenure = rng.integers(30, 400, n)
    recency = rng.integers(0, 120, n)
    avg_fare = rng.integers(60, 200, n)
    monetary = frequency * avg_fare
    cancellations = rng.poisson(0.6, n)
    thumbs_down = rng.poisson(0.3, n)
    # The "truth" the model must recover: churn risk rises with recency and
    # cancellations, falls with frequency. Plus noise, so it isn't trivial.
    logit = (-2.0 + 0.045 * recency - 0.18 * frequency + 0.35 * cancellations
             + 0.2 * thumbs_down + rng.normal(0, 0.8, n))
    churned = (1 / (1 + np.exp(-logit)) > 0.5).astype(int)
    return pd.DataFrame({
        "pax_id": np.arange(1, n + 1), "recency_days": recency, "frequency": frequency,
        "monetary_ttd": monetary, "avg_fare_ttd": avg_fare, "cancellations": cancellations,
        "thumbs_down": thumbs_down, "tenure_days": tenure, "churned": churned,
    })


def main() -> None:
    force_demo = "--demo" in sys.argv
    source = "synthetic (forced)"
    if force_demo:
        df = make_synthetic()
    else:
        try:
            df = load_real()
            source = "real database"
        except Exception as error:  # noqa: BLE001
            print(f"(could not read the database: {error})")
            df = pd.DataFrame()
        # Need enough rows and both classes to learn anything.
        if len(df) < 50 or df["churned"].nunique() < 2:
            print("Not enough real history to train on — using synthetic data instead.\n")
            df = make_synthetic()
            source = "synthetic (fallback)"

    print("=" * 56)
    print(f"UBA churn model   (data: {source}, {len(df)} passengers)")
    print("=" * 56)

    X = df[FEATURES].fillna(0).to_numpy(dtype=float)
    y = df["churned"].to_numpy(dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=1, stratify=y)

    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression(max_iter=1000)
    model.fit(scaler.transform(X_train), y_train)

    proba = model.predict_proba(scaler.transform(X_test))[:, 1]
    preds = (proba >= 0.5).astype(int)

    print("\nHow good is it? (on held-out passengers it never saw)")
    print(classification_report(y_test, preds, target_names=["active", "churned"], zero_division=0))
    try:
        print(f"ROC-AUC: {roc_auc_score(y_test, proba):.3f}  (0.5 = guessing, 1.0 = perfect)")
    except ValueError:
        pass

    print("\nWhat drives churn? (standardised coefficients; + pushes toward churn)")
    for name, coef in sorted(zip(FEATURES, model.coef_[0]), key=lambda kv: abs(kv[1]), reverse=True):
        arrow = "↑ churn" if coef > 0 else "↓ churn"
        print(f"  {name:<16} {coef:+.3f}   {arrow}")

    # Score the whole population and show who to call first.
    df = df.copy()
    df["risk"] = model.predict_proba(scaler.transform(X))[:, 1]
    at_risk = df[df["churned"] == 0].sort_values("risk", ascending=False)
    print("\nStill-active passengers at highest risk (target these with an offer):")
    cols = ["pax_id", "recency_days", "frequency", "monetary_ttd", "risk"]
    print(at_risk[cols].head(10).to_string(index=False, float_format=lambda v: f"{v:.2f}")
          if not at_risk.empty else "  (none)")


if __name__ == "__main__":
    main()
