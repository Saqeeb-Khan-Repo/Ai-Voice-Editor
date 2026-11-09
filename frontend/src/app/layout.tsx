import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Naat Studio - Professional Local Audio Enhancement",
  description: "Browser-based local-first audio enhancement workstation designed for Naat, Islamic vocals, and spiritual recitation recordings.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
