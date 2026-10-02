import { useState, useEffect, useRef } from 'react'
import {
  GitCompareArrows, Users, ChevronDown, Trophy,
  Sparkles, Layers, Check, X as XIcon, Search
} from 'lucide-react'
import { compareCandidates } from '../services/compareApi'
import type { CompareResponse, CandidateCompareProfile } from '../services/compareApi'
import { getJobs } from '../services/jobs'
import type { Job } from '../services/jobs'
import { api } from '../lib/api'
import { PageShell } from '../components/ui/PageShell'
import { LiquidButton } from '../components/ui/liquid-glass-button'

// Colors for candidates
const CANDIDATE_COLORS = ['#F6B98A', '#C084FC', '#4ADE80', '#60A5FA', '#FB7185', '#FBBF24']

interface CandidateOption {
  id: number
  display_name: string | null
  email: string | null
  stage: string | null
  relevance_score: number | null
}

export function Compare() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [candidates, setCandidates] = useState<CandidateOption[]>([])
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<number[]>([])
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [candidateSearch, setCandidateSearch] = useState('')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    if (selectedJobId) fetchCandidates()
  }, [selectedJobId])

  useEffect(() => {
    if (result) drawRadarChart()
  }, [result])

  const fetchJobs = async () => {
    try {
      const data = await getJobs()
      setJobs(data)
      if (data.length > 0) setSelectedJobId(data[0].id)
    } catch (err) {
      console.error('Failed to fetch jobs', err)
    }
  }

  const fetchCandidates = async () => {
    if (!selectedJobId) return
    try {
      const res = await api.get(`/pipeline/${selectedJobId}`)
      const pipelineEntries = res.data as any[]
      
      const opts: CandidateOption[] = pipelineEntries.map(entry => ({
        id: entry.candidate_id,
        display_name: entry.candidate_name || `Candidate #${entry.candidate_id}`,
        email: entry.candidate_email,
        stage: entry.stage,
        relevance_score: entry.relevance_score,
      }))
      
      setCandidates(opts)
    } catch (err) {
      console.error('Failed to fetch pipeline candidates', err)
    }
  }

  const toggleCandidate = (id: number) => {
    setSelectedCandidateIds(prev => {
      if (prev.includes(id)) return prev.filter(i => i !== id)
      if (prev.length >= 4) return prev
      return [...prev, id]
    })
  }

  const handleCompare = async () => {
    if (!selectedJobId || selectedCandidateIds.length < 2) {
      setError('Select at least 2 candidates to compare.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await compareCandidates(selectedJobId, selectedCandidateIds)
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Comparison failed.')
    } finally {
      setLoading(false)
    }
  }

  // --- Radar Chart Drawing ---
  const drawRadarChart = () => {
    const canvas = canvasRef.current
    if (!canvas || !result) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const size = 320
    canvas.width = size * dpr
    canvas.height = size * dpr
    canvas.style.width = `${size}px`
    canvas.style.height = `${size}px`
    ctx.scale(dpr, dpr)

    const cx = size / 2
    const cy = size / 2
    const radius = 120
    const dims = result.radar_chart
    const n = dims.length
    if (n === 0) return

    ctx.clearRect(0, 0, size, size)

    // Draw grid rings
    for (let ring = 1; ring <= 4; ring++) {
      const r = (radius / 4) * ring
      ctx.beginPath()
      for (let i = 0; i <= n; i++) {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2
        const x = cx + r * Math.cos(angle)
        const y = cy + r * Math.sin(angle)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.strokeStyle = 'rgba(255,255,255,0.08)'
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // Draw axis lines and labels
    for (let i = 0; i < n; i++) {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2
      const x = cx + radius * Math.cos(angle)
      const y = cy + radius * Math.sin(angle)

      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(x, y)
      ctx.strokeStyle = 'rgba(255,255,255,0.06)'
      ctx.lineWidth = 1
      ctx.stroke()

      // Label
      const labelX = cx + (radius + 16) * Math.cos(angle)
      const labelY = cy + (radius + 16) * Math.sin(angle)
      ctx.font = '9px system-ui'
      ctx.fillStyle = 'rgba(255,247,238,0.50)'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      // Abbreviate labels
      const label = dims[i].dimension.replace('Coverage', 'Cov').replace('Relevance ', '')
      ctx.fillText(label, labelX, labelY)
    }

    // Draw candidate polygons
    const candidateIds = Object.keys(dims[0].values)
    candidateIds.forEach((cidStr, colorIdx) => {
      const color = CANDIDATE_COLORS[colorIdx % CANDIDATE_COLORS.length]

      ctx.beginPath()
      for (let i = 0; i <= n; i++) {
        const dim = dims[i % n]
        const val = (dim.values[cidStr] || 0) / 100
        const angle = (Math.PI * 2 * (i % n)) / n - Math.PI / 2
        const x = cx + radius * val * Math.cos(angle)
        const y = cy + radius * val * Math.sin(angle)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.closePath()

      // Fill
      ctx.fillStyle = color + '18'
      ctx.fill()

      // Stroke
      ctx.strokeStyle = color + 'AA'
      ctx.lineWidth = 2
      ctx.stroke()

      // Dots
      for (let i = 0; i < n; i++) {
        const dim = dims[i]
        const val = (dim.values[cidStr] || 0) / 100
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2
        const x = cx + radius * val * Math.cos(angle)
        const y = cy + radius * val * Math.sin(angle)
        ctx.beginPath()
        ctx.arc(x, y, 3, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
      }
    })
  }

  const getCandidateName = (profile: CandidateCompareProfile) =>
    profile.candidate_name || `Candidate #${profile.candidate_id}`

  return (
    <PageShell
      title="Candidate Comparison"
      subtitle="Compare candidates side-by-side with radar charts, skill overlap, and AI-powered insights."
    >
      <div className="flex flex-col gap-6">

        {/* Selection Controls */}
        <div className="cq-card-elevated rounded-2xl p-5">
          <div className="flex flex-col sm:flex-row items-start gap-5">
            {/* Job Picker */}
            <div className="flex flex-col gap-1.5 shrink-0">
              <div className="h-8 flex items-center">
                <label className="text-[11px] font-bold text-[rgba(255,247,238,0.45)] uppercase tracking-wider">Job</label>
              </div>
              <div className="relative">
                <select
                  value={selectedJobId ?? ''}
                  onChange={(e) => { setSelectedJobId(Number(e.target.value)); setResult(null); setSelectedCandidateIds([]) }}
                  className="appearance-none pl-4 pr-10 py-2.5 rounded-xl text-[13px] font-medium text-[#FBE6B8] outline-none cursor-pointer min-w-[200px]"
                  style={{ background: 'rgba(58,44,110,0.45)', border: '1px solid rgba(251,230,184,0.18)' }}
                >
                  {jobs.map(j => (
                    <option key={j.id} value={j.id} className="bg-[#1E163A] text-[#FBE6B8]">{j.title}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(255,247,238,0.40)] pointer-events-none" />
              </div>
            </div>

            {/* Candidate Selection */}
            <div className="flex flex-col gap-1.5 flex-1 min-w-[300px]">
              <div className="h-8 flex items-center justify-between">
                <label className="text-[11px] font-bold text-[rgba(255,247,238,0.45)] uppercase tracking-wider">
                  Select Candidates (2-4)
                </label>
                
                {/* Search Bar */}
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[rgba(255,247,238,0.35)]" />
                  <input 
                    type="text" 
                    placeholder="Search candidates..."
                    value={candidateSearch}
                    onChange={(e) => setCandidateSearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 rounded-lg text-[11px] font-medium text-[#FFF7EE] outline-none w-[180px]"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                  />
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 max-h-[120px] overflow-y-auto custom-scrollbar p-1">
                {candidates
                  .filter(c => 
                    !candidateSearch || 
                    (c.display_name && c.display_name.toLowerCase().includes(candidateSearch.toLowerCase())) ||
                    (c.email && c.email.toLowerCase().includes(candidateSearch.toLowerCase()))
                  )
                  .map((c) => {
                  const selected = selectedCandidateIds.includes(c.id)
                  const color = selected ? CANDIDATE_COLORS[selectedCandidateIds.indexOf(c.id) % CANDIDATE_COLORS.length] : undefined
                  return (
                    <button
                      key={c.id}
                      onClick={() => toggleCandidate(c.id)}
                      className={`flex flex-col gap-0.5 px-3 py-1.5 rounded-xl text-left transition-all group ${
                        selected
                          ? 'ring-1 text-[#FFF7EE] shadow-md'
                          : 'text-[rgba(255,247,238,0.55)] hover:text-[rgba(255,247,238,0.80)] hover:bg-[rgba(255,255,255,0.05)]'
                      }`}
                      style={{
                        background: selected ? `${color}18` : 'rgba(58,44,110,0.30)',
                        border: selected ? `1px solid ${color}50` : '1px solid rgba(255,255,255,0.07)',
                      }}
                    >
                      <div className="flex items-center gap-2">
                        {selected ? (
                          <div className="w-4 h-4 rounded-full flex items-center justify-center text-[8px] font-bold shrink-0" style={{ backgroundColor: color, color: '#140F25' }}>
                            {selectedCandidateIds.indexOf(c.id) + 1}
                          </div>
                        ) : (
                          <Users className="w-3.5 h-3.5 shrink-0" />
                        )}
                        <span className="truncate max-w-[150px] text-[12px] font-medium">{c.display_name}</span>
                        {c.relevance_score !== null && (
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md ${selected ? '' : 'bg-[rgba(255,255,255,0.05)]'}`} style={{ color: selected ? color : '#94A3B8' }}>
                            {Math.round(c.relevance_score)}%
                          </span>
                        )}
                      </div>
                      {(c.email || c.stage) && (
                        <div className="flex items-center gap-2 text-[9px] text-[rgba(255,247,238,0.40)] pl-6">
                          {c.stage && <span className="uppercase tracking-wider">{c.stage}</span>}
                          {c.stage && c.email && <span>•</span>}
                          {c.email && <span className="truncate max-w-[120px]">{c.email}</span>}
                        </div>
                      )}
                    </button>
                  )
                })}
                {candidates.length === 0 && (
                  <p className="text-[11px] text-[rgba(255,247,238,0.3)] p-2">No candidates applied for this job yet.</p>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-1.5 shrink-0">
              <div className="h-8 hidden sm:block"></div>
              <LiquidButton
                onClick={handleCompare}
                disabled={loading || selectedCandidateIds.length < 2}
                className="text-[#140F25] font-semibold text-[13px] bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.25)] rounded-full disabled:opacity-50 px-6 py-2.5 shrink-0"
              >
                <GitCompareArrows className="w-4 h-4" />
                {loading ? 'Comparing...' : 'Compare'}
              </LiquidButton>
            </div>
          </div>

          {error && (
            <p className="mt-3 text-[12px] text-[#FB7185]">{error}</p>
          )}
        </div>

        {/* Results */}
        {result && (
          <>
            {/* Ranking Banner */}
            <div className="flex flex-wrap gap-3">
              {result.ranking.map((r, i) => {
                const color = CANDIDATE_COLORS[result.candidates.findIndex(c => c.candidate_id === r.candidate_id) % CANDIDATE_COLORS.length]
                return (
                  <div
                    key={r.candidate_id}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl flex-1 min-w-[200px]"
                    style={{ background: `${color}10`, border: `1px solid ${color}25` }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-[14px] font-bold shrink-0"
                      style={{ backgroundColor: `${color}20`, color }}
                    >
                      {i === 0 ? <Trophy className="w-4 h-4" /> : `#${r.rank}`}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-semibold text-[#FFF7EE] truncate">{r.candidate_name || `#${r.candidate_id}`}</p>
                      <p className="text-[11px]" style={{ color }}>{Math.round(r.relevance_score)}% relevance</p>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Main Comparison Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Radar Chart */}
              <div className="cq-card-elevated rounded-2xl p-6 flex flex-col items-center">
                <h3 className="text-[13px] font-bold text-[#FFF7EE] mb-1 self-start">Performance Radar</h3>
                <p className="text-[11px] text-[rgba(255,247,238,0.40)] mb-4 self-start">6-dimensional comparison across scoring signals.</p>
                <canvas ref={canvasRef} className="mb-4" />
                {/* Legend */}
                <div className="flex flex-wrap gap-3 justify-center">
                  {result.candidates.map((c, i) => (
                    <div key={c.candidate_id} className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CANDIDATE_COLORS[i % CANDIDATE_COLORS.length] }} />
                      <span className="text-[11px] text-[rgba(255,247,238,0.60)]">{getCandidateName(c)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skill Overlap */}
              <div className="cq-card-elevated rounded-2xl p-6">
                <h3 className="text-[13px] font-bold text-[#FFF7EE] mb-1">Skill Overlap Analysis</h3>
                <p className="text-[11px] text-[rgba(255,247,238,0.40)] mb-5">Shared vs. unique skills across selected candidates.</p>

                {/* Shared Skills */}
                {result.skill_overlap.shared_skills.length > 0 && (
                  <div className="mb-5">
                    <div className="flex items-center gap-2 mb-2.5">
                      <Layers className="w-3.5 h-3.5 text-[#4ADE80]" />
                      <span className="text-[11px] font-bold text-[#4ADE80] uppercase tracking-wider">Shared by All ({result.skill_overlap.shared_skills.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {result.skill_overlap.shared_skills.map(skill => (
                        <span key={skill} className="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-[rgba(74,222,128,0.08)] text-[rgba(74,222,128,0.80)] border border-[rgba(74,222,128,0.15)]">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Unique Skills Per Candidate */}
                {result.candidates.map((c, i) => {
                  const unique = result.skill_overlap.per_candidate[String(c.candidate_id)] || []
                  if (unique.length === 0) return null
                  const color = CANDIDATE_COLORS[i % CANDIDATE_COLORS.length]
                  return (
                    <div key={c.candidate_id} className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color }}>
                          Only {getCandidateName(c)} ({unique.length})
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {unique.slice(0, 12).map(skill => (
                          <span
                            key={skill}
                            className="px-2.5 py-1 rounded-lg text-[10px] font-medium"
                            style={{ background: `${color}10`, color: `${color}CC`, border: `1px solid ${color}25` }}
                          >
                            {skill}
                          </span>
                        ))}
                        {unique.length > 12 && (
                          <span className="px-2.5 py-1 rounded-lg text-[10px] text-[rgba(255,247,238,0.35)]">+{unique.length - 12} more</span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Detailed Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {result.candidates.map((c, i) => {
                const color = CANDIDATE_COLORS[i % CANDIDATE_COLORS.length]
                const rank = result.ranking.find(r => r.candidate_id === c.candidate_id)
                return (
                  <div
                    key={c.candidate_id}
                    className="cq-card-elevated rounded-2xl p-5 flex flex-col gap-4"
                    style={{ borderTop: `3px solid ${color}` }}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-bold shrink-0"
                          style={{ backgroundColor: `${color}20`, color }}
                        >
                          {(getCandidateName(c))[0].toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="text-[13px] font-semibold text-[#FFF7EE] truncate">{getCandidateName(c)}</p>
                          {c.predicted_domain && (
                            <p className="text-[10px] text-[#C084FC]">{c.predicted_domain}</p>
                          )}
                        </div>
                      </div>
                      {rank && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: `${color}15`, color }}>
                          #{rank.rank}
                        </span>
                      )}
                    </div>

                    {/* Scores */}
                    <div className="space-y-2.5">
                      <ScoreBar label="Relevance" value={c.relevance_score} color={color} />
                      <ScoreBar label="Required Cov." value={c.required_coverage} color="#60A5FA" />
                      <ScoreBar label="Preferred Cov." value={c.preferred_coverage} color="#C084FC" />
                      <ScoreBar label="Combined Match" value={c.combined_match} color="#4ADE80" />
                    </div>

                    {/* Skills Summary */}
                    <div className="flex items-center gap-3 text-[10px]">
                      <span className="flex items-center gap-1 text-[#4ADE80]">
                        <Check className="w-3 h-3" /> {c.matched_required.length} req
                      </span>
                      <span className="flex items-center gap-1 text-[#FB7185]">
                        <XIcon className="w-3 h-3" /> {c.missing_required.length} missing
                      </span>
                      <span className="flex items-center gap-1 text-[#C084FC]">
                        <Sparkles className="w-3 h-3" /> {c.skills.length} total
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* AI Summary */}
            {result.ai_summary && (
              <div className="cq-card-elevated rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-[#F6B98A]" />
                  <h3 className="text-[13px] font-bold text-[#FFF7EE]">AI Comparison Summary</h3>
                </div>
                <div className="text-[13px] text-[rgba(255,247,238,0.65)] leading-relaxed whitespace-pre-wrap">
                  {result.ai_summary}
                </div>
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {!result && !loading && (
          <div className="cq-card-elevated rounded-2xl p-12 text-center">
            <GitCompareArrows className="w-10 h-10 text-[rgba(255,247,238,0.20)] mx-auto mb-4" />
            <p className="text-[15px] text-[rgba(255,247,238,0.50)] mb-1">Select a job and 2+ candidates to compare</p>
            <p className="text-[12px] text-[rgba(255,247,238,0.30)]">You'll see radar charts, skill overlap, and AI-generated insights.</p>
          </div>
        )}
      </div>
    </PageShell>
  )
}

// --- Helper Component ---

function ScoreBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const score = value ?? 0
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-[10px] text-[rgba(255,247,238,0.50)]">{label}</span>
        <span className="text-[10px] font-bold" style={{ color }}>{Math.round(score)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, score)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
