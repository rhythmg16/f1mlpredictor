import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export const TEAM_CAR_COLORS = {
  Mercedes: { primary: "#00D2BE", accent: "#111111" },
  Ferrari: { primary: "#E8002D", accent: "#FFD200" },
  McLaren: { primary: "#FF8000", accent: "#47C7FC" },
  "Red Bull Racing": { primary: "#3671C6", accent: "#FCD700" },
  "Racing Bulls": { primary: "#6692FF", accent: "#FFFFFF" },
  Alpine: { primary: "#FF87BC", accent: "#0090FF" },
  "Haas F1 Team": { primary: "#E10600", accent: "#FFFFFF" },
  Williams: { primary: "#64C4FF", accent: "#FFFFFF" },
  Audi: { primary: "#F50537", accent: "#111111" },
  "Aston Martin": { primary: "#229971", accent: "#CEDC00" },
  Cadillac: { primary: "#C4A35A", accent: "#111111" },
  "Kick Sauber": { primary: "#52E252", accent: "#111111" },
};

function hexColor(hex) {
  return new THREE.Color(hex);
}

function makeMat(hex, opts = {}) {
  return new THREE.MeshStandardMaterial({
    color: hexColor(hex),
    metalness: opts.metalness ?? 0.45,
    roughness: opts.roughness ?? 0.35,
    ...opts,
  });
}

export function createF1Car(primary = "#E8002D", accent = "#FFD200") {
  const car = new THREE.Group();
  const bodyMat = makeMat(primary);
  const accentMat = makeMat(accent, { metalness: 0.2, roughness: 0.4 });
  const darkMat = makeMat("#141414", { metalness: 0.7, roughness: 0.25 });
  const rubberMat = makeMat("#1a1a1a", { metalness: 0.1, roughness: 0.85 });
  const haloMat = makeMat("#c0c0c0", { metalness: 0.9, roughness: 0.2 });

  const nose = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.22, 1.4), bodyMat);
  nose.position.set(0, 0.28, 1.55);
  car.add(nose);

  const chassis = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.28, 2.2), bodyMat);
  chassis.position.set(0, 0.32, 0.15);
  car.add(chassis);

  const cockpit = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.28, 0.7), darkMat);
  cockpit.position.set(0, 0.52, -0.05);
  car.add(cockpit);

  const engineCover = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.35, 1.1), bodyMat);
  engineCover.position.set(0, 0.5, -0.95);
  car.add(engineCover);

  const airbox = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.28, 0.35), darkMat);
  airbox.position.set(0, 0.78, -0.55);
  car.add(airbox);

  const sideLeft = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.32, 1.2), bodyMat);
  sideLeft.position.set(-0.55, 0.34, -0.15);
  car.add(sideLeft);

  const sideRight = sideLeft.clone();
  sideRight.position.x = 0.55;
  car.add(sideRight);

  const sideAccentL = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.18, 0.9), accentMat);
  sideAccentL.position.set(-0.82, 0.38, -0.1);
  car.add(sideAccentL);

  const sideAccentR = sideAccentL.clone();
  sideAccentR.position.x = 0.82;
  car.add(sideAccentR);

  const frontWing = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.35), accentMat);
  frontWing.position.set(0, 0.12, 2.25);
  car.add(frontWing);

  const frontWingPlateL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.28, 0.35), darkMat);
  frontWingPlateL.position.set(-0.85, 0.22, 2.25);
  car.add(frontWingPlateL);

  const frontWingPlateR = frontWingPlateL.clone();
  frontWingPlateR.position.x = 0.85;
  car.add(frontWingPlateR);

  const rearWing = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.06, 0.28), accentMat);
  rearWing.position.set(0, 0.85, -1.75);
  car.add(rearWing);

  const rearWingTop = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.05, 0.2), bodyMat);
  rearWingTop.position.set(0, 1.05, -1.75);
  car.add(rearWingTop);

  const endplateL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.55, 0.35), darkMat);
  endplateL.position.set(-0.68, 0.85, -1.75);
  car.add(endplateL);

  const endplateR = endplateL.clone();
  endplateR.position.x = 0.68;
  car.add(endplateR);

  const halo = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.035, 10, 24, Math.PI), haloMat);
  halo.rotation.x = Math.PI / 2;
  halo.rotation.z = Math.PI;
  halo.position.set(0, 0.68, 0.05);
  car.add(halo);

  function addWheel(x, z) {
    const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.22, 18), rubberMat);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(x, 0.28, z);
    car.add(wheel);

    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.24, 12), haloMat);
    hub.rotation.z = Math.PI / 2;
    hub.position.set(x, 0.28, z);
    car.add(hub);
  }

  addWheel(-0.7, 1.35);
  addWheel(0.7, 1.35);
  addWheel(-0.75, -1.2);
  addWheel(0.75, -1.2);

  car.traverse((obj) => {
    if (obj.isMesh) {
      obj.castShadow = true;
      obj.receiveShadow = true;
    }
  });

  car.userData.bodyMats = [bodyMat];
  car.userData.accentMats = [accentMat];
  return car;
}

export class CarViewer {
  constructor(canvas) {
    this.canvas = canvas;
    this.stage = canvas.parentElement;
    this.teamName = null;
    this.dragging = false;

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    this.camera.position.set(4.2, 1.8, 5.2);

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = false;
    this.controls.minDistance = 4;
    this.controls.maxDistance = 9;
    this.controls.maxPolarAngle = Math.PI * 0.55;
    this.controls.minPolarAngle = Math.PI * 0.2;
    this.controls.target.set(0, 0.45, 0);
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 1.1;

    canvas.addEventListener("pointerdown", () => {
      this.dragging = true;
      this.controls.autoRotate = false;
    });
    window.addEventListener("pointerup", () => {
      this.dragging = false;
    });

    const hemi = new THREE.HemisphereLight(0xffffff, 0x222222, 1.1);
    this.scene.add(hemi);

    const key = new THREE.DirectionalLight(0xffffff, 1.35);
    key.position.set(4, 8, 3);
    key.castShadow = true;
    this.scene.add(key);

    const fill = new THREE.DirectionalLight(0xffffff, 0.45);
    fill.position.set(-5, 2, -2);
    this.scene.add(fill);

    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(4.5, 48),
      new THREE.MeshStandardMaterial({
        color: 0x000000,
        transparent: true,
        opacity: 0.18,
        metalness: 0,
        roughness: 1,
      })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = 0;
    ground.receiveShadow = true;
    this.scene.add(ground);

    this.car = createF1Car();
    this.scene.add(this.car);

    this._onResize = () => this.resize();
    window.addEventListener("resize", this._onResize);
    this.resize();
    this.animate();
  }

  setTeam(teamName) {
    this.teamName = teamName;
    const palette = TEAM_CAR_COLORS[teamName] || { primary: "#E8002D", accent: "#FFD200" };
    this.car.userData.bodyMats.forEach((mat) => mat.color.set(palette.primary));
    this.car.userData.accentMats.forEach((mat) => mat.color.set(palette.accent));
    this.controls.autoRotate = true;
  }

  resize() {
    const { clientWidth: w, clientHeight: h } = this.stage;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  animate = () => {
    requestAnimationFrame(this.animate);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };
}
