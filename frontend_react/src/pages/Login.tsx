import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Zap, Lock, Mail, Eye, EyeOff, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'
import DyeWhorl from '../components/ui/dye-whorl'
import { LiquidButton } from '../components/ui/liquid-glass-button'
import { ShimmerText } from '../components/ui/shimmer-text'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await api.post('/auth/login', { email, password })
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } }
  }

  return (
    <DyeWhorl className="min-h-screen w-full flex text-[#FFF7EE] !bg-transparent" density={1.2} speed={0.8} stir={1.5}>
      <div className="w-full flex flex-col lg:flex-row relative z-10 max-w-[1600px] mx-auto min-h-screen">
        
        {/* Left Side - Hero / Branding */}
        <div className="flex-1 p-8 md:p-16 lg:p-24 flex flex-col justify-center pointer-events-none">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="max-w-xl pointer-events-auto"
          >
            {/* Logo */}
            <motion.div variants={itemVariants} className="flex items-center gap-3 mb-12">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#C4749B] to-[#F6B98A] shadow-[0_0_24px_rgba(246,185,138,0.30)]">
                <Zap className="w-5 h-5 text-[#140F25]" strokeWidth={2.5} />
              </div>
              <div>
                <ShimmerText className="font-bold text-[#FFF7EE] text-[18px] tracking-tight leading-none block [--shimmer-contrast:rgba(246,185,138,0.8)]" duration={3}>
                  Candiq
                </ShimmerText>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[rgba(255,247,238,0.5)] mt-0.5">Candidate Intelligence OS</p>
              </div>
            </motion.div>

            {/* Headline */}
            <motion.h1 
              variants={itemVariants}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-[#FFF7EE] leading-[1.1] mb-6"
            >
              <ShimmerText className="[--shimmer-contrast:rgba(246,185,138,0.6)]" duration={2.5} delay={1}>
                Turn Resumes Into
              </ShimmerText> <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F6B98A] to-[#C4749B]">
                Hiring Intelligence.
              </span>
            </motion.h1>

            {/* Description */}
            <motion.p 
              variants={itemVariants}
              className="text-base md:text-lg text-[rgba(255,247,238,0.65)] leading-relaxed mb-12 max-w-lg"
            >
              Understand candidates beyond keywords with AI-powered resume intelligence, semantic matching, and recruitment analytics.
            </motion.p>

            {/* Value Props */}
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 sm:gap-8">
              {['Understand.', 'Match.', 'Discover.', 'Hire.'].map((step, i) => (
                <div key={step} className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#F6B98A]" strokeWidth={2.5} />
                  <span className="font-semibold text-sm text-[rgba(255,247,238,0.85)]">{step}</span>
                </div>
              ))}
            </motion.div>
          </motion.div>
        </div>

        {/* Right Side - Login Panel */}
        <div className="w-full lg:w-[500px] xl:w-[600px] p-4 md:p-8 lg:p-16 flex items-center justify-center pointer-events-none">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-md rounded-[24px] p-8 md:p-10 shadow-[0_30px_80px_rgba(20,10,40,0.35)] relative overflow-hidden pointer-events-auto"
            style={{
              background: 'rgba(58,44,110,0.72)',
              backdropFilter: 'blur(24px)',
              WebkitBackdropFilter: 'blur(24px)',
              border: '1px solid rgba(251,230,184,0.16)'
            }}
          >
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-[#FFF7EE] tracking-tight">Welcome back</h2>
              <p className="text-[14px] text-[rgba(255,247,238,0.55)] mt-1.5">Enter your credentials to access Candiq Intelligence OS.</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-5 relative z-20">
              {error && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-[rgba(251,113,133,0.12)] border border-[rgba(251,113,133,0.25)] animate-in fade-in slide-in-from-top-2">
                  <AlertCircle className="w-4 h-4 text-[#FB7185] shrink-0 mt-0.5" strokeWidth={2} />
                  <p className="text-[13px] text-[#FB7185] font-medium">{error}</p>
                </div>
              )}

              <div>
                <label className="block text-[11px] font-bold text-[rgba(255,247,238,0.65)] mb-2 uppercase tracking-[0.05em]">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-[rgba(255,247,238,0.4)]" strokeWidth={2} />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl outline-none transition-all placeholder:text-[rgba(251,230,184,0.30)] text-[#FBE6B8] text-[14px]"
                    style={{
                      background: 'rgba(58,44,110,0.45)',
                      border: '1px solid rgba(251,230,184,0.18)',
                    }}
                    onFocus={(e) => {
                      e.target.style.border = '1px solid #F6B98A';
                      e.target.style.boxShadow = '0 0 0 4px rgba(246,185,138,0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.border = '1px solid rgba(251,230,184,0.18)';
                      e.target.style.boxShadow = 'none';
                    }}
                    placeholder="name@company.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[rgba(255,247,238,0.65)] mb-2 uppercase tracking-[0.05em]">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-[rgba(255,247,238,0.4)]" strokeWidth={2} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-11 py-3 rounded-xl outline-none transition-all placeholder:text-[rgba(251,230,184,0.30)] text-[#FBE6B8] text-[14px]"
                    style={{
                      background: 'rgba(58,44,110,0.45)',
                      border: '1px solid rgba(251,230,184,0.18)',
                    }}
                    onFocus={(e) => {
                      e.target.style.border = '1px solid #F6B98A';
                      e.target.style.boxShadow = '0 0 0 4px rgba(246,185,138,0.1)';
                    }}
                    onBlur={(e) => {
                      e.target.style.border = '1px solid rgba(251,230,184,0.18)';
                      e.target.style.boxShadow = 'none';
                    }}
                    placeholder="••••••••"
                  />
                  <LiquidButton
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-1 top-1/2 -translate-y-1/2 text-[rgba(255,247,238,0.40)] hover:text-[rgba(255,247,238,0.80)] transition-colors h-9 w-9 bg-transparent"
                  >
                    {showPassword ? <EyeOff className="w-[18px] h-[18px]" /> : <Eye className="w-[18px] h-[18px]" />}
                  </LiquidButton>
                </div>
              </div>

              <div className="w-full mt-4 h-[56px] relative">
                <LiquidButton
                  disabled={loading}
                  className="w-full h-full text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_10px_25px_rgba(196,116,155,0.3)] rounded-xl disabled:opacity-50 text-lg"
                >
                  {loading ? 'Authenticating...' : 'Sign In'}
                </LiquidButton>
              </div>

              <div className="pt-6 mt-6 border-t border-[rgba(255,255,255,0.06)] text-center">
                <p className="text-[13px] text-[rgba(255,247,238,0.5)] flex items-center justify-center gap-1">
                  Don't have an account?{' '}
                  <LiquidButton variant="link" type="button" className="text-[#F6B98A] font-semibold hover:text-[#FBE6B8] transition-colors p-0 h-auto underline-offset-4">
                    Create account
                  </LiquidButton>
                </p>
                
                <LiquidButton
                  type="button"
                  variant="ghost"
                  onClick={() => { setEmail('admin@example.com'); setPassword('changeme123'); }}
                  className="mt-6 text-[11px] font-medium text-[rgba(255,247,238,0.35)] hover:text-[#F6B98A] transition-colors h-auto py-1 px-3 bg-transparent"
                >
                  ⚡ Fill demo credentials
                </LiquidButton>
              </div>
            </form>
          </motion.div>
        </div>
      </div>
    </DyeWhorl>
  )
}
