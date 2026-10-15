import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import type { Room, RoomFixture } from '../../db'
import { cmToMeters } from '../../lib/homeLayout'
import { FIXTURE_LABELS } from '../../lib/fixtures'

type Props = {
  rooms: Room[]
  fixtures: RoomFixture[]
  planCols: number
  planRows: number
}

function Orbit() {
  const { camera, gl } = useThree()
  const controls = useRef<OrbitControls | null>(null)

  useEffect(() => {
    const c = new OrbitControls(camera, gl.domElement)
    c.enableDamping = true
    c.target.set(0, 0.9, 0)
    c.maxPolarAngle = Math.PI * 0.49
    c.minDistance = 4
    c.maxDistance = 48
    controls.current = c
    return () => c.dispose()
  }, [camera, gl])

  useFrame(() => controls.current?.update())
  return null
}

function FixtureMark({
  fixture,
  roomW,
  roomD,
  roomH,
}: {
  fixture: RoomFixture
  roomW: number
  roomD: number
  roomH: number
}) {
  const isWindow = fixture.kind === 'window' || fixture.kind === 'french'
  const color = isWindow ? '#7dd3fc' : '#fbbf24'
  const maxAlong = fixture.wall === 'N' || fixture.wall === 'S' ? roomW : roomD
  const w = Math.max(0.2, Math.min(fixture.widthM, maxAlong))
  const h = Math.max(0.2, Math.min(fixture.heightM, roomH))
  const sill = Math.max(0, Math.min(fixture.sillM, roomH - h))
  const along = Math.max(w / 2, Math.min(maxAlong - w / 2, fixture.offsetM + w / 2))

  const halfW = roomW / 2
  const halfD = roomD / 2
  let position: [number, number, number] = [0, sill + h / 2, 0]

  if (fixture.wall === 'N') position = [-halfW + along, sill + h / 2, -halfD]
  else if (fixture.wall === 'S') position = [-halfW + along, sill + h / 2, halfD]
  else if (fixture.wall === 'W') position = [-halfW, sill + h / 2, -halfD + along]
  else position = [halfW, sill + h / 2, -halfD + along]

  const panelW = fixture.wall === 'E' || fixture.wall === 'W' ? 0.1 : w
  const panelD = fixture.wall === 'E' || fixture.wall === 'W' ? w : 0.1

  return (
    <mesh position={position}>
      <boxGeometry args={[panelW, h, panelD]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={isWindow ? 0.5 : 0.9}
        emissive={color}
        emissiveIntensity={0.2}
      />
    </mesh>
  )
}

function RoomBox({
  room,
  fixtures,
  planCols,
  planRows,
}: {
  room: Room
  fixtures: RoomFixture[]
  planCols: number
  planRows: number
}) {
  const w = room.gridW
  const d = room.gridH
  const h = cmToMeters(room.heightCm) || 2.8
  const x = room.gridX + w / 2 - planCols / 2
  const z = room.gridY + d / 2 - planRows / 2
  const mine = fixtures.filter((f) => f.roomId === room.id)
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(w, h, d)), [w, h, d])

  return (
    <group position={[x, 0, z]}>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color="#1e293b" transparent opacity={0.32} depthWrite={false} />
      </mesh>
      <lineSegments position={[0, h / 2, 0]} geometry={edges}>
        <lineBasicMaterial color="#94a3b8" />
      </lineSegments>
      {mine.map((fixture) => (
        <FixtureMark key={fixture.id} fixture={fixture} roomW={w} roomD={d} roomH={h} />
      ))}
    </group>
  )
}

function Scene({ rooms, fixtures, planCols, planRows }: Props) {
  return (
    <>
      <color attach="background" args={['#05070b']} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[8, 14, 6]} intensity={1.1} />
      <directionalLight position={[-6, 8, -4]} intensity={0.35} />
      <Orbit />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[planCols + 2, planRows + 2]} />
        <meshStandardMaterial color="#0b1220" />
      </mesh>
      <gridHelper
        args={[Math.max(planCols, planRows) + 2, Math.max(planCols, planRows) + 2, '#334155', '#1e293b']}
        position={[0, 0.01, 0]}
      />
      {rooms.map((room) => (
        <RoomBox
          key={room.id}
          room={room}
          fixtures={fixtures}
          planCols={planCols}
          planRows={planRows}
        />
      ))}
    </>
  )
}

export function House3D({ rooms, fixtures, planCols, planRows }: Props) {
  if (rooms.length === 0) {
    return <p className="empty">尚无房间可展示。</p>
  }

  return (
    <div className="house3d">
      <div className="house3d-legend">
        <span className="house3d-swatch door" /> 门
        <span className="house3d-swatch window" /> 窗
        {fixtures.slice(0, 5).map((f) => (
          <span key={f.id} className="house3d-chip">
            {FIXTURE_LABELS[f.kind]}·{f.name}
          </span>
        ))}
      </div>
      <div className="house3d-canvas">
        <Canvas camera={{ position: [planCols * 0.75, Math.max(6, planCols * 0.5), planRows * 0.9], fov: 42 }}>
          <Scene rooms={rooms} fixtures={fixtures} planCols={planCols} planRows={planRows} />
        </Canvas>
      </div>
      <p className="section-lead">拖拽旋转，滚轮缩放。半透明体块为房间，亮条为门窗。</p>
    </div>
  )
}
