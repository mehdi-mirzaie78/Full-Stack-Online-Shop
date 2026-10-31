import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

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
        <header className="border-b border-border/60 bg-background/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span lang="en" dir="ltr" className="text-neon-cyan font-extrabold tracking-tight text-xl">
              CYBER//STORE
            </span>
            <span lang="en" dir="ltr" className="hidden whitespace-nowrap text-xs px-2 py-0.5 rounded border border-neon-cyan/40 text-neon-cyan bg-neon-cyan/10 sm:inline-flex">
              3D MATS & UE
            </span>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <div lang="fa" dir="rtl" className="flex items-center gap-2 px-3 py-1 rounded bg-secondary text-muted-foreground border border-border">
              <span>وضعیت سرور:</span>
              <span className="text-neon-lime flex items-center gap-1 font-medium">
                ✔ متصل
              </span>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
