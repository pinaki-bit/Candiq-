import React from 'react'
import { ParticleWave } from './particle-wave'

export function GlobalVisualBackground() {
  return (
    <div className="fixed inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
      {/* 1. Base Gradient */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(165deg, #3A2C6E 0%, #C4749B 33%, #F6B98A 67%, #FBE6B8 100%)',
          opacity: 0.85
        }}
      />
      
      {/* 2. Grain (using SVG filter approach for subtlety) */}
      <div 
        className="absolute inset-0 opacity-[0.03] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`
        }}
      />

      {/* 3. Subtle Particle Field */}
      <div className="absolute inset-0 mix-blend-screen opacity-60">
         <ParticleWave 
           opacity={0.20} 
           intensity={0.8} 
           speed={0.4} 
           interactive={false} 
           className="w-full h-full"
         />
      </div>

      {/* 4. Atmospheric Depth (Radial glows) */}
      <div 
        className="absolute inset-0" 
        style={{
          background: 'radial-gradient(circle at 15% 20%, rgba(58,44,110,0.4) 0%, transparent 50%), radial-gradient(circle at 85% 85%, rgba(246,185,138,0.15) 0%, transparent 50%)'
        }}
      />
      
      {/* 5. Dark Vignette to ground the UI */}
      <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_150px_rgba(20,15,37,0.5)]" />
    </div>
  )
}
