import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo, useRef } from "react";
import type { Mesh } from "three";
import { useMatchStore } from "../store/matchStore";
import type { SimUnit } from "../sim/types";

function Ground({ size }: { size: number[] }) {
  const w = size[0] ?? 64;
  const h = size[1] ?? 64;
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[w / 2, 0, h / 2]} receiveShadow>
      <planeGeometry args={[w, h]} />
      <meshStandardMaterial color="#1a2332" />
    </mesh>
  );
}

function UnitMesh({
  unit,
  selected,
  onSelect,
}: {
  unit: SimUnit;
  selected: boolean;
  onSelect: () => void;
}) {
  const ref = useRef<Mesh>(null);
  const energyScale = 0.7 + unit.energy * 0.5;
  const y = unit.tier === "captain" ? 0.7 : unit.tier === "hybrid" ? 0.55 : 0.4;

  useFrame(() => {
    if (ref.current) {
      ref.current.position.set(unit.pos[0], y * energyScale * 0.5, unit.pos[1]);
    }
  });

  if (!unit.alive) {
    return (
      <mesh position={[unit.pos[0], 0.05, unit.pos[1]]}>
        <boxGeometry args={[0.35, 0.08, 0.35]} />
        <meshStandardMaterial color="#333" transparent opacity={0.4} />
      </mesh>
    );
  }

  const color = unit.color;
  const emissive = selected ? "#ffffff" : "#000000";
  const intensity = selected ? 0.35 : unit.energy * 0.15;

  const geo =
    unit.tier === "captain" ? (
      <coneGeometry args={[0.35, 0.9 * energyScale, 4]} />
    ) : unit.tier === "hybrid" ? (
      <octahedronGeometry args={[0.38 * energyScale, 0]} />
    ) : (
      <boxGeometry args={[0.4 * energyScale, 0.4 * energyScale, 0.4 * energyScale]} />
    );

  return (
    <mesh
      ref={ref}
      position={[unit.pos[0], y * energyScale * 0.5, unit.pos[1]]}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
      castShadow
    >
      {geo}
      <meshStandardMaterial
        color={color}
        emissive={emissive}
        emissiveIntensity={intensity}
      />
    </mesh>
  );
}

function SimLoop() {
  const tick = useMatchStore((s) => s.tick);
  useFrame((_, dt) => {
    tick(Math.min(dt, 0.05));
  });
  return null;
}

function Units() {
  const units = useMatchStore((s) => s.sim?.units ?? []);
  const selected = useMatchStore((s) => s.selectedUnitId);
  const selectUnit = useMatchStore((s) => s.selectUnit);
  return (
    <>
      {units.map((u) => (
        <UnitMesh
          key={u.id}
          unit={u}
          selected={selected === u.id}
          onSelect={() => selectUnit(u.id)}
        />
      ))}
    </>
  );
}

export function Battlefield() {
  const match = useMatchStore((s) => s.match);
  const size = match?.map.size ?? [64, 64];
  const cx = (size[0] ?? 64) / 2;
  const cz = (size[1] ?? 64) / 2;

  const cameraPos = useMemo(() => [cx + 28, 32, cz + 28] as [number, number, number], [cx, cz]);

  return (
    <Canvas
      shadows
      camera={{ position: cameraPos, fov: 40, near: 0.1, far: 200 }}
      onPointerMissed={() => useMatchStore.getState().selectUnit(null)}
    >
      <color attach="background" args={["#05070a"]} />
      <ambientLight intensity={0.45} />
      <directionalLight
        position={[cx + 20, 40, cz + 10]}
        intensity={1.1}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <Ground size={size} />
      {/* grid helper */}
      <gridHelper
        args={[Math.max(size[0] ?? 64, size[1] ?? 64), 32, "#2a3544", "#1c2530"]}
        position={[cx, 0.02, cz]}
      />
      {match && <Units />}
      {match && <SimLoop />}
      <OrbitControls target={[cx, 0, cz]} maxPolarAngle={Math.PI / 2.15} />
    </Canvas>
  );
}
