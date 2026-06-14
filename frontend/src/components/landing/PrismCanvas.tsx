import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { EdgesGeometry, MathUtils, OctahedronGeometry, type Group } from "three";

// Honor reduced-motion: the prism still renders, it just holds still.
const REDUCED =
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** A faceted dark-glass crystal that slowly rotates, gently floats, and tilts toward the pointer. */
function Prism() {
  const tilt = useRef<Group>(null);
  const spin = useRef<Group>(null);

  // Share one geometry between the glass body and its glowing edge overlay.
  const geometry = useMemo(() => new OctahedronGeometry(1.4, 0), []);
  const edges = useMemo(() => new EdgesGeometry(geometry), [geometry]);

  useFrame((state, delta) => {
    const spinGroup = spin.current;
    const tiltGroup = tilt.current;
    if (!spinGroup || !tiltGroup || REDUCED) return;

    // Continuous slow rotation.
    spinGroup.rotation.y += delta * 0.22;
    spinGroup.rotation.x += delta * 0.06;
    // Gentle vertical float + parallax tilt easing toward the pointer.
    tiltGroup.position.y = Math.sin(state.clock.elapsedTime * 0.6) * 0.12;
    tiltGroup.rotation.x = MathUtils.lerp(tiltGroup.rotation.x, -state.pointer.y * 0.3, 0.05);
    tiltGroup.rotation.y = MathUtils.lerp(tiltGroup.rotation.y, state.pointer.x * 0.4, 0.05);
  });

  return (
    <group ref={tilt}>
      <group ref={spin} scale={[1, 1.4, 1]}>
        <mesh geometry={geometry}>
          <meshPhysicalMaterial
            color="#10131d"
            metalness={0.35}
            roughness={0.15}
            transmission={0.5}
            thickness={1.5}
            ior={1.5}
            clearcoat={1}
            clearcoatRoughness={0.15}
            reflectivity={0.7}
            attenuationColor="#0a84ff"
            attenuationDistance={2}
            flatShading
          />
        </mesh>
        {/* Glowing accent edges keep the crystal silhouette legible against pure black. */}
        <lineSegments geometry={edges}>
          <lineBasicMaterial color="#3a9bff" transparent opacity={0.72} />
        </lineSegments>
      </group>
    </group>
  );
}

/** The hero's floating dark-glass prism. Lazy-loaded so three.js stays out of the initial bundle. */
export default function PrismCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0, 4.4], fov: 45 }}
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      style={{ width: "100%", height: "100%" }}
    >
      <ambientLight intensity={0.55} />
      {/* Broad key light for facet gradients + cool/accent rim lights for edge glints. */}
      <directionalLight position={[5, 8, 6]} intensity={2.8} color="#ffffff" />
      <pointLight position={[-6, -2, 4]} intensity={160} color="#0a84ff" />
      <pointLight position={[4, 4, 5]} intensity={110} color="#9ccbff" />
      <Prism />
    </Canvas>
  );
}
