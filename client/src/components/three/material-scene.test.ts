import { describe, expect, it, vi } from "vitest";
import { MeshStandardMaterial, PerspectiveCamera, SphereGeometry } from "three";
import { createMaterialScene } from "./material-scene";

describe("material preview scene", () => {
  it("builds a lit PBR sphere with editable material values", () => {
    const preview = createMaterialScene({ color: "#00cddd", roughness: 0.35, metalness: 0.3 });
    expect(preview.camera).toBeInstanceOf(PerspectiveCamera);
    expect(preview.sphere.geometry).toBeInstanceOf(SphereGeometry);
    expect(preview.sphere.material).toBeInstanceOf(MeshStandardMaterial);
    expect(preview.sphere.material.color.getHexString()).toBe("00cddd");
    expect(preview.sphere.material.roughness).toBe(0.35);
    expect(preview.sphere.material.metalness).toBe(0.3);
    expect(preview.scene.children.filter((child) => child.type.endsWith("Light"))).toHaveLength(3);
    preview.dispose();
  });

  it("releases owned geometry and material on teardown", () => {
    const preview = createMaterialScene({ color: "#ffffff", roughness: 1, metalness: 0 });
    const geometry = vi.spyOn(preview.sphere.geometry, "dispose");
    const material = vi.spyOn(preview.sphere.material, "dispose");
    preview.dispose();
    expect(geometry).toHaveBeenCalledOnce();
    expect(material).toHaveBeenCalledOnce();
    expect(preview.scene.children).toHaveLength(0);
  });
});
