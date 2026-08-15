import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Business CRM — Lead Management Dashboard",
  description:
    "CRM dashboard for managing business leads collected from Google Maps. View, filter, search, and update lead statuses.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full bg-[#0b0c10]">
        <Sidebar />
        <main className="ml-60 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
