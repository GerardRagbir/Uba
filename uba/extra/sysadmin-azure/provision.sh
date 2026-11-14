#!/usr/bin/env bash
# ============================================================
# Provision UBA on Azure — the az CLI walkthrough
# ============================================================
# Read every line before running. This CREATES BILLABLE RESOURCES.
# Teardown at the end removes them all.
#
# Prereqs: az login  (and Docker running, to build the image)

set -euo pipefail

# --- settings you can change ---
RG="uba-demo-rg"              # resource group (a folder for all resources)
LOCATION="eastus"
PREFIX="uba"
IMAGE_TAG="1.0.0"

echo "==> 1. Resource group (a container for everything; delete it to delete all)"
az group create --name "$RG" --location "$LOCATION" --output table

echo "==> 2. Container registry (build its name is derived in Bicep; create one now for the image)"
# We create the ACR first so we have somewhere to push the image the Bicep will run.
ACR_NAME="${PREFIX}acr$(az group show -n "$RG" --query id -o tsv | md5 -q 2>/dev/null | cut -c1-8 || echo demo)"
az acr create --resource-group "$RG" --name "$ACR_NAME" --sku Basic --admin-enabled true --output table
LOGIN_SERVER=$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)

echo "==> 3. Build and push the backend image straight in ACR (no local Docker push needed)"
# 'az acr build' ships the build context to Azure and builds it there.
az acr build \
  --registry "$ACR_NAME" \
  --image "uba-backend:${IMAGE_TAG}" \
  --file ../../backend/Dockerfile \
  ../../backend

echo "==> 4. Secrets — generated now, passed to the deploy, stored in Key Vault by Bicep"
DB_PASSWORD="$(openssl rand -base64 24)"
JWT_SECRET="$(openssl rand -hex 32)"

echo "==> 5. Deploy the infrastructure (Bicep) — Postgres, Key Vault, logs, Container App"
az deployment group create \
  --resource-group "$RG" \
  --template-file main.bicep \
  --parameters \
      namePrefix="$PREFIX" \
      location="$LOCATION" \
      backendImage="${LOGIN_SERVER}/uba-backend:${IMAGE_TAG}" \
      dbPassword="$DB_PASSWORD" \
      jwtSecret="$JWT_SECRET" \
  --output table

echo "==> Done. The backend URL:"
az deployment group show -g "$RG" -n main --query properties.outputs.backendUrl.value -o tsv || true

cat <<'EOF'

Next:
  python ops.py status      # is it running?
  python ops.py logs        # stream logs
  curl https://<backendUrl>/api/health

Teardown (stops the bill — do this when you are finished):
  az group delete --name uba-demo-rg --yes --no-wait
EOF
