"use client";

import { useEffect, useRef } from "react";
import { ACESFilmicToneMapping, Vector3, WebGLRenderer } from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { createMaterialScene, type MaterialSettings } from "./material-scene";

function mountViewer(canvas: HTMLCanvasElement, onError: () => void) {
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = ACESFilmicToneMapping;
  const preview = createMaterialScene({ color: "#00cddd", roughness: 0.35, metalness: 0.3 });
  const controls = new OrbitControls(preview.camera, canvas);
  controls.enablePan = false;
  controls.enableZoom = false;
  canvas.style.touchAction = "pan-y"; // Vertical swipes scroll; horizontal swipes orbit.
  const render = () => renderer.render(preview.scene, preview.camera);
  const resize = () => {
    const { width, height } = canvas.getBoundingClientRect();
    if (!width || !height) return;
    renderer.setSize(width, height, false);
    preview.camera.aspect = width / height;
    preview.camera.updateProjectionMatrix();
    render();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  controls.addEventListener("change", render);
  canvas.addEventListener("webglcontextlost", onError);
  resize();
  return {
    update(settings: MaterialSettings) {
      preview.sphere.material.color.set(settings.color);
      preview.sphere.material.roughness = settings.roughness;
      preview.sphere.material.metalness = settings.metalness;
      render();
    },
    rotate(key: string) {
      if (key === "Home") preview.camera.position.set(0, 0, 3.6);
      else preview.camera.position.applyAxisAngle(new Vector3(0, 1, 0), key === "ArrowLeft" ? -0.15 : 0.15);
      controls.update();
      render();
    },
    dispose() {
      observer.disconnect();
      canvas.removeEventListener("webglcontextlost", onError);
      controls.removeEventListener("change", render);
      controls.dispose();
      preview.dispose();
      renderer.dispose(); // Strict Mode reuses canvas; keep its context valid.
    },
  };
}

export default function MaterialCanvas({ settings, label, onError }: {
  settings: MaterialSettings; label: string; onError: () => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const viewer = useRef<ReturnType<typeof mountViewer> | null>(null);
  useEffect(() => {
    try {
      viewer.current = mountViewer(canvas.current!, onError);
    } catch {
      onError();
    }
    return () => {
      viewer.current?.dispose();
      viewer.current = null;
    };
  }, [onError]);
  useEffect(() => { viewer.current?.update(settings); }, [settings]);
  return <canvas ref={canvas} role="img" aria-label={label} tabIndex={0}
    className="absolute inset-0 h-full w-full rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-neon-cyan"
    onKeyDown={(event) => {
      if (!["ArrowLeft", "ArrowRight", "Home"].includes(event.key)) return;
      event.preventDefault();
      viewer.current?.rotate(event.key);
    }} />;
}
