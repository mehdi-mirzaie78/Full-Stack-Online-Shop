import type { Metadata } from "next";
import "./globals.css";

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
    <html lang={defaultLang} dir={defaultDir} className="dark">
      <body className="min-h-screen bg-background text-foreground cyber-grid">
        <header className="border-b border-border/60 bg-background/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-neon-cyan font-black tracking-wider text-xl">
              CYBER//STORE
            </span>
            <span className="text-xs px-2 py-0.5 rounded border border-neon-cyan/40 text-neon-cyan bg-neon-cyan/10">
              3D MATS & UE
            </span>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-secondary text-muted-foreground border border-border">
              <span>وضعیت سرور:</span>
              <span className="text-neon-lime flex items-center gap-1 font-mono">
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
