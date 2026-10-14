import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WORKINT · Profile Manager",
  description:
    "Demostración académica de gestión de perfiles y postulaciones simuladas",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
