let layoutCenter = { x: 0, z: 0 };

export function setLayoutCenter(cx: number, cz: number): void {
  layoutCenter = { x: cx, z: cz };
}

export function gridToWorld(gx: number, gz: number): [number, number, number] {
  const spacing = 1.6;
  return [
    (gx - layoutCenter.x) * spacing,
    0,
    (gz - layoutCenter.z) * spacing,
  ];
}

export function conwayNeighborPattern(gx: number, gz: number, tick: number): number {
  const hash = (Math.floor(gx * 3) * 7 + Math.floor(gz * 3) * 13 + tick) % 9;
  return hash < 3 ? 0.15 : hash < 6 ? 0.08 : 0;
}