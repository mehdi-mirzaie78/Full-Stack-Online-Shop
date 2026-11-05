"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <section><p role="alert">Identity service unavailable / سرویس هویت در دسترس نیست</p><button className="rounded border px-4 py-2" onClick={reset}>Retry / تلاش دوباره</button></section>;
}
