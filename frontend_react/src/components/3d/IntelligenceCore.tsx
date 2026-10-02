import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function ParticleSwarm({ count = 1000 }) {
  const points = useRef<THREE.Points>(null)

  // Generate random points in a sphere
  const positions = useMemo(() => {
    const p = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const radius = 2 + Math.random() * 0.5
      const theta = 2 * Math.PI * Math.random()
      const phi = Math.acos(2 * Math.random() - 1)
      
      const x = radius * Math.sin(phi) * Math.cos(theta)
      const y = radius * Math.sin(phi) * Math.sin(theta)
      const z = radius * Math.cos(phi)
      
      p[i * 3] = x
      p[i * 3 + 1] = y
      p[i * 3 + 2] = z
    }
    return p
  }, [count])

  // Animate rotation
  useFrame((_state, delta) => {
    if (points.current) {
      points.current.rotation.y -= delta * 0.1
      points.current.rotation.x -= delta * 0.05
    }
  })

  return (
    <Points ref={points} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#F6B98A"
        size={0.035}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  )
}

function InnerCore() {
  const mesh = useRef<THREE.Mesh>(null)
  
  useFrame((_state, delta) => {
    if (mesh.current) {
      mesh.current.rotation.y += delta * 0.2
      mesh.current.rotation.z += delta * 0.1
    }
  })

  return (
    <mesh ref={mesh}>
      <icosahedronGeometry args={[1.2, 2]} />
      <meshStandardMaterial 
        color="#C4749B" 
        wireframe 
        transparent 
        opacity={0.4}
        emissive="#C4749B"
        emissiveIntensity={0.6}
      />
    </mesh>
  )
}

export function IntelligenceCore() {
  return (
    <div className="w-full h-full relative">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }} gl={{ alpha: true }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1.2} color="#F6B98A" />
        <ParticleSwarm count={1500} />
        <InnerCore />
      </Canvas>
    </div>
  )
}
