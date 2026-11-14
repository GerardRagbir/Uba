// The map library does part of its work in a "web worker", a script the
// browser loads from its own URL. This copies that script into public/ so the
// site can serve it. It runs automatically before `npm run dev` and `npm run build`.
import { copyFileSync, mkdirSync } from "node:fs";

mkdirSync("public", { recursive: true });
copyFileSync("node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs", "public/maplibre-gl-worker.mjs");
