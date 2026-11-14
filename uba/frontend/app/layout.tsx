import type { Metadata } from "next";
import "./globals.css";

import { MapProvider } from "@/components/MapBackdrop";

export const metadata: Metadata = {
  title: "UBA Taxi Booking",
  description: "Book a taxi anywhere in Trinidad",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full text-slate-900">
        {/* the map lives here, once, behind every page */}
        <MapProvider>{children}</MapProvider>
      </body>
    </html>
  );
}
