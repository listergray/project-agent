import { Canvas, useFrame, useLoader, useThree } from '@react-three/fiber'
import { Suspense, useMemo, useRef } from 'react'
import {
  AdditiveBlending,
  Color,
  DoubleSide,
  FogExp2,
  Object3D,
  SRGBColorSpace,
  TextureLoader,
  type InstancedMesh,
  type Mesh,
  type Points,
} from 'three'

const INK = '#141c18'
const JADE = '#6f8f82'
const MIST = '#d5ddd8'
const GOLD = '#e8d5a3'
const CINNABAR = '#c45c52'

const silkVert = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const silkFrag = /* glsl */ `
uniform float uTime;
uniform vec3 uA;
uniform vec3 uB;
uniform vec3 uC;
varying vec2 vUv;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}
float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
    f.y
  );
}
float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * noise(p);
    p *= 2.04;
    a *= 0.52;
  }
  return v;
}
void main() {
  vec2 uv = vUv;
  float n = fbm(uv * 2.8 + vec2(uTime * 0.035, uTime * 0.018));
  float m = fbm(uv * 4.6 - vec2(uTime * 0.05, uTime * 0.01));
  float ridge = smoothstep(0.35, 0.82, n);
  vec3 col = mix(uA, uB, n);
  col = mix(col, uC, m * 0.4);
  float alpha = 0.22 + ridge * 0.42;
  gl_FragColor = vec4(col, alpha * (0.35 + vUv.y * 0.65));
}
`

function Backdrop() {
  const map = useLoader(TextureLoader, '/cover.jpg')
  map.colorSpace = SRGBColorSpace
  const ref = useRef<Mesh>(null)
  useFrame((_, dt) => {
    if (!ref.current) return
    ref.current.rotation.z += dt * 0.004
  })
  return (
    <mesh ref={ref} position={[0.6, 1.15, -10]} scale={[19.2, 11.2, 1]}>
      <planeGeometry args={[1, 1]} />
      <meshBasicMaterial map={map} />
    </mesh>
  )
}

function SilkMist() {
  const mat = useRef<{ uniforms: { uTime: { value: number } } }>(null)
  useFrame((_, dt) => {
    if (mat.current) mat.current.uniforms.uTime.value += dt
  })
  return (
    <mesh position={[0, 0.15, -1.2]} rotation={[-0.42, 0.08, 0]} scale={[16, 7.5, 1]}>
      <planeGeometry args={[1, 1]} />
      <shaderMaterial
        ref={mat}
        transparent
        depthWrite={false}
        vertexShader={silkVert}
        fragmentShader={silkFrag}
        uniforms={{
          uTime: { value: 0 },
          uA: { value: new Color(INK) },
          uB: { value: new Color(JADE) },
          uC: { value: new Color(MIST) },
        }}
      />
    </mesh>
  )
}

function Peak({
  position,
  scale,
  color,
  delay = 0,
}: {
  position: [number, number, number]
  scale: [number, number, number]
  color: string
  delay?: number
}) {
  const ref = useRef<Mesh>(null)
  useFrame((state) => {
    if (!ref.current) return
    ref.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.35 + delay) * 0.04
  })
  return (
    <mesh ref={ref} position={position} scale={scale} rotation={[0, 0.15, 0]}>
      <coneGeometry args={[1, 2.4, 5]} />
      <meshStandardMaterial color={color} roughness={0.95} metalness={0.08} />
    </mesh>
  )
}

function GoldMotes() {
  const ref = useRef<Points>(null)
  const positions = useMemo(() => {
    const arr = new Float32Array(420 * 3)
    for (let i = 0; i < 420; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 14
      arr[i * 3 + 1] = Math.random() * 6 - 0.4
      arr[i * 3 + 2] = (Math.random() - 0.5) * 8 - 1
    }
    return arr
  }, [])

  useFrame((_, dt) => {
    const pts = ref.current
    if (!pts) return
    const attr = pts.geometry.attributes.position
    for (let i = 0; i < 420; i++) {
      let y = attr.getY(i) + dt * (0.08 + (i % 7) * 0.01)
      if (y > 5.6) y = -0.6
      attr.setY(i, y)
      attr.setX(i, attr.getX(i) + Math.sin(y + i) * dt * 0.04)
    }
    attr.needsUpdate = true
    pts.rotation.y += dt * 0.012
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color={GOLD}
        size={0.035}
        transparent
        opacity={0.72}
        depthWrite={false}
        blending={AdditiveBlending}
      />
    </points>
  )
}

const lanternSpots: [number, number, number][] = [
  [-2.4, 0.55, 0.8],
  [2.8, 0.95, -0.4],
  [-0.6, 1.4, -1.8],
  [1.5, 0.35, 1.4],
  [-3.2, 1.1, -2.2],
  [3.4, 1.7, -3],
]

function Lanterns() {
  const ref = useRef<InstancedMesh>(null)
  const dummy = useMemo(() => new Object3D(), [])

  useFrame((state) => {
    const mesh = ref.current
    if (!mesh) return
    lanternSpots.forEach((p, i) => {
      dummy.position.set(p[0], p[1] + Math.sin(state.clock.elapsedTime * 0.7 + i) * 0.12, p[2])
      dummy.rotation.set(0, state.clock.elapsedTime * 0.2 + i, 0.12)
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)
    })
    mesh.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={ref} args={[undefined, undefined, lanternSpots.length]}>
      <sphereGeometry args={[0.07, 10, 10]} />
      <meshStandardMaterial
        color={CINNABAR}
        emissive={CINNABAR}
        emissiveIntensity={1.8}
        roughness={0.4}
      />
    </instancedMesh>
  )
}

function Shafts() {
  return (
    <group position={[3.2, 3.4, -4]} rotation={[0, 0, -0.55]}>
      {[0, 0.18, -0.16, 0.34].map((x, i) => (
        <mesh key={i} position={[x, 0, 0]} rotation={[0.2, 0, 0]}>
          <cylinderGeometry args={[0.04 + i * 0.05, 1.1, 16, 12, 1, true]} />
          <meshBasicMaterial
            color={GOLD}
            transparent
            opacity={0.05 + i * 0.015}
            side={DoubleSide}
            depthWrite={false}
            blending={AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  )
}

function Rig() {
  const { camera, pointer } = useThree()
  useFrame(() => {
    camera.position.x += (pointer.x * 0.72 - camera.position.x) * 0.028
    camera.position.y += (1.15 + pointer.y * 0.28 - camera.position.y) * 0.028
    camera.lookAt(0, 0.55, 0)
  })
  return null
}

function FogSetup() {
  const { scene } = useThree()
  scene.fog = new FogExp2('#1a221e', 0.055)
  scene.background = new Color('#161e1a')
  return null
}

function World() {
  return (
    <>
      <FogSetup />
      <Rig />
      <ambientLight intensity={0.35} color="#c9d4ce" />
      <directionalLight position={[6, 8, 2]} intensity={1.35} color="#fff1d0" />
      <pointLight position={[-3, 1.4, 2]} intensity={8} distance={7} color={CINNABAR} />
      <Backdrop />
      <SilkMist />
      <Peak position={[-3.6, -0.2, -2.4]} scale={[2.2, 2.6, 1.6]} color="#0f1614" delay={0.2} />
      <Peak position={[-1.4, -0.35, -1.4]} scale={[1.5, 1.9, 1.2]} color="#1a2420" delay={1.1} />
      <Peak position={[3.1, -0.15, -2.8]} scale={[2.8, 3.2, 1.8]} color="#121a17" delay={0.6} />
      <Peak position={[1.1, -0.5, -0.6]} scale={[1.1, 1.3, 0.9]} color="#24302b" delay={1.7} />
      <Peak position={[-4.8, -0.4, -4.2]} scale={[3.4, 3.8, 2]} color="#0c1210" delay={0.9} />
      <Shafts />
      <GoldMotes />
      <Lanterns />
    </>
  )
}

export function ShanShui() {
  return (
    <Canvas
      className="cover-canvas"
      dpr={[1, 1.6]}
      camera={{ position: [0, 1.15, 5.5], fov: 40, near: 0.1, far: 40 }}
      gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
    >
      <Suspense fallback={null}>
        <World />
      </Suspense>
    </Canvas>
  )
}
