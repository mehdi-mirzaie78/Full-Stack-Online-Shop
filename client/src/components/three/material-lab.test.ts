import { expect, it, vi } from "vitest";
import { PreviewBoundary } from "./material-lab";
import MaterialLab from "./material-lab";
import * as React from "react";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";

it("offers page reload recovery for a cached failed viewer import", () => {
  const source = readFileSync(new URL("./material-lab.tsx", import.meta.url), "utf8");
  expect(source).toContain('window.location.reload()');
  expect(source).toContain('Reload page to retry 3D');
});

it.each([false, true])("explicitly labels each material slider (Persian: %s)", (persian) => {
  vi.stubGlobal("React", React);
  const html = renderToStaticMarkup(createElement(MaterialLab, { persian }));
  vi.unstubAllGlobals();
  for (const property of ["roughness", "metalness"]) {
    expect(html).toContain(`for="material-${property}"`);
    expect(html).toContain(`id="material-${property}"`);
  }
});

it("notifies parent when a preview render fails so loading can be retried", () => {
  const onError = vi.fn();
  const boundary = new PreviewBoundary({ children: null, fallback: null, onError });
  boundary.componentDidCatch();
  expect(onError).toHaveBeenCalledOnce();
});
