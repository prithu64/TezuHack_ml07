import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Student Support Risk Prediction",
  description:
    "ML-powered academic risk assessment and student support insights.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
