"use client";

import { useState, type FormEvent, type ReactNode } from "react";

import { Loading, Shell } from "@/components/Shell";
import { Button, Card, Field, Modal, Notice, SelectField, StatusBadge, Table, Tabs, ratingText, type NoticeState } from "@/components/ui";
import { api, messageFrom, type Booking, type Destination, type User, type Vehicle } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import { useUser } from "@/lib/useUser";

const TABS = ["Users", "Vehicles", "Destinations", "Bookings"];
type Dialog = "user" | "vehicle" | "destination" | null;

const emptyUser = { role: "driver", username: "", email: "", name: "", password: "", permit_no: "" };
const emptyVehicle = { plate: "", make: "", model: "", seats: "4", driver_id: "" };
const emptyDestination = { name: "", fare: "", latitude: "", longitude: "" };

export default function AdminPage() {
  const user = useUser("admin");
  const [tab, setTab] = useState(TABS[0]);
  const [users, setUsers] = useState<User[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [notice, setNotice] = useState<NoticeState>(null);
  const [dialogError, setDialogError] = useState<NoticeState>(null);
  const [userForm, setUserForm] = useState(emptyUser);
  const [vehicleForm, setVehicleForm] = useState(emptyVehicle);
  const [destinationForm, setDestinationForm] = useState(emptyDestination);

  async function load() {
    try {
      const [userList, vehicleList, destinationList, bookingList] = await Promise.all([
        api<User[]>("/users"),
        api<Vehicle[]>("/vehicles"),
        api<Destination[]>("/destinations"),
        api<Booking[]>("/bookings"),
      ]);
      setUsers(userList);
      setVehicles(vehicleList);
      setDestinations(destinationList);
      setBookings(bookingList);
    } catch {
      // a failed refresh is not worth interrupting the user for
    }
  }
  usePolling(load, user !== null);

  if (!user) return <Loading />;

  // Only drivers who do not have a vehicle yet can be given one.
  const freeDrivers = users.filter((u) => u.role === "driver" && !vehicles.some((v) => v.driver_id === u.id));

  function open(which: Dialog) {
    setDialogError(null);
    setDialog(which);
  }

  // Saves a dialog's form. On failure the dialog stays open with what was typed.
  async function save(event: FormEvent, action: () => Promise<unknown>, success: string, reset: () => void) {
    event.preventDefault();
    try {
      await action();
      setDialog(null);
      reset();
      setNotice({ kind: "ok", text: success });
      await load();
    } catch (error) {
      setDialogError({ kind: "error", text: messageFrom(error) });
    }
  }

  function heading(title: string, button?: ReactNode) {
    return (
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold tracking-tight">{title}</h2>
        {button}
      </div>
    );
  }

  const dialogButtons = (label: string) => (
    <>
      <Notice notice={dialogError} />
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={() => setDialog(null)}>Cancel</Button>
        <Button type="submit">{label}</Button>
      </div>
    </>
  );

  return (
    <Shell subtitle="Admin Dashboard" user={user}>
      <Tabs tabs={TABS} current={tab} onChange={(next) => { setTab(next); setNotice(null); }} />
      <div className="mt-6 space-y-4">
        <Notice notice={notice} />

        {tab === "Users" && (
          <Card>
            {heading("Users", <Button onClick={() => open("user")}>Add a user</Button>)}
            <Table headings={["Username", "Name", "Email", "Role", "Details"]} empty={users.length === 0}>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.name}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>{u.role === "pax" && u.phone ? `Phone: ${u.phone}` : u.role === "driver" && u.permit_no ? `Permit: ${u.permit_no}` : ""}</td>
                </tr>
              ))}
            </Table>
          </Card>
        )}

        {tab === "Vehicles" && (
          <Card>
            {heading("Vehicles", <Button onClick={() => open("vehicle")}>Add a vehicle</Button>)}
            <Table headings={["Plate", "Make", "Model", "Seats", "Driver"]} empty={vehicles.length === 0}>
              {vehicles.map((v) => (
                <tr key={v.id}>
                  <td>{v.plate}</td>
                  <td>{v.make}</td>
                  <td>{v.model}</td>
                  <td>{v.seats}</td>
                  <td>{v.driver_username}</td>
                </tr>
              ))}
            </Table>
          </Card>
        )}

        {tab === "Destinations" && (
          <Card>
            {heading("Destinations and fares", <Button onClick={() => open("destination")}>Add a destination</Button>)}
            <Table headings={["Destination", "Fare (TT$)", "On the map"]} empty={destinations.length === 0}>
              {destinations.map((d) => (
                <tr key={d.id}>
                  <td>{d.name}</td>
                  <td>{d.fare}</td>
                  <td className="text-slate-500">{d.latitude != null && d.longitude != null ? `${d.latitude.toFixed(4)}, ${d.longitude.toFixed(4)}` : "No coordinates"}</td>
                </tr>
              ))}
            </Table>
          </Card>
        )}

        {tab === "Bookings" && (
          <Card>
            {heading("All bookings")}
            <Table headings={["Booking", "Pickup", "Destination", "Fare (TT$)", "Status", "Pax", "Driver", "Rating"]} empty={bookings.length === 0}>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td>{b.id}</td>
                  <td>{b.pickup}</td>
                  <td>{b.destination}</td>
                  <td>{b.fare}</td>
                  <td><StatusBadge status={b.status} /></td>
                  <td>{b.pax_username}</td>
                  <td>{b.driver_username ?? "-"}</td>
                  <td>{ratingText(b.rating)}</td>
                </tr>
              ))}
            </Table>
          </Card>
        )}
      </div>

      {dialog === "user" && (
        <Modal title="Add a user" onClose={() => setDialog(null)}>
          <form
            className="space-y-4"
            onSubmit={(e) =>
              save(e, () => api("/users", { method: "POST", body: { ...userForm, permit_no: userForm.role === "driver" ? userForm.permit_no || null : null } }), "User added.", () => setUserForm(emptyUser))
            }
          >
            <SelectField label="Account type" value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
              <option value="driver">Driver</option>
              <option value="admin">Admin</option>
            </SelectField>
            <Field label="Username" value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} required minLength={3} />
            <Field label="Email" type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} required />
            <Field label="Full name" value={userForm.name} onChange={(e) => setUserForm({ ...userForm, name: e.target.value })} required />
            <Field label="Password (at least 8 characters)" type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} required minLength={8} autoComplete="new-password" />
            {userForm.role === "driver" && (
              <Field label="Driver's permit number" value={userForm.permit_no} onChange={(e) => setUserForm({ ...userForm, permit_no: e.target.value })} />
            )}
            {dialogButtons("Add user")}
          </form>
        </Modal>
      )}

      {dialog === "vehicle" && (
        <Modal title="Add a vehicle" onClose={() => setDialog(null)}>
          <form
            className="space-y-4"
            onSubmit={(e) =>
              save(e, () => api("/vehicles", { method: "POST", body: { ...vehicleForm, seats: Number(vehicleForm.seats), driver_id: Number(vehicleForm.driver_id) } }), "Vehicle added.", () => setVehicleForm(emptyVehicle))
            }
          >
            <Field label="Plate (e.g. HDK 2210)" value={vehicleForm.plate} onChange={(e) => setVehicleForm({ ...vehicleForm, plate: e.target.value })} required />
            <Field label="Make (e.g. Toyota)" value={vehicleForm.make} onChange={(e) => setVehicleForm({ ...vehicleForm, make: e.target.value })} />
            <Field label="Model (e.g. Axio)" value={vehicleForm.model} onChange={(e) => setVehicleForm({ ...vehicleForm, model: e.target.value })} />
            <Field label="Seats" type="number" min={1} value={vehicleForm.seats} onChange={(e) => setVehicleForm({ ...vehicleForm, seats: e.target.value })} required />
            <SelectField label="Driver" value={vehicleForm.driver_id} onChange={(e) => setVehicleForm({ ...vehicleForm, driver_id: e.target.value })} required>
              <option value="">Choose…</option>
              {freeDrivers.map((d) => <option key={d.id} value={d.id}>{d.username}</option>)}
            </SelectField>
            {freeDrivers.length === 0 && <p className="text-sm text-slate-500">Every driver already has a vehicle. Add a driver first.</p>}
            {dialogButtons("Add vehicle")}
          </form>
        </Modal>
      )}

      {dialog === "destination" && (
        <Modal title="Add a destination" onClose={() => setDialog(null)}>
          <form
            className="space-y-4"
            onSubmit={(e) =>
              save(e, () => api("/destinations", { method: "POST", body: {
                name: destinationForm.name,
                fare: Number(destinationForm.fare),
                // optional: where the map should fly to for this place
                latitude: destinationForm.latitude === "" ? null : Number(destinationForm.latitude),
                longitude: destinationForm.longitude === "" ? null : Number(destinationForm.longitude),
              } }), "Destination added.", () => setDestinationForm(emptyDestination))
            }
          >
            <Field label="Destination name" value={destinationForm.name} onChange={(e) => setDestinationForm({ ...destinationForm, name: e.target.value })} required />
            <Field label="Fare in TT$" type="number" min={1} value={destinationForm.fare} onChange={(e) => setDestinationForm({ ...destinationForm, fare: e.target.value })} required />
            <div className="grid grid-cols-2 gap-3">
              <Field label="Latitude (optional)" type="number" step="any" placeholder="10.6549" value={destinationForm.latitude} onChange={(e) => setDestinationForm({ ...destinationForm, latitude: e.target.value })} />
              <Field label="Longitude (optional)" type="number" step="any" placeholder="-61.5019" value={destinationForm.longitude} onChange={(e) => setDestinationForm({ ...destinationForm, longitude: e.target.value })} />
            </div>
            <p className="text-xs text-slate-500">With coordinates, the map can fly to this place. Right-click a spot on openstreetmap.org and choose &quot;Show address&quot; to find them.</p>
            {dialogButtons("Add destination")}
          </form>
        </Modal>
      )}
    </Shell>
  );
}
