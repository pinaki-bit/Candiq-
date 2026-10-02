import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import React from 'react'
import { Layout } from './components/Layout'
import { GlobalVisualBackground } from './components/ui/candiq-background'
import { UploadPortal } from './pages/UploadPortal'
import { TalentExplorer } from './pages/TalentExplorer'
import { AdminAnalytics } from './pages/AdminAnalytics'
import { Login } from './pages/Login'
import { Jobs } from './pages/Jobs'
import { CandidatePortal } from './pages/CandidatePortal'
import { PageShell } from './components/ui/PageShell'
import FeaturesWithPanel from './components/ui/features-with-panel'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function StatCard({
  label, value, icon: Icon, color, sub
}: {
  label: string; value: string | number; icon: React.ElementType;
  color: string; sub?: string
}) {
  return (
    <div className="cq-stat-card group">
      <div className="flex items-start justify-between mb-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.10em] text-[rgba(255,247,238,0.45)]">{label}</p>
        <div className={`p-1.5 rounded-lg bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.06)] ${color}`}>
          <Icon className="w-3.5 h-3.5" strokeWidth={2} />
        </div>
      </div>
      <p className="text-3xl font-bold text-[#FFF7EE] tracking-tight">{value}</p>
      {sub && <p className={`text-[11px] mt-1.5 font-medium ${color}`}>{sub}</p>}
    </div>
  )
}

function Dashboard() {
  return (
    <PageShell
      title="Candidate Intelligence Overview"
      subtitle="Your recruitment intelligence layer is active and processing."
    >
      <div className="flex flex-col gap-6">

        {/* Features With Panel - Animated Section */}
        <div className="mt-4">
          <FeaturesWithPanel />
        </div>

      </div>
    </PageShell>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="relative w-full min-h-screen bg-[#140F25] selection:bg-[#C4749B]/30">
        <GlobalVisualBackground />
        <div className="relative z-10 w-full min-h-screen">
          <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><UploadPortal /></ProtectedRoute>} />
        <Route path="/jobs" element={<ProtectedRoute><Jobs /></ProtectedRoute>} />
        <Route path="/explorer" element={<ProtectedRoute><TalentExplorer /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><AdminAnalytics /></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><AdminAnalytics /></ProtectedRoute>} />
        <Route path="/candidate" element={<ProtectedRoute><CandidatePortal /></ProtectedRoute>} />
      </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
