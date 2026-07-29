import type { Metadata } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const viewport = { themeColor: "#08111D", width: "device-width", initialScale: 1, maximumScale: 1 };

export const metadata: Metadata = {
  title: "GeoBancas RD",
  description: "Sistema de geolocalización y supervisión de bancas",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
