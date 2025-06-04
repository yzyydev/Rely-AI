import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rely AI - Decision Report Generator",
  description: "Generate AI-powered decision reports with multiple model perspectives",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
