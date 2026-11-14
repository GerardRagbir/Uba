"use client";

// The OpenStreetMap map that sits behind every page.
//
// It is decoration with a job: it cannot be dragged or zoomed by the user,
// but pages can tell it where to look. The passenger page flies it to the
// pickup point, then out and back in to the destination.

import "maplibre-gl/dist/maplibre-gl.css";

import type { GeoJSONSource, Map as MapLibreMap, Marker } from "maplibre-gl";
import { createContext, useCallback, useContext, useEffect, useRef, type ReactNode } from "react";

export type MapPoint = { lat: number; lng: number };

export type MapView = {
  pickup?: MapPoint | null;
  destination?: MapPoint | null;
  // overview: the whole island.  pickup / destination: fly in to that point.
  // both: frame the whole trip.
  focus: "overview" | "pickup" | "destination" | "both";
};

type Library = typeof import("maplibre-gl");

// [west, south] and [east, north] corners of Trinidad
const TRINIDAD: [[number, number], [number, number]] = [[-61.95, 10.03], [-60.9, 10.86]];
const CLOSE_ZOOM = 14.2;
const EMPTY_LINE = { type: "FeatureCollection" as const, features: [] };

const MapContext = createContext<(view: MapView) => void>(() => {});

// Pages call this to get the function that moves the map.
export function useMapView() {
  return useContext(MapContext);
}

export function MapProvider({ children }: { children: ReactNode }) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const library = useRef<Library | null>(null);
  const markers = useRef<{ pickup?: Marker; destination?: Marker }>({});
  const ready = useRef(false);
  const waiting = useRef<MapView | null>(null);

  const apply = useCallback((view: MapView) => {
    const mapNow = map.current;
    const lib = library.current;
    if (!mapNow || !lib) return;

    // --- markers: one for the pickup, one for the destination ---
    for (const kind of ["pickup", "destination"] as const) {
      const point = view[kind];
      markers.current[kind]?.remove();
      markers.current[kind] = undefined;
      if (point) {
        // The map library moves the outer element around, so our own
        // styling goes on a child and the two never fight over CSS.
        const element = document.createElement("div");
        const shape = document.createElement("span");
        shape.className = `uba-pin uba-pin-${kind}`;
        element.appendChild(shape);
        markers.current[kind] = new lib.Marker({ element, anchor: kind === "destination" ? "bottom" : "center" })
          .setLngLat([point.lng, point.lat])
          .addTo(mapNow);
      }
    }

    // --- the dashed line joining them ---
    const line = mapNow.getSource("trip") as GeoJSONSource | undefined;
    if (view.pickup && view.destination) {
      line?.setData({
        type: "Feature",
        properties: {},
        geometry: {
          type: "LineString",
          coordinates: [
            [view.pickup.lng, view.pickup.lat],
            [view.destination.lng, view.destination.lat],
          ],
        },
      });
    } else {
      line?.setData(EMPTY_LINE);
    }

    // --- the camera ---
    // On a wide screen the page's card sits on the left, so we aim a little
    // to the right of centre. On a phone the card is on top, so we aim lower.
    const wide = window.innerWidth >= 1024;
    const offset: [number, number] = wide ? [Math.min(240, window.innerWidth * 0.18), 30] : [0, window.innerHeight * 0.37];
    const padding = wide
      ? { top: 140, bottom: 140, right: 120, left: Math.min(520, window.innerWidth * 0.42) }
      : { top: window.innerHeight * 0.72, bottom: 50, left: 40, right: 40 };

    const target = view.focus === "pickup" ? view.pickup : view.focus === "destination" ? view.destination : null;
    if (target) {
      // flyTo zooms out, travels, and zooms back in: exactly the "out of the
      // pickup and into the destination" movement.
      mapNow.flyTo({
        center: [target.lng, target.lat],
        zoom: CLOSE_ZOOM,
        offset,
        curve: 1.6,
        duration: view.focus === "pickup" ? 2600 : 3800,
      });
    } else if (view.focus === "both" && view.pickup && view.destination) {
      const bounds = new lib.LngLatBounds([view.pickup.lng, view.pickup.lat], [view.pickup.lng, view.pickup.lat]);
      bounds.extend([view.destination.lng, view.destination.lat]);
      mapNow.fitBounds(bounds, { padding, maxZoom: 13, duration: 2200 });
    } else {
      mapNow.fitBounds(TRINIDAD, { padding: 30, duration: 2200 });
    }
  }, []);

  const showView = useCallback(
    (view: MapView) => {
      waiting.current = view; // remembered in case the map is still loading
      if (ready.current) apply(view);
    },
    [apply],
  );

  useEffect(() => {
    let cancelled = false;
    let created: MapLibreMap | null = null;

    // The map library is big, so it is loaded separately, after the page.
    import("maplibre-gl").then((lib) => {
      if (cancelled || !container.current) return;
      lib.setWorkerUrl("/maplibre-gl-worker.mjs");

      created = new lib.Map({
        container: container.current,
        interactive: false, // no dragging, zooming or rotating by the user
        attributionControl: false, // we show our own credit, below
        bounds: TRINIDAD,
        fitBoundsOptions: { padding: 30 },
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              maxzoom: 19,
            },
          },
          layers: [
            {
              id: "osm",
              type: "raster",
              source: "osm",
              // Yellow-cab theme: strip the colour out of the base map so it
              // reads as crisp black-and-white, then our own yellow overlays
              // (route line, markers) are the only colour on screen.
              //   saturation -1 = fully grey; a little extra contrast and a
              //   lifted minimum brightness keep it clean and light.
              paint: {
                "raster-saturation": -1,
                "raster-contrast": 0.15,
                "raster-brightness-min": 0.05,
                "raster-brightness-max": 1,
              },
            },
          ],
        },
      });
      map.current = created;
      library.current = lib;

      created.on("load", () => {
        if (!created) return;
        created.addSource("trip", { type: "geojson", data: EMPTY_LINE });
        created.addLayer({
          id: "trip-outline",
          type: "line",
          source: "trip",
          layout: { "line-cap": "round" },
          // black casing under a bold cab-yellow route line
          paint: { "line-color": "#111827", "line-width": 8, "line-opacity": 0.9 },
        });
        created.addLayer({
          id: "trip-line",
          type: "line",
          source: "trip",
          layout: { "line-cap": "round" },
          paint: { "line-color": "#fbbf24", "line-width": 4 },
        });
        ready.current = true;
        if (waiting.current) apply(waiting.current);
      });
    });

    return () => {
      cancelled = true;
      ready.current = false;
      created?.remove();
      map.current = null;
    };
  }, [apply]);

  return (
    <MapContext.Provider value={showView}>
      {/* the map itself: fixed to the window, behind everything, untouchable */}
      {/* The outer box does the positioning. The map library gives its own
          container "position: relative", which would undo "fixed". */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0">
        <div ref={container} className="h-full w-full" />
      </div>
      {/* a soft wash over the map so text on top stays readable */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-white/60 via-transparent to-white/40" />

      <div className="relative z-10">{children}</div>

      {/* OpenStreetMap's licence requires this credit to be visible */}
      <a
        href="https://www.openstreetmap.org/copyright"
        target="_blank"
        rel="noreferrer"
        className="fixed bottom-2 right-2 z-20 rounded-md bg-white/85 px-2 py-0.5 text-[11px] text-slate-600 shadow-sm backdrop-blur hover:text-slate-900"
      >
        © OpenStreetMap contributors
      </a>
    </MapContext.Provider>
  );
}

// Turns a destination's latitude and longitude into a point for the map,
// or null when it has no coordinates.
export function toPoint(latitude: number | null | undefined, longitude: number | null | undefined): MapPoint | null {
  if (latitude == null || longitude == null) return null;
  return { lat: latitude, lng: longitude };
}
