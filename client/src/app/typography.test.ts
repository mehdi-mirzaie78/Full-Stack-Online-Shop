import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

it("self-hosts both scripts with language-aware stacks and swap loading", () => {
  const layout = readFileSync(new URL("./layout.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("./globals.css", import.meta.url), "utf8");
  expect(layout).toContain('from "next/font/local"');
  expect(layout).toContain('weight: "100 900"');
  expect(layout).toContain('weight: "200 800"');
  expect(layout.match(/display: "swap"/g)).toHaveLength(2);
  expect(css).toContain('--font-ui: var(--font-manrope), var(--font-vazirmatn)');
  expect(css).toContain('--font-ui: var(--font-vazirmatn), var(--font-manrope)');
  expect(css).toContain('--line-height-body: 1.7');
  expect(css).toContain('--line-height-heading: 1.3');
  expect(css).toContain('--line-height-heading: 1.55');
  expect(css).toContain('line-height: var(--line-height-heading)');
  for (const font of ["Vazirmatn-Variable", "Manrope-Latin-Variable"]) {
    expect(readFileSync(new URL(`./fonts/${font}.woff2`, import.meta.url)).subarray(0, 4).toString()).toBe("wOF2");
  }
});
