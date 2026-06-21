import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Acre — Field Health Dashboard",
  description: "Offline-first handheld plant scanner. Map, scores, and AI report.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
