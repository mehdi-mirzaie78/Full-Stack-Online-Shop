"use client";

import dynamic from "next/dynamic";
import { Component, useCallback, useState, type ReactNode } from "react";

const MaterialCanvas = dynamic(() => import("./material-canvas"), { ssr: false });
const initial = { color: "#00cddd", roughness: 0.35, metalness: 0.3 };

export class PreviewBoundary extends Component<{ children: ReactNode; fallback: ReactNode; onError: () => void }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.onError(); }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

export default function MaterialLab({ persian }: { persian: boolean }) {
  const [active, setActive] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [settings, setSettings] = useState(initial);
  const fail = useCallback(() => setFailed(true), []);
  const unavailable = persian ? "نمایش سه‌بعدی در دسترس نیست. پیش‌نمایش ثابت باقی می‌ماند." : "3D unavailable. Static preview remains available.";
  const button = "rounded-md border border-neon-cyan/50 px-4 py-2 text-sm text-neon-cyan focus-visible:outline focus-visible:outline-2 focus-visible:outline-neon-cyan";
  return (
    <section aria-labelledby="material-lab-title" className="rounded-2xl border border-border bg-card/80 p-6 md:p-8">
      <h2 id="material-lab-title" className="text-2xl font-bold">{persian ? "آزمایشگاه متریال" : "Material lab"}</h2>
      <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{persian
        ? "نمونه آموزشی Three.js، نه پیش‌نمایش محصولات فروشگاه یا رندر دقیق Unreal Engine. رنگ و زبری سطح را تغییر دهید."
        : "A Three.js learning sample, not a catalog product or exact Unreal Engine render. Explore how color and surface roughness change a material."}</p>
      <div className="mt-6 grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="relative h-72 overflow-hidden rounded-xl border border-border bg-background md:h-96">
          <div className="flex h-full items-center justify-center" role="img" aria-label={persian ? "نمونه ثابت متریال" : "Static material sample"}>
            <div className="h-44 w-44 rounded-full" style={{ background: `radial-gradient(circle at 30% 25%, #fff, ${settings.color} 35%, #101725 80%)` }} />
          </div>
          {active && !failed && <PreviewBoundary key={attempt} onError={fail} fallback={<p role="status" className="absolute inset-x-0 bottom-3 px-4 text-sm">{unavailable}</p>}>
            <MaterialCanvas settings={settings} onError={fail} label={persian ? "کره متریال سه‌بعدی؛ برای چرخش بکشید یا از کلیدهای چپ و راست استفاده کنید. Home برای بازنشانی نما." : "3D material sphere. Drag or use Left/Right arrows to orbit. Home resets view."} />
          </PreviewBoundary>}
          {failed && <p role="status" className="absolute inset-x-0 bottom-3 px-4 text-sm">{unavailable}</p>}
        </div>
        <div className="flex flex-col gap-5">
          <button type="button" className={button} onClick={() => {
            setFailed(false);
            setAttempt(attempt + 1);
            setActive(!active || failed);
          }}>{active && !failed ? (persian ? "بستن نمایش سه‌بعدی" : "Close 3D preview") : (persian ? "بارگذاری نمایش سه‌بعدی" : "Load 3D preview")}</button>
          {failed && <button type="button" className={button} onClick={() => window.location.reload()}>
            {persian ? "بارگذاری مجدد صفحه برای تلاش دوباره سه‌بعدی" : "Reload page to retry 3D"}
          </button>}
          <label className="flex items-center justify-between gap-3 text-sm">
            {persian ? "رنگ پایه" : "Base color"}
            <input type="color" value={settings.color} onChange={(event) => setSettings({ ...settings, color: event.target.value })} />
          </label>
          {(["roughness", "metalness"] as const).map((property) => <label key={property} htmlFor={`material-${property}`} className="space-y-2 text-sm">
            <span className="flex justify-between gap-3"><span>{property === "roughness" ? (persian ? "زبری" : "Roughness") : (persian ? "فلزی بودن" : "Metalness")}</span><output>{settings[property].toFixed(2)}</output></span>
            <input id={`material-${property}`} className="w-full accent-neon-cyan" type="range" min="0" max="1" step="0.01" value={settings[property]}
              onChange={(event) => setSettings({ ...settings, [property]: Number(event.target.value) })} />
          </label>)}
          <button type="button" className={button} onClick={() => {
            setSettings(initial);
            setAttempt(attempt + 1);
          }}>{persian ? "بازنشانی متریال و نما" : "Reset material and view"}</button>
          <p className="text-xs leading-relaxed text-muted-foreground">{persian ? "برای چرخش بکشید. کلیدهای چپ و راست: چرخش. Home: بازنشانی نما. حرکت خودکار غیرفعال است." : "Drag to orbit. Keyboard: Left/Right to orbit, Home to reset view. No automatic animation."}</p>
        </div>
      </div>
    </section>
  );
}
