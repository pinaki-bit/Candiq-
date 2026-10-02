import { useState, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FileUp, Briefcase, Search, User,
  Activity, Settings, LogOut, Menu, X, ChevronDown,
  Zap, Bell
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { LiquidButton } from './ui/liquid-glass-button'

const NAV_SECTIONS = [
  {
    label: 'Core',
    items: [
      { name: 'Overview',         path: '/',          icon: LayoutDashboard },
      { name: 'Upload',           path: '/upload',    icon: FileUp },
      { name: 'Jobs',             path: '/jobs',      icon: Briefcase },
    ]
  },
  {
    label: 'Intelligence',
    items: [
      { name: 'Talent Explorer',  path: '/explorer',  icon: Search },
      { name: 'Candidate Portal', path: '/candidate', icon: User },
      { name: 'Analytics',        path: '/analytics', icon: Activity },
    ]
  },
  {
    label: 'System',
    items: [
      { name: 'Admin',            path: '/admin',     icon: Settings },
    ]
  }
]

const ALL_NAV = NAV_SECTIONS.flatMap(s => s.items)

export interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const isActive = (path: string) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)

  const SidebarNav = ({ onNav }: { onNav?: () => void }) => (
    <div className="flex flex-col h-full">
      <div className="px-5 pt-6 pb-7">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#C4749B] to-[#F6B98A] flex items-center justify-center shadow-[0_0_14px_rgba(246,185,138,0.30)] shrink-0">
            <Zap className="w-4 h-4 text-[#140F25]" strokeWidth={2.5} />
          </div>
          <div>
            <span className="font-bold text-[#FFF7EE] text-[15px] tracking-tight leading-none">Candiq</span>
            <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-[rgba(255,247,238,0.38)] mt-0.5">Intelligence OS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 overflow-y-auto custom-scrollbar space-y-5">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <p className="px-3 mb-1.5 text-[9.5px] font-bold uppercase tracking-[0.14em] text-[rgba(255,247,238,0.30)]">
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={onNav}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-150 relative ${
                      active
                        ? 'cq-nav-active text-[#FFF7EE]'
                        : 'text-[rgba(255,247,238,0.52)] hover:text-[rgba(255,247,238,0.88)] hover:bg-[rgba(58,44,110,0.40)]'
                    }`}
                  >
                    <item.icon
                      className={`w-[15px] h-[15px] shrink-0 ${active ? 'text-[#F6B98A]' : ''}`}
                      strokeWidth={active ? 2.5 : 2}
                    />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-3 pb-5 pt-4 mt-auto border-t border-[rgba(255,255,255,0.06)]">
        <LiquidButton
          variant="ghost"
          onClick={handleLogout}
          className="w-full flex items-center justify-start gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium text-[rgba(255,247,238,0.45)] hover:text-[#FB7185] hover:bg-[rgba(251,113,133,0.08)] transition-all duration-150 h-auto bg-transparent border-0 ring-0 shadow-none"
        >
          <LogOut className="w-[15px] h-[15px] shrink-0" strokeWidth={2} />
          <span>Sign Out</span>
        </LiquidButton>
      </div>
    </div>
  )

  const currentPage = ALL_NAV.find(i => isActive(i.path))

  return (
    <div className="flex h-screen w-full bg-transparent overflow-hidden">
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="flex h-full w-full relative z-10"
      >
        <aside className="hidden lg:block w-[240px] h-full shrink-0 relative z-20">
          <div className="absolute inset-0 bg-[rgba(20,15,37,0.82)] backdrop-blur-2xl border-r border-[rgba(255,255,255,0.07)]" />
          <div className="relative z-10 h-full">
            <SidebarNav />
          </div>
        </aside>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                onClick={() => setMobileOpen(false)}
                className="fixed inset-0 bg-[#140F25]/65 backdrop-blur-sm z-40 lg:hidden"
              />
              <motion.aside
                initial={{ x: '-100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ type: 'spring', damping: 28, stiffness: 300 }}
                className="fixed inset-y-0 left-0 w-[260px] z-50 lg:hidden"
              >
                <div className="absolute inset-0 bg-[rgba(20,15,37,0.95)] backdrop-blur-2xl border-r border-[rgba(255,255,255,0.09)]" />
                <div className="relative z-10 h-full">
                  <LiquidButton
                    variant="ghost"
                    size="icon"
                    onClick={() => setMobileOpen(false)}
                    className="absolute top-4 right-3 z-10 p-1.5 rounded-lg text-[rgba(255,247,238,0.45)] hover:text-[#FFF7EE] hover:bg-[rgba(255,255,255,0.06)] transition-colors h-8 w-8 bg-transparent"
                  >
                    <X className="w-4 h-4" />
                  </LiquidButton>
                  <SidebarNav onNav={() => setMobileOpen(false)} />
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
          <header className="h-14 shrink-0 flex items-center justify-between px-4 lg:px-6 border-b border-[rgba(255,255,255,0.07)] bg-[rgba(20,15,37,0.75)] backdrop-blur-xl z-20">
            <div className="flex items-center gap-3">
              <LiquidButton
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(true)}
                className="lg:hidden p-1.5 rounded-lg text-[rgba(255,247,238,0.55)] hover:text-[#FFF7EE] hover:bg-[rgba(255,255,255,0.06)] transition-colors h-8 w-8 bg-transparent"
              >
                <Menu className="w-5 h-5" strokeWidth={2} />
              </LiquidButton>
              <div className="flex items-center gap-1.5 text-sm">
                <span className="text-[rgba(255,247,238,0.35)] font-medium hidden sm:inline">Candiq</span>
                <span className="text-[rgba(255,247,238,0.18)] hidden sm:inline">/</span>
                <span className="text-[rgba(255,247,238,0.82)] font-semibold">{currentPage?.name ?? 'Dashboard'}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-[rgba(74,222,128,0.07)] border border-[rgba(74,222,128,0.16)]">
                <span className="cq-status-dot cq-status-online" />
                <span className="text-[9.5px] font-bold tracking-[0.10em] uppercase text-[rgba(74,222,128,0.85)]">AI Online</span>
              </div>
              <Bell className="w-4 h-4 text-[rgba(255,247,238,0.38)] cursor-pointer hover:text-[rgba(255,247,238,0.70)] transition-colors" strokeWidth={2} />
              <LiquidButton
                variant="ghost"
                onClick={handleLogout}
                title="Sign Out"
                className="flex items-center gap-1.5 pl-1.5 pr-2.5 py-1.5 rounded-lg border border-[rgba(255,255,255,0.08)] bg-[rgba(58,44,110,0.40)] hover:bg-[rgba(58,44,110,0.65)] hover:border-[rgba(246,185,138,0.20)] transition-all h-auto"
              >
                <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#C4749B] to-[#F6B98A] flex items-center justify-center text-[9px] font-bold text-[#140F25]">A</div>
                <ChevronDown className="w-3 h-3 text-[rgba(255,247,238,0.38)]" strokeWidth={2.5} />
              </LiquidButton>
            </div>
          </header>

          <main className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
            <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
              {children}
            </div>
          </main>
        </div>
      </motion.div>
    </div>
  )
}

export default Layout
