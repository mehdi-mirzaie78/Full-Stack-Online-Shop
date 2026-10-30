"use client";

import { useState } from "react";
import { Box, Layers, Cpu, Sparkles, Check, X, Globe } from "lucide-react";
import MaterialLab from "@/components/three/material-lab";

export default function HomePage() {
  const [direction, setDirection] = useState<"rtl" | "ltr">("rtl");

  const toggleDirection = () => {
    const nextDir = direction === "rtl" ? "ltr" : "rtl";
    setDirection(nextDir);
    document.documentElement.setAttribute("dir", nextDir);
    document.documentElement.setAttribute("lang", nextDir === "rtl" ? "fa" : "en");
  };

  const sampleProducts = [
    {
      id: "mat-01",
      title: direction === "rtl" ? "مجموعه متریال فیبر کربن نانو" : "Nano Carbon Fiber PBR Pack",
      software: ["Unreal Engine 5.5", "3ds Max (V-Ray / Corona)"],
      resolution: "8K UHD Textures",
      price: "1,450,000 تومان",
      available: true,
      tag: "CYBER-SPEC",
    },
    {
      id: "mat-02",
      title: direction === "rtl" ? "شیدر شیشه هولوگرافیک سایبرپانک" : "Holographic Cyber Glass Shader",
      software: ["Unreal Engine 5.5", "Substance Painter"],
      resolution: "Real-time HLSL",
      price: "890,000 تومان",
      available: true,
      tag: "RAY-TRACED",
    },
    {
      id: "mat-03",
      title: direction === "rtl" ? "پک فلزات صنعتی زنگ‌زده رباتیک" : "Industrial Scuffed Chrome & Rust",
      software: ["3ds Max", "Unreal Engine 5"],
      resolution: "4K Seamless",
      price: "620,000 تومان",
      available: false,
      tag: "TIME-LOCKED",
    },
  ];

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-neon-cyan/30 bg-card/60 p-8 md:p-12 backdrop-blur-xl shadow-neon-cyan">
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-neon-pink/40 bg-neon-pink/10 px-3 py-1 text-xs text-neon-pink font-mono">
            <Sparkles className="h-3.5 w-3.5" />
            <span lang="en" dir="ltr">UNREAL ENGINE 5 & 3DS MAX COMPATIBLE</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            {direction === "rtl" ? (
              <>
                فروشگاه متریال‌های سه‌بعدی نسل آینده با کیفیت{" "}
                <span className="text-neon-cyan">فوق‌العاده بالا</span>
              </>
            ) : (
              <>
                Next-Gen 3D PBR Materials &{" "}
                <span className="text-neon-cyan">Ultra Realism</span>
              </>
            )}
          </h1>

          <p className="text-muted-foreground text-sm md:text-base leading-relaxed">
            {direction === "rtl"
              ? "مخصوص طراحان سه‌بعدی، محیط‌سازان Unreal Engine و استودیوهای رندرینگ 3ds Max. دانلود آنی، لایسنس تجاری، و تست بلادرنگ شیدرها."
              : "Built for 3D technical artists, UE environment artists, and 3ds Max rendering pipelines. Instant downloads and verified PBR maps."}
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={toggleDirection}
              className="inline-flex items-center gap-2 rounded-lg border border-neon-cyan bg-neon-cyan/15 px-4 py-2.5 text-sm font-semibold text-neon-cyan hover:bg-neon-cyan/25 transition-all shadow-sm"
            >
              <Globe className="h-4 w-4" />
              <span>{direction === "rtl" ? "تغییر جهت به چپ‌به‌راست (LTR)" : "Switch to RTL (راست‌به‌چپ)"}</span>
            </button>
          </div>
        </div>
      </section>

      <MaterialLab persian={direction === "rtl"} />

      {/* Featured Products */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl md:text-2xl font-bold tracking-tight flex items-center gap-2">
            <Box className="h-5 w-5 text-neon-cyan" />
            <span>{direction === "rtl" ? "محصولات برگزیده و شیدرها" : "Featured Shaders & Materials"}</span>
          </h2>
          <span className="text-xs font-mono text-muted-foreground">3D ASSETS MATRIX</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sampleProducts.map((p) => (
            <div
              key={p.id}
              className="group relative flex flex-col justify-between rounded-xl border border-border bg-card/80 p-6 transition-all hover:border-neon-cyan/50 hover:shadow-neon-cyan"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-muted text-neon-cyan border border-neon-cyan/20">
                    {p.tag}
                  </span>
                  <div className="flex items-center gap-1.5 text-xs font-medium">
                    {p.available ? (
                      <span className="inline-flex items-center gap-1 text-neon-lime">
                        <Check className="h-3.5 w-3.5" />
                        <span>{direction === "rtl" ? "موجود" : "In Stock"}</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-400">
                        <X className="h-3.5 w-3.5" />
                        <span>{direction === "rtl" ? "پنجره زمانی نامعتبر" : "Time Window Locked"}</span>
                      </span>
                    )}
                  </div>
                </div>

                <h3 className="text-base font-bold text-foreground group-hover:text-neon-cyan transition-colors">
                  {p.title}
                </h3>

                <div className="space-y-1.5 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                    <span lang="en" dir="ltr">{p.software.join(" • ")}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Cpu className="h-3.5 w-3.5 text-muted-foreground" />
                    <span lang="en" dir="ltr">{p.resolution}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-between border-t border-border/60 pt-4">
                <span lang="fa" className="text-sm font-semibold tabular-nums text-white">
                  {p.price}
                </span>
                <button
                  disabled={!p.available}
                  className="rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium transition-all hover:bg-neon-pink hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {p.available
                    ? direction === "rtl"
                      ? "افزودن به سبد خرید"
                      : "Add to Cart"
                    : direction === "rtl"
                    ? "غیرقابل سفارش"
                    : "Unavailable"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
