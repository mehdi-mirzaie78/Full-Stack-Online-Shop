import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { IdentityLanguage } from "@/components/identity/language";

const vazirmatn = localFont({
  src: "./fonts/Vazirmatn-Variable.woff2",
  variable: "--font-vazirmatn",
  weight: "100 900",
  display: "swap",
});

const manrope = localFont({
  src: "./fonts/Manrope-Latin-Variable.woff2",
  variable: "--font-manrope",
  weight: "200 800",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CYBERSTORE | 3D Materials & Digital Assets",
  description: "Next-generation 3D materials, Unreal Engine shaders, and 3ds Max workflows.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Default to RTL (Persian fa-IR) as per requirements, switchable to LTR
  const defaultDir = process.env.NEXT_PUBLIC_DEFAULT_DIR || "rtl";
  const defaultLang = process.env.NEXT_PUBLIC_DEFAULT_LOCALE || "fa";

  return (
    <html lang={defaultLang} dir={defaultDir} className={`dark ${vazirmatn.variable} ${manrope.variable}`}>
      <body className="min-h-screen bg-background text-foreground cyber-grid">
        <IdentityLanguage>
        <Navbar />

        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
        </IdentityLanguage>
      </body>
    </html>
  );
}
