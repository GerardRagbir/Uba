// Every call to the backend goes through this one function.

export type Role = "pax" | "driver" | "admin";

export type User = {
  id: number;
  username: string;
  email: string;
  name: string;
  role: Role;
  phone: string | null;
  permit_no: string | null;
};

export type Destination = {
  id: number;
  name: string;
  fare: number;
  latitude: number | null;
  longitude: number | null;
};

export type Booking = {
  id: number;
  pickup: string;
  pickup_latitude: number | null;
  pickup_longitude: number | null;
  destination: string;
  destination_latitude: number | null;
  destination_longitude: number | null;
  fare: number;
  status: "pending" | "accepted" | "completed" | "cancelled";
  rating: "up" | "down" | null;
  pax_username: string;
  pax_name: string;
  pax_phone: string | null;
  driver_username: string | null;
  created_at: string;
};

export type Vehicle = {
  id: number;
  plate: string;
  make: string;
  model: string;
  seats: number;
  driver_id: number;
  driver_username: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Options = { method?: "GET" | "POST" | "PUT"; body?: unknown };

// What the fare model returns: the price, plus why it is what it is.
export type FareEstimate = {
  base_fare: number;
  final_fare: number;
  distance_km: number | null;
  time_multiplier: number;
  time_label: string;
  traffic_multiplier: number;
  traffic_label: string;
  demand_multiplier: number;
  demand_label: string;
  surge: boolean;
};

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
    // Send the login cookie. The browser manages it; this code never sees it.
    credentials: "same-origin",
  });

  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  return (await response.json()) as T;
}

// FastAPI sends errors as { detail: "..." } or, for validation, a list.
async function errorMessage(response: Response): Promise<string> {
  if (response.status === 429) return "Too many attempts. Wait a moment and try again.";
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: { loc?: string[]; msg: string }) => {
          const field = item.loc?.[item.loc.length - 1];
          return field ? `${field}: ${item.msg}` : item.msg;
        })
        .join(". ");
    }
  } catch {
    // not JSON, fall through
  }
  return "Something went wrong. Please try again.";
}

export function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}
