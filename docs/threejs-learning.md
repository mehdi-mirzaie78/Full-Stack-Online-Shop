# Three.js: learn by building this material store

## What exists now

Repository scan: Next.js 15 / React 19 client, bilingual cyber-themed material storefront with sample products, Django core models and health endpoints, and infrastructure configuration. Catalog models/API, real cart, paid downloads, and preview asset storage are not implemented. Existing Unreal Engine / 3ds Max labels describe the intended audience, not browser-renderer compatibility.

The starter adds one native Three.js material sphere on the home page. It uses generated geometry and lights, not external models, HDR files, textures, or catalog data. Adjusting it does not edit products, prices, stock, or cart state.

Keep current visual tokens: dark navy surfaces, cyan focus/accent, existing typography and RTL layout. The sphere is the only new visual focal point; controls remain ordinary HTML next to it on desktop and below it on mobile. No automatic motion or extra decorative effects.

## Run it

From repository root:

```sh
npm ci
npm --prefix client ci
npm run dev:client
```

Open `http://localhost:3000`, find **آزمایشگاه متریال / Material lab**, switch language if desired, then choose **Load 3D preview**. Server, Docker, and product API are not needed for this exercise. Use the existing server/infrastructure setup separately for backend work; never use SQLite.

```sh
npm --prefix client run test
npm --prefix client run typecheck
npm --prefix client run lint
npm --prefix client run build
```

Root scripts also run backend checks and require Python dependencies and PostgreSQL. Frontend and root have separate lockfiles; install each with its own `npm ci` command. Next.js may report multiple lockfiles during build; this is not a shared npm workspace.

## Read code in this order

| File | What to learn |
| --- | --- |
| `client/src/components/three/material-scene.ts` | Scene, camera, geometry, material, mesh, lights, ownership |
| `client/src/components/three/material-scene.test.ts` | Check actual Three.js scene objects without a GPU |
| `client/src/components/three/material-canvas.tsx` | WebGL renderer, orbit controls, resize, redraw, React effect teardown |
| `client/src/components/three/material-lab.tsx` | HTML controls, client-only lazy loading, static fallback, error boundary |
| `client/src/app/page.tsx` | Mount one reusable lab without replacing catalog UI |

### Mental model

- **Scene** holds objects. Adding a mesh makes it part of that world.
- **Geometry** describes shape/vertices. `SphereGeometry` gives a familiar material sample.
- **Material** describes how light interacts with a surface. `MeshStandardMaterial` provides a built-in PBR shading model.
- **Mesh** pairs geometry and material. Same shape can display many materials.
- **Camera** chooses viewpoint. Perspective field of view, aspect ratio, and near/far planes affect what is visible.
- **Lights** illuminate surfaces. Metallic materials need useful surrounding illumination; directional/hemisphere lighting here is intentionally basic, not a calibrated studio environment.
- **Renderer** draws scene from camera onto canvas. It belongs in browser-only code, not server rendering.
- **Controls** change camera. HTML sliders change material values. A change triggers one render; no permanent animation loop is needed.

React owns component lifetime and UI state; Three.js owns mutable scene objects. The mount effect creates GPU resources once. A second effect applies material changes without rebuilding geometry. Closing, retrying, resetting the view, or unmounting disposes the owned geometry/material/controls/renderer and disconnects the resize observer. React Strict Mode deliberately rehearses setup/cleanup during development.

`dynamic(..., { ssr: false })` lives in a client component, and the canvas component is only mounted after an explicit click. Initial server HTML includes the static CSS sphere and controls. WebGL failure leaves that sample visible; it is an illustration, not a physically accurate poster. Later product previews need actual poster images.

## First lesson: change one thing, explain result

1. Read `createMaterialScene`; point to each term above before changing code.
2. Load the viewer. Set roughness near `0`, then near `1`. Explain highlight shape, not just brightness.
3. Compare metalness `0` and `1` at fixed color/roughness. Explain why lighting changes the result.
4. Change camera field of view from `40` to `60`. Predict framing first, then check it. Revert afterward.
5. Change the rim light's position/color. Explain which side of the sphere changes and why.
6. Drag the sphere, then focus the canvas and use Left/Right arrows and Home. Reset material and view.
7. Close and reopen the viewer several times. Explain why removing canvas alone is not GPU cleanup.
8. Run the four client checks above. Commit only when you understand the changes; no commit is created by this setup.

Do not complete later tasks by copying a large finished viewer. Use each `TASK-3D-*` acceptance criterion in `tasks.md` as one small learning milestone, and record what you changed, what you predicted, and what happened.

## Component path

| Milestone | Store component | New concept |
| --- | --- | --- |
| `TASK-3D-001` | Material lab (starter included) | Scene, PBR scalar values, browser/React lifecycle |
| `TASK-3D-002` | PBR texture inspector | UVs, tiling, color space, map loading/disposal |
| `TASK-3D-003` | Product detail material preview | Validated API metadata, approved URLs, static posters |
| `TASK-3D-004` | GLB product turntable | Scene graphs, bounds, loaders, resource budgets |
| `TASK-3D-005` | Material comparison / optional shader lab | Shared rendering, uniforms, GLSL |
| `TASK-3D-006` | Production-ready preview | Browser automation, mobile profiling, failure recovery |

Three.js is a renderer, not an asset converter. UE shaders, HLSL, and V-Ray/Corona materials do not run unchanged in this viewer. glTF/PBR exports can approximate compatible surfaces; lighting, tone mapping, and unsupported material features still differ. Do not promise exact parity.

## Guardrails

- Keep one active viewer, not one canvas per product card. Static product content and checkout must work without WebGL.
- Keep DOM controls and text accessible in Persian/English. Canvas includes keyboard orbit/reset instructions. No automatic animation means reduced-motion users receive no unsolicited movement.
- Render on demand; cap device pixel ratio at `2`. Avoid postprocessing, real-time shadows, physics, global viewer state, React Three Fiber, and Drei until a concrete component needs them.
- Treat preview assets as public. Never load paid source archives or private licensed downloads into browser previews. Future uploads need validated file types, byte/resource limits, approved origins, and safe external-resource handling.
- Texture disposal is separate from material disposal. Add explicit texture ownership when the texture lesson introduces maps.
- Before deployment, resolve existing dependency audit findings. Initial install reported Next.js/PostCSS and Vitest/transitive advisories; those need a separate dependency upgrade task, not `npm audit fix --force` as part of learning Three.js.

## Browser checks

For each change, verify initial static preview, loading, both languages, drag/keyboard orbit, range/color controls, reset, close/reopen, and a narrow viewport. In DevTools, simulate lost context with `WEBGL_lose_context`; confirm fallback appears and loading again creates a fresh viewer. Block WebGL entirely and confirm catalog text/buttons remain present. Test development Strict Mode as well as production build.

Scene unit tests do not prove GPU rendering, pointer behavior, accessibility, network failure handling, or leak-free repeated mounts. Automate those browser cases under `TASK-3D-006`; measure memory/frame time on real target hardware before claiming performance budgets.

## Official references

- [Three.js manual](https://threejs.org/manual/)
- [Fundamentals](https://threejs.org/manual/en/fundamentals.html)
- [Rendering on demand](https://threejs.org/manual/pages/rendering-on-demand.html)
- [Resource disposal](https://threejs.org/manual/pages/how-to-dispose-of-objects.html)
- [Three.js API](https://threejs.org/docs/): look up `MeshStandardMaterial`, `WebGLRenderer`, `OrbitControls`, and later `GLTFLoader`.

Start with fundamentals, use this repository's sphere to make each concept visible, then move to real PBR maps. Do not begin with custom shaders.
