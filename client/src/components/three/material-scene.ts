import {
  DirectionalLight, HemisphereLight, Mesh, MeshStandardMaterial,
  PerspectiveCamera, Scene, SphereGeometry,
} from "three";

export type MaterialSettings = { color: string; roughness: number; metalness: number };

export function createMaterialScene(settings: MaterialSettings) {
  const scene = new Scene();
  const camera = new PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 0, 3.6);
  const geometry = new SphereGeometry(1, 48, 32);
  const material = new MeshStandardMaterial(settings);
  const sphere = new Mesh(geometry, material);
  const key = new DirectionalLight(0xffffff, 4);
  key.position.set(3, 4, 5);
  const rim = new DirectionalLight(0x00ddeb, 2);
  rim.position.set(-3, 1, -2);
  scene.add(sphere, key, rim, new HemisphereLight(0xcceeff, 0x202030, 2));
  return {
    scene, camera, sphere,
    dispose() {
      geometry.dispose();
      material.dispose();
      scene.clear();
    },
  };
}
