"use client";

import { useEffect, useState, type FormEvent } from "react";

import { toPoint, useMapView } from "@/components/MapBackdrop";
import { Loading, Shell } from "@/components/Shell";
import { Button, Card, Field, Notice, Table, Tabs, ratingText, type NoticeState } from "@/components/ui";
import { api, messageFrom, type Booking, type Vehicle } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { useUser } from "@/lib/useUser";

const TABS = ["Bookings", "My vehicle"];

export default function DriverPage() {
  const user = useUser("driver");
  const [tab, setTab] = useState(TABS[0]);
  const [pending, setPending] = useState<Booking[]>([]);
  const [mine, setMine] = useState<Booking[]>([]);
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [form, setForm] = useState({ plate: "", make: "", model: "", seats: "4" });
  const [formLoaded, setFormLoaded] = useState(false);
  const [notice, setNotice] = useState<NoticeState>(null);

  async function load() {
    try {
      const [pendingList, myList, myVehicle] = await Promise.all([
        api<Booking[]>("/bookings/pending"),
        api<Booking[]>("/bookings"),
        api<Vehicle | null>("/vehicles/mine"),
      ]);
      setPending(pendingList);
      setMine(myList);
      setVehicle(myVehicle);
      // Fill the edit form once. Refilling on every refresh would wipe
      // whatever the driver is in the middle of typing.
      if (myVehicle && !formLoaded) {
        setForm({ plate: myVehicle.plate, make: myVehicle.make, model: myVehicle.model, seats: String(myVehicle.seats) });
        setFormLoaded(true);
      }
    } catch {
      // a failed refresh is not worth interrupting the user for
    }
  }
  usePolling(load, user !== null);

  async function run(action: () => Promise<unknown>, success: string) {
    try {
      await action();
      setNotice({ kind: "ok", text: success });
    } catch (error) {
      setNotice({ kind: "error", text: messageFrom(error) });
    }
    await load();
  }

  // A driver does one job at a time.
  const currentJob = mine.find((booking) => booking.status === "accepted");

  // While there is a job, the map behind the page frames the whole trip.
  const showOnMap = useMapView();
  const jobId = currentJob?.id;
  const pickupLat = currentJob?.pickup_latitude;
  const pickupLng = currentJob?.pickup_longitude;
  const destinationLat = currentJob?.destination_latitude;
  const destinationLng = currentJob?.destination_longitude;
  useEffect(() => {
    const pickup = toPoint(pickupLat, pickupLng);
    const destination = toPoint(destinationLat, destinationLng);
    showOnMap(jobId && pickup && destination ? { pickup, destination, focus: "both" } : { focus: "overview" });
    return () => showOnMap({ focus: "overview" });
  }, [showOnMap, jobId, pickupLat, pickupLng, destinationLat, destinationLng]);

  if (!user) return <Loading />;

  const past = mine.filter((booking) => booking.status === "completed");

  async function saveVehicle(event: FormEvent) {
    event.preventDefault();
    await run(
      () => api("/vehicles/mine", { method: "PUT", body: { ...form, seats: Number(form.seats) } }),
      "Vehicle updated.",
    );
  }

  return (
    <Shell subtitle="Driver Trips" user={user}>
      <Tabs tabs={TABS} current={tab} onChange={(next) => { setTab(next); setNotice(null); }} />
      <div className="mt-6 space-y-4">
        <Notice notice={notice} />

        {tab === "Bookings" && (
          <>
            {currentJob ? (
              <Card className="w-full max-w-md">
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">Current job · booking #{currentJob.id}</p>
                <div className="mt-3 flex gap-3">
                  <div aria-hidden="true" className="flex flex-col items-center py-1.5">
                    <span className="h-3.5 w-3.5 rounded-full bg-slate-900 ring-4 ring-slate-200" />
                    <span className="my-1 w-0 flex-1 border-l-2 border-dotted border-slate-300" />
                    <span className="h-3.5 w-3.5 rounded-full bg-amber-400 ring-4 ring-amber-100" />
                  </div>
                  <div className="flex-1 space-y-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pickup</p>
                      <p className="text-lg font-bold tracking-tight">{currentJob.pickup}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Destination</p>
                      <p className="text-lg font-bold tracking-tight">{currentJob.destination}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex items-end justify-between gap-3 rounded-xl bg-slate-900/[0.04] px-4 py-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Passenger</p>
                    <p className="text-sm font-medium">{currentJob.pax_name}{currentJob.pax_phone ? `, ${currentJob.pax_phone}` : ""}</p>
                  </div>
                  <p className="text-3xl font-black tracking-tight">TT${currentJob.fare}</p>
                </div>
                <div className="mt-5 flex gap-2">
                  <Button className="flex-1" onClick={() => run(() => api(`/bookings/${currentJob.id}/complete`, { method: "POST" }), `Trip completed. Collect TT$${currentJob.fare}.`)}>
                    Complete trip
                  </Button>
                  <Button variant="danger" onClick={() => run(() => api(`/bookings/${currentJob.id}/release`, { method: "POST" }), "Job cancelled. The booking is pending again.")}>
                    Cancel job
                  </Button>
                </div>
              </Card>
            ) : (
              <Card title="Pending bookings">
                <Table headings={["Booking", "Pickup", "Destination", "Fare (TT$)", "Pax", "Actions"]} empty={pending.length === 0}>
                  {pending.map((booking) => (
                    <tr key={booking.id}>
                      <td>{booking.id}</td>
                      <td>{booking.pickup}</td>
                      <td>{booking.destination}</td>
                      <td>{booking.fare}</td>
                      <td>{booking.pax_username}</td>
                      <td>
                        <Button size="sm" onClick={() => run(() => api(`/bookings/${booking.id}/accept`, { method: "POST" }), "Booking accepted.")}>
                          Accept
                        </Button>
                      </td>
                    </tr>
                  ))}
                </Table>
              </Card>
            )}

            <Card title="Past bookings">
              <Table headings={["Booking", "Pickup", "Destination", "Fare (TT$)", "Pax", "Rating"]} empty={past.length === 0}>
                {past.map((booking) => (
                  <tr key={booking.id}>
                    <td>{booking.id}</td>
                    <td>{booking.pickup}</td>
                    <td>{booking.destination}</td>
                    <td>{booking.fare}</td>
                    <td>{booking.pax_username}</td>
                    <td>{ratingText(booking.rating)}</td>
                  </tr>
                ))}
              </Table>
            </Card>
          </>
        )}

        {tab === "My vehicle" && (
          <Card title="My vehicle" className="w-full max-w-md">
            {vehicle ? (
              <form onSubmit={saveVehicle} className="space-y-4">
                <Field label="Plate" value={form.plate} onChange={(e) => setForm({ ...form, plate: e.target.value })} required />
                <Field label="Make" value={form.make} onChange={(e) => setForm({ ...form, make: e.target.value })} />
                <Field label="Model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
                <Field label="Seats" type="number" min={1} value={form.seats} onChange={(e) => setForm({ ...form, seats: e.target.value })} required />
                <Button type="submit" className="w-full">Save changes</Button>
              </form>
            ) : (
              <p className="text-sm text-slate-500">No vehicle assigned yet. Ask an admin.</p>
            )}
          </Card>
        )}
      </div>
    </Shell>
  );
}
