"use client";

import { useEffect, useState } from "react";

import { toPoint, useMapView } from "@/components/MapBackdrop";
import { Loading, Shell } from "@/components/Shell";
import { Button, Card, Notice, SelectField, StatusBadge, Table, Tabs, type NoticeState } from "@/components/ui";
import { api, messageFrom, type Booking, type Destination, type FareEstimate } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { useUser } from "@/lib/useUser";

const TABS = ["Book a ride", "My bookings", "Destinations and fares"];
// Pending first, finished at the bottom.
const ORDER = { pending: 0, accepted: 1, completed: 2, cancelled: 3 };

// One line of the fare breakdown: a reason and what it multiplied the price by.
// A multiplier of 1.0 means "no change", shown quietly.
function PriceLine({ label, mult }: { label: string; mult: number }) {
  const changed = mult !== 1;
  return (
    <li className={`flex justify-between ${changed ? "text-slate-600" : ""}`}>
      <span className="capitalize">{label}</span>
      <span>{changed ? `×${mult.toFixed(2)}` : "no change"}</span>
    </li>
  );
}

export default function PaxPage() {
  const user = useUser("pax");
  const [tab, setTab] = useState(TABS[0]);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [pickupId, setPickupId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const [notice, setNotice] = useState<NoticeState>(null);
  const [fare, setFare] = useState<FareEstimate | null>(null);
  const showOnMap = useMapView();

  // Leaving the page puts the map back to the whole island.
  useEffect(() => () => showOnMap({ focus: "overview" }), [showOnMap]);

  // Moves the map behind the page. `changed` says which box was just used,
  // and that is the place the map flies to.
  function moveMap(nextPickupId: string, nextDestinationId: string, changed: "pickup" | "destination") {
    const find = (id: string) => {
      const place = destinations.find((d) => String(d.id) === id);
      return place ? toPoint(place.latitude, place.longitude) : null;
    };
    const pickupPoint = find(nextPickupId);
    const destinationPoint = find(nextDestinationId);
    const target = changed === "pickup" ? pickupPoint : destinationPoint;
    showOnMap({
      pickup: pickupPoint,
      destination: destinationPoint,
      // if the chosen place has no coordinates, show whatever we can
      focus: target ? changed : pickupPoint && destinationPoint ? "both" : "overview",
    });
  }

  async function load() {
    try {
      const [destinationList, bookingList] = await Promise.all([
        api<Destination[]>("/destinations"),
        api<Booking[]>("/bookings"),
      ]);
      setDestinations(destinationList);
      setBookings(bookingList);
    } catch {
      // a failed refresh is not worth interrupting the user for
    }
  }
  usePolling(load, user !== null);

  // Ask the fare model for a live quote whenever both ends are chosen. It
  // refreshes on the same beat as everything else, so a surge that starts
  // while the rider is deciding shows up in the price.
  useEffect(() => {
    if (!pickupId || !destinationId || pickupId === destinationId) return;
    let cancelled = false;
    const ask = () =>
      api<FareEstimate>(`/fare/estimate?pickup_id=${pickupId}&destination_id=${destinationId}`)
        .then((quote) => !cancelled && setFare(quote))
        .catch(() => !cancelled && setFare(null));
    ask();
    const timer = setInterval(ask, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [pickupId, destinationId]);

  // Runs an action, then refreshes the lists and shows the result.
  async function run(action: () => Promise<unknown>, success: string) {
    try {
      await action();
      setNotice({ kind: "ok", text: success });
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
    }
    await load();
  }

  if (!user) return <Loading />;

  const pickup = destinations.find((d) => String(d.id) === pickupId);
  const destination = destinations.find((d) => String(d.id) === destinationId);
  let fareText = "Choose a pickup and a destination to see the fare.";
  if (pickup && destination) {
    fareText = pickup.id === destination.id ? "Pickup and destination cannot be the same." : "";
  }
  const canBook = pickup && destination && pickup.id !== destination.id;
  const sorted = [...bookings].sort((a, b) => ORDER[a.status] - ORDER[b.status] || b.id - a.id);

  async function book() {
    await run(
      () => api("/bookings", { method: "POST", body: { pickup_id: Number(pickupId), destination_id: Number(destinationId) } }),
      "Booked! Waiting for a driver to accept.",
    );
    setTab("My bookings");
  }

  return (
    <Shell subtitle="Passenger Bookings" user={user}>
      <Tabs tabs={TABS} current={tab} onChange={(next) => { setTab(next); setNotice(null); }} />
      <div className="mt-6 space-y-4">
        <Notice notice={notice} />

        {tab === "Book a ride" && (
          // The card keeps to the left on a wide screen, so the map and its
          // animation stay visible on the right.
          <Card className="w-full max-w-md">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">Book a ride</p>
            <h2 className="mb-5 text-2xl font-black tracking-tight">Where are you going?</h2>

            <div className="flex gap-3">
              {/* the little route drawing: blue dot, dotted line, red dot */}
              <div aria-hidden="true" className="flex flex-col items-center pb-5 pt-9">
                <span className="h-3.5 w-3.5 rounded-full bg-slate-900 ring-4 ring-slate-200" />
                <span className="my-1 w-0 flex-1 border-l-2 border-dotted border-slate-300" />
                <span className="h-3.5 w-3.5 rounded-full bg-amber-400 ring-4 ring-amber-100" />
              </div>
              <div className="flex-1 space-y-4">
                <SelectField
                  label="Pickup"
                  value={pickupId}
                  onChange={(e) => {
                    setPickupId(e.target.value);
                    setFare(null); // clear the old quote until the new one arrives
                    moveMap(e.target.value, destinationId, "pickup");
                  }}
                >
                  <option value="">Choose a pickup point…</option>
                  {destinations.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </SelectField>
                <SelectField
                  label="Destination"
                  value={destinationId}
                  onChange={(e) => {
                    setDestinationId(e.target.value);
                    setFare(null); // clear the old quote until the new one arrives
                    moveMap(pickupId, e.target.value, "destination");
                  }}
                >
                  <option value="">Choose a destination…</option>
                  {destinations.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </SelectField>
              </div>
            </div>

            <div className="mt-5 rounded-xl bg-slate-900/[0.04] p-4">
              {canBook && destination && fare ? (
                <>
                  <div className="flex items-end justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Estimated fare
                        {fare.distance_km != null && <span className="normal-case text-slate-400"> · {fare.distance_km} km</span>}
                      </p>
                      <p className="text-sm text-slate-600">{pickup?.name} to {destination.name}</p>
                    </div>
                    <div className="text-right">
                      {fare.final_fare !== fare.base_fare && (
                        <p className="text-xs text-slate-400 line-through">TT${fare.base_fare}</p>
                      )}
                      <p className="text-3xl font-black tracking-tight">TT${fare.final_fare}</p>
                    </div>
                  </div>

                  {/* the model's reasoning, shown line by line */}
                  <ul className="mt-3 space-y-1 border-t border-slate-200/70 pt-3 text-xs text-slate-500">
                    <li className="flex justify-between"><span>Base fare (route)</span><span>TT${fare.base_fare}</span></li>
                    <PriceLine label={fare.time_label} mult={fare.time_multiplier} />
                    <PriceLine label={fare.traffic_label} mult={fare.traffic_multiplier} />
                    <PriceLine label={fare.demand_label} mult={fare.demand_multiplier} />
                  </ul>

                  {fare.surge && (
                    <p className="mt-3 rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-semibold text-amber-900">
                      ⚡ Surge pricing in effect — lots of riders, few free drivers right now.
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-slate-600">{fareText || "Estimating fare…"}</p>
              )}
            </div>

            <Button onClick={book} disabled={!canBook} className="mt-5 w-full py-3 text-base">
              {canBook && fare ? `Book ride · TT$${fare.final_fare}` : "Book ride"}
            </Button>
          </Card>
        )}

        {tab === "My bookings" && (
          <Card>
            <Table headings={["Booking", "Pickup", "Destination", "Fare (TT$)", "Status", "Driver", "Actions"]} empty={sorted.length === 0}>
              {sorted.map((booking) => (
                <tr key={booking.id}>
                  <td>{booking.id}</td>
                  <td>{booking.pickup}</td>
                  <td>{booking.destination}</td>
                  <td>{booking.fare}</td>
                  <td><StatusBadge status={booking.status} /></td>
                  <td>{booking.driver_username ?? "-"}</td>
                  <td>
                    {booking.status === "pending" && (
                      <Button variant="danger" size="sm" onClick={() => run(() => api(`/bookings/${booking.id}/cancel`, { method: "POST" }), "Booking cancelled.")}>
                        Cancel
                      </Button>
                    )}
                    {booking.status === "completed" && (
                      <div className="flex gap-1 text-xl">
                        {(["up", "down"] as const).map((rating) => (
                          <button
                            key={rating}
                            aria-label={rating === "up" ? "Thumbs up" : "Thumbs down"}
                            onClick={() => run(() => api(`/bookings/${booking.id}/rating`, { method: "POST", body: { rating } }), "Thanks for rating your driver.")}
                            className={`rounded-lg px-1.5 py-0.5 transition hover:scale-110 hover:bg-slate-900/5 ${booking.rating && booking.rating !== rating ? "opacity-30" : ""}`}
                          >
                            {rating === "up" ? "👍" : "👎"}
                          </button>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
        )}

        {tab === "Destinations and fares" && (
          <Card>
            <Table headings={["Destination", "Fare (TT$)"]} empty={destinations.length === 0}>
              {destinations.map((d) => (
                <tr key={d.id}>
                  <td>{d.name}</td>
                  <td>{d.fare}</td>
                </tr>
              ))}
            </Table>
          </Card>
        )}
      </div>
    </Shell>
  );
}
