import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

export interface ParticleWaveProps {
  className?: string
  intensity?: number
  speed?: number
  opacity?: number
  interactive?: boolean
  particleColor?: string
}

export const ParticleWave: React.FC<ParticleWaveProps> = ({
  className = '',
  intensity = 1.0,
  speed = 1.0,
  opacity = 0.35,
  interactive = true,
  particleColor,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [hasWebGL, setHasWebGL] = useState<boolean>(true)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    // 1. WebGL Support Detection
    try {
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
      if (!gl) {
        setHasWebGL(false)
        return
      }
    } catch {
      setHasWebGL(false)
      return
    }

    // 2. Reduced Motion Detection
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // 3. Responsive Particle Count Setup
    const getGridDimensions = (width: number) => {
      if (width < 640) return { cols: 45, rows: 30 }
      if (width < 1024) return { cols: 80, rows: 50 }
      return { cols: 130, rows: 80 }
    }

    let width = container.clientWidth || window.innerWidth
    let height = container.clientHeight || window.innerHeight
    let { cols, rows } = getGridDimensions(width)

    // 4. Three.js Scene, Camera & Renderer Setup
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x201646, 0.012)

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
    camera.position.set(0, 18, 38)
    camera.lookAt(0, -2, 0)

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: false, // Performance optimized
      powerPreference: 'high-performance',
    })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)

    // 5. Geometry & Attributes Generation
    let geometry = new THREE.BufferGeometry()
    
    const buildGridGeometry = (colsCount: number, rowsCount: number) => {
      const total = colsCount * rowsCount
      const positions = new Float32Array(total * 3)
      const colors = new Float32Array(total * 3)
      const initialCoords = new Float32Array(total * 2)

      const spacingX = 0.55
      const spacingZ = 0.55
      const offsetX = (colsCount * spacingX) / 2
      const offsetZ = (rowsCount * spacingZ) / 2

      // Color Palette: Plum (#C4749B), Peach (#F6B98A), Butter (#FBE6B8)
      const color1 = particleColor ? new THREE.Color(particleColor) : new THREE.Color(0xC4749B)
      const color2 = new THREE.Color(0xF6B98A)
      const color3 = new THREE.Color(0xFBE6B8)

      let i = 0
      let c = 0
      let coordIdx = 0

      for (let r = 0; r < rowsCount; r++) {
        for (let cl = 0; cl < colsCount; cl++) {
          const x = cl * spacingX - offsetX
          const z = r * spacingZ - offsetZ
          const y = 0

          positions[i] = x
          positions[i + 1] = y
          positions[i + 2] = z

          initialCoords[coordIdx] = cl / colsCount
          initialCoords[coordIdx + 1] = r / rowsCount

          // Color gradient blend across the particle grid
          const factorX = cl / colsCount
          const factorZ = r / rowsCount
          const mixColor = new THREE.Color()

          if (factorX < 0.5) {
            mixColor.copy(color1).lerp(color2, factorX * 2)
          } else {
            mixColor.copy(color2).lerp(color3, (factorX - 0.5) * 2)
          }

          // Subtle Z depth dimming for atmospheric depth
          const depthDim = 1.0 - Math.min(1.0, factorZ * 0.4)
          colors[c] = mixColor.r * depthDim
          colors[c + 1] = mixColor.g * depthDim
          colors[c + 2] = mixColor.b * depthDim

          i += 3
          c += 3
          coordIdx += 2
        }
      }

      const geom = new THREE.BufferGeometry()
      geom.setAttribute('position', new THREE.BufferAttribute(positions, 3))
      geom.setAttribute('color', new THREE.BufferAttribute(colors, 3))
      geom.setAttribute('aGridCoord', new THREE.BufferAttribute(initialCoords, 2))
      return geom
    }

    geometry = buildGridGeometry(cols, rows)

    // 6. Custom Shaders for Smooth Wave & Point Softness
    const vertexShader = `
      uniform float uTime;
      uniform vec2 uMouse;
      uniform float uIntensity;
      uniform float uSpeed;
      
      attribute vec3 color;
      attribute vec2 aGridCoord;

      varying vec3 vColor;
      varying float vElevation;

      void main() {
        vColor = color;
        vec3 pos = position;

        // Wave Mathematics - Dual Frequency Sine Field
        float distToMouse = length(pos.xz - uMouse * 15.0);
        float mouseEffect = smoothstep(12.0, 0.0, distToMouse) * 1.5;

        float wave1 = sin(pos.x * 0.35 + uTime * 1.2 * uSpeed) * cos(pos.z * 0.35 + uTime * 1.0 * uSpeed) * 2.2;
        float wave2 = sin(pos.x * 0.7 - uTime * 0.8 * uSpeed + pos.z * 0.4) * 0.9;
        float wave3 = cos(aGridCoord.x * 6.28 + uTime * 0.5 * uSpeed) * 0.6;

        float elevation = (wave1 + wave2 + wave3 + mouseEffect) * uIntensity;
        pos.y += elevation;
        vElevation = elevation;

        vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
        gl_Position = projectionMatrix * mvPosition;

        // Depth-based point scaling
        gl_PointSize = (120.0 / -mvPosition.z) * (0.8 + elevation * 0.15);
      }
    `

    const fragmentShader = `
      varying vec3 vColor;
      varying float vElevation;

      void main() {
        // Soft circular particle rendering with smooth radial glow
        float dist = length(gl_PointCoord - vec2(0.5));
        if (dist > 0.5) discard;

        float alpha = smoothstep(0.5, 0.0, dist);
        // Highlight particle crests with brighter luminance
        vec3 finalColor = vColor + vec3(smoothstep(0.5, 2.5, vElevation) * 0.25);

        gl_FragColor = vec4(finalColor, alpha * 0.85);
      }
    `

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new THREE.Vector2(0, 0) },
        uIntensity: { value: intensity },
        uSpeed: { value: prefersReducedMotion ? 0.05 : speed },
      },
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })

    const particleSystem = new THREE.Points(geometry, material)
    scene.add(particleSystem)

    // 7. Mouse Interaction Tracking (Interpolated / Lerped)
    let mouseTargetX = 0
    let mouseTargetY = 0
    let mouseCurrentX = 0
    let mouseCurrentY = 0

    const handleMouseMove = (event: MouseEvent) => {
      if (!interactive) return
      mouseTargetX = (event.clientX / window.innerWidth) * 2 - 1
      mouseTargetY = -(event.clientY / window.innerHeight) * 2 + 1
    }

    if (interactive) {
      window.addEventListener('mousemove', handleMouseMove, { passive: true })
    }

    // 8. Resize Handler with Adaptive Quality
    const handleResize = () => {
      if (!container) return
      const newWidth = container.clientWidth || window.innerWidth
      const newHeight = container.clientHeight || window.innerHeight

      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()

      renderer.setSize(newWidth, newHeight)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

      const newGrid = getGridDimensions(newWidth)
      if (newGrid.cols !== cols || newGrid.rows !== rows) {
        cols = newGrid.cols
        rows = newGrid.rows

        particleSystem.geometry.dispose()
        particleSystem.geometry = buildGridGeometry(cols, rows)
      }
    }

    window.addEventListener('resize', handleResize, { passive: true })

    // 9. Animation Render Loop
    let animationFrameId: number
    const startTime = performance.now()

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)

      const elapsedTime = (performance.now() - startTime) * 0.001
      material.uniforms.uTime.value = elapsedTime

      // Smooth mouse position lerping
      if (interactive) {
        mouseCurrentX += (mouseTargetX - mouseCurrentX) * 0.04
        mouseCurrentY += (mouseTargetY - mouseCurrentY) * 0.04
        material.uniforms.uMouse.value.set(mouseCurrentX, mouseCurrentY)

        // Subtle camera inclination response
        camera.position.x = mouseCurrentX * 2.5
        camera.position.y = 18 + mouseCurrentY * 1.5
        camera.lookAt(0, -2, 0)
      }

      renderer.render(scene, camera)
    }

    animate()

    // 10. Clean Cleanup on Unmount (Zero Memory Leaks)
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
      if (interactive) {
        window.removeEventListener('mousemove', handleMouseMove)
      }

      geometry.dispose()
      material.dispose()
      renderer.dispose()
      scene.remove(particleSystem)
    }
  }, [intensity, speed, interactive, particleColor])

  // Fallback for non-WebGL environments
  if (!hasWebGL) {
    return (
      <div
        className={`fixed inset-0 pointer-events-none z-0 bg-gradient-to-tr from-[#0a0f1c] via-[#111827] to-[#0f172a] ${className}`}
        aria-hidden="true"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.15),transparent_70%)] animate-pulse" />
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`fixed inset-0 pointer-events-none overflow-hidden z-0 transition-opacity duration-1000 ${className}`}
      style={{ opacity }}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="block w-full h-full" />
      
      {/* Subtle Atmospheric Depth Glow & Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,#0a0f1c_95%)] pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-[#0a0f1c] to-transparent pointer-events-none" />
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0a0f1c] to-transparent pointer-events-none" />
    </div>
  )
}

export default ParticleWave
