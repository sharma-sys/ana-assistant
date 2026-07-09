import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ANA | AAYUDH News Assistant",
  description: "Internal AI-powered editorial dashboard for Aayudh Media",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
