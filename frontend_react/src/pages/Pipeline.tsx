import { useState, useEffect } from 'react'
import {
  Users, ArrowRight, Clock, TrendingUp, ChevronDown,
  Briefcase, User, GripVertical, History, BarChart3, Mail
} from 'lucide-react'
import {
  getPipelineForJob, movePipelineStage, getPipelineStats, getPipelineHistory,
  sendPipelineEmail, PIPELINE_STAGES, STAGE_CONFIG,
} from '../services/pipelineApi'
import type { PipelineEntry, PipelineStats, PipelineHistoryItem } from '../services/pipelineApi'
import { getJobs } from '../services/jobs'
import type { Job as JobFull } from '../services/jobs'
import { PageShell } from '../components/ui/PageShell'
import { LiquidButton } from '../components/ui/liquid-glass-button'

// Stages to show as columns (exclude rejected — shown as a separate row)
const KANBAN_COLUMNS = PIPELINE_STAGES.filter(s => s !== 'rejected')

export function Pipeline() {
  const [jobs, setJobs] = useState<JobFull[]>([])
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [entries, setEntries] = useState<PipelineEntry[]>([])
  const [stats, setStats] = useState<PipelineStats | null>(null)
  const [history, setHistory] = useState<PipelineHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showHistory, setShowHistory] = useState(false)
  const [movingEntry, setMovingEntry] = useState<number | null>(null)
  const [emailingEntry, setEmailingEntry] = useState<number | null>(null)

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    if (selectedJobId) {
      fetchPipelineData(selectedJobId)
    }
  }, [selectedJobId])

  const fetchJobs = async () => {
    try {
      const data = await getJobs()
      setJobs(data)
      if (data.length > 0) {
        setSelectedJobId(data[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch jobs', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchPipelineData = async (jobId: number) => {
    try {
      const [pipelineData, statsData, historyData] = await Promise.all([
        getPipelineForJob(jobId),
        getPipelineStats(jobId),
        getPipelineHistory(jobId, 20),
      ])
      setEntries(pipelineData)
      setStats(statsData)
      setHistory(historyData)
    } catch (err) {
      console.error('Failed to fetch pipeline data', err)
    }
  }

  const handleMoveStage = async (entryId: number, toStage: string) => {
    setMovingEntry(entryId)
    try {
      await movePipelineStage(entryId, toStage)
      if (selectedJobId) {
        await fetchPipelineData(selectedJobId)
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to move candidate.'
      alert(detail)
    } finally {
      setMovingEntry(null)
    }
  }

  const handleSendEmail = async (entryId: number) => {
    setEmailingEntry(entryId)
    try {
      const res = await sendPipelineEmail(entryId)
      alert(res.message || 'Email sent successfully!')
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to send email.'
      alert(detail)
    } finally {
      setEmailingEntry(null)
    }
  }

  const getEntriesForStage = (stage: string) =>
    entries.filter(e => e.stage === stage)

  const formatTimeAgo = (iso: string) => {
    const ms = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(ms / 60000)
    if (mins < 60) return `${mins}m ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours}h ago`
    return `${Math.floor(hours / 24)}d ago`
  }

  // Determine valid next stages for a given stage
  const getNextStages = (currentStage: string): string[] => {
    const transitions: Record<string, string[]> = {
      applied:     ['screened', 'rejected'],
      screened:    ['shortlisted', 'rejected'],
      shortlisted: ['interview', 'rejected'],
      interview:   ['offer', 'shortlisted', 'rejected'],
      offer:       ['hired', 'rejected'],
      hired:       [],
      rejected:    ['applied'],
    }
    return transitions[currentStage] || []
  }


  if (loading) {
    return (
      <PageShell title="Hiring Pipeline" subtitle="Loading pipeline data...">
        <div className="p-12 flex items-center justify-center text-[rgba(255,247,238,0.45)] text-sm">Loading...</div>
      </PageShell>
    )
  }

  if (jobs.length === 0) {
    return (
      <PageShell title="Hiring Pipeline" subtitle="Visualize and manage your candidate journey.">
        <div className="cq-card-elevated rounded-2xl p-12 text-center">
          <Briefcase className="w-10 h-10 text-[rgba(255,247,238,0.25)] mx-auto mb-4" />
          <p className="text-[15px] text-[rgba(255,247,238,0.55)]">No jobs found. Create a job first to start building your pipeline.</p>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell
      title="Hiring Pipeline"
      subtitle="Drag candidates through stages. Every move is tracked and audited."
      action={
        <div className="flex items-center gap-3">
          <LiquidButton
            onClick={() => setShowHistory(!showHistory)}
            className="px-3 py-2 bg-[rgba(58,44,110,0.50)] border border-[rgba(255,255,255,0.10)] rounded-full text-[12px] font-medium text-[rgba(255,247,238,0.65)] flex items-center gap-2"
          >
            <History className="w-3.5 h-3.5" />
            {showHistory ? 'Hide History' : 'Activity Log'}
          </LiquidButton>
        </div>
      }
    >
      <div className="flex flex-col gap-6">

        {/* Job Selector + Stats Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          {/* Job Dropdown */}
          <div className="relative">
            <select
              value={selectedJobId ?? ''}
              onChange={(e) => setSelectedJobId(Number(e.target.value))}
              className="appearance-none pl-4 pr-10 py-2.5 rounded-xl text-[13px] font-medium text-[#FBE6B8] outline-none cursor-pointer min-w-[220px]"
              style={{
                background: 'rgba(58,44,110,0.45)',
                border: '1px solid rgba(251,230,184,0.18)',
              }}
            >
              {jobs.map(job => (
                <option key={job.id} value={job.id} className="bg-[#1E163A] text-[#FBE6B8]">
                  {job.title}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[rgba(255,247,238,0.40)] pointer-events-none" />
          </div>

          {/* Quick Stats */}
          {stats && (
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[rgba(58,44,110,0.30)] border border-[rgba(255,255,255,0.06)]">
                <Users className="w-3.5 h-3.5 text-[#F6B98A]" />
                <span className="text-[11px] font-bold text-[#FFF7EE]">{stats.total_candidates}</span>
                <span className="text-[11px] text-[rgba(255,247,238,0.45)]">candidates</span>
              </div>
              {stats.conversion_rates.applied !== undefined && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[rgba(58,44,110,0.30)] border border-[rgba(255,255,255,0.06)]">
                  <TrendingUp className="w-3.5 h-3.5 text-[#4ADE80]" />
                  <span className="text-[11px] font-bold text-[#FFF7EE]">{stats.conversion_rates.applied}%</span>
                  <span className="text-[11px] text-[rgba(255,247,238,0.45)]">pass rate</span>
                </div>
              )}
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[rgba(58,44,110,0.30)] border border-[rgba(255,255,255,0.06)]">
                <BarChart3 className="w-3.5 h-3.5 text-[#C084FC]" />
                <span className="text-[11px] font-bold text-[#FFF7EE]">
                  {stats.stage_counts.hired || 0}
                </span>
                <span className="text-[11px] text-[rgba(255,247,238,0.45)]">hired</span>
              </div>
            </div>
          )}
        </div>

        {/* Kanban Board */}
        <div className="w-full overflow-x-auto pb-4 custom-scrollbar">
          <div className="flex gap-4 min-w-max">
            {KANBAN_COLUMNS.map(stage => {
              const config = STAGE_CONFIG[stage]
              const stageEntries = getEntriesForStage(stage)

              return (
                <div
                  key={stage}
                  className="w-[260px] shrink-0 flex flex-col rounded-2xl overflow-hidden"
                  style={{ background: 'rgba(20,15,37,0.50)', border: '1px solid rgba(255,255,255,0.06)' }}
                >
                  {/* Column Header */}
                  <div
                    className="px-4 py-3 flex items-center justify-between"
                    style={{ borderBottom: `2px solid ${config.color}30` }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: config.color }}
                      />
                      <span className="text-[12px] font-bold text-[#FFF7EE] uppercase tracking-wider">
                        {config.label}
                      </span>
                    </div>
                    <span
                      className="text-[11px] font-bold px-2 py-0.5 rounded-full"
                      style={{ color: config.color, background: config.bgColor }}
                    >
                      {stageEntries.length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="flex-1 p-2.5 space-y-2 min-h-[120px] max-h-[500px] overflow-y-auto custom-scrollbar">
                    {stageEntries.length === 0 && (
                      <div className="flex items-center justify-center h-20 text-[11px] text-[rgba(255,247,238,0.25)] italic">
                        No candidates
                      </div>
                    )}
                    {stageEntries.map(entry => (
                      <div
                        key={entry.id}
                        className={`group rounded-xl p-3 transition-all duration-150 hover:border-[rgba(246,185,138,0.20)] ${
                          movingEntry === entry.id ? 'opacity-50 scale-95' : ''
                        }`}
                        style={{
                          background: 'rgba(58,44,110,0.35)',
                          border: '1px solid rgba(255,255,255,0.07)',
                        }}
                      >
                        {/* Candidate Info */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#C4749B] to-[#F6B98A] flex items-center justify-center text-[10px] font-bold text-[#140F25] shrink-0">
                              {(entry.candidate_name || 'C')[0].toUpperCase()}
                            </div>
                            <div className="min-w-0">
                              <p className="text-[12px] font-semibold text-[#FFF7EE] truncate">
                                {entry.candidate_name || `Candidate #${entry.candidate_id}`}
                              </p>
                              {entry.candidate_email && (
                                <p className="text-[10px] text-[rgba(255,247,238,0.40)] truncate">
                                  {entry.candidate_email}
                                </p>
                              )}
                            </div>
                          </div>
                          <GripVertical className="w-3.5 h-3.5 text-[rgba(255,247,238,0.15)] group-hover:text-[rgba(255,247,238,0.35)] shrink-0 mt-0.5" />
                        </div>

                        {/* Score + Domain */}
                        <div className="flex items-center gap-2 mb-2.5">
                          {entry.relevance_score !== null && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[rgba(246,185,138,0.12)] text-[#F6B98A]">
                              {Math.round(entry.relevance_score)}% match
                            </span>
                          )}
                          {entry.predicted_domain && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[rgba(192,132,252,0.10)] text-[#C084FC]">
                              {entry.predicted_domain}
                            </span>
                          )}
                        </div>

                        {/* Time in stage */}
                        <div className="flex items-center gap-1 mb-2.5">
                          <Clock className="w-3 h-3 text-[rgba(255,247,238,0.30)]" />
                          <span className="text-[10px] text-[rgba(255,247,238,0.35)]">
                            {formatTimeAgo(entry.stage_changed_at)}
                          </span>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-wrap gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          {getNextStages(stage).length > 0 && getNextStages(stage).map(nextStage => {
                            const nextConfig = STAGE_CONFIG[nextStage]
                            return (
                              <button
                                key={nextStage}
                                onClick={() => handleMoveStage(entry.id, nextStage)}
                                disabled={movingEntry === entry.id || emailingEntry === entry.id}
                                className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-all hover:brightness-110 disabled:opacity-50"
                                style={{
                                  color: nextConfig.color,
                                  background: nextConfig.bgColor,
                                  border: `1px solid ${nextConfig.color}25`,
                                }}
                              >
                                <ArrowRight className="w-2.5 h-2.5" />
                                {nextConfig.label}
                              </button>
                            )
                          })}
                          
                          {/* Dedicated Email Button for Hired */}
                          {stage === 'hired' && (
                            <button
                                onClick={() => handleSendEmail(entry.id)}
                                disabled={emailingEntry === entry.id}
                                className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-all hover:brightness-110 disabled:opacity-50"
                                style={{
                                  color: '#38BDF8',
                                  background: 'rgba(56,189,248,0.12)',
                                  border: `1px solid rgba(56,189,248,0.25)`,
                                }}
                              >
                                <Mail className="w-2.5 h-2.5" />
                                {emailingEntry === entry.id ? 'Sending...' : 'Send Welcome Email'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Rejected Row */}
        {getEntriesForStage('rejected').length > 0 && (
          <div className="cq-card-elevated rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2.5 h-2.5 rounded-full bg-[#FB7185]" />
              <h3 className="text-[12px] font-bold text-[#FB7185] uppercase tracking-wider">
                Rejected ({getEntriesForStage('rejected').length})
              </h3>
            </div>
            <div className="flex flex-wrap gap-3">
              {getEntriesForStage('rejected').map(entry => (
                <div
                  key={entry.id}
                  className="group flex items-center gap-3 px-3 py-2 rounded-full bg-[rgba(251,113,133,0.06)] border border-[rgba(251,113,133,0.12)]"
                >
                  <div className="w-6 h-6 rounded-md bg-[rgba(251,113,133,0.15)] flex items-center justify-center text-[9px] font-bold text-[#FB7185]">
                    {(entry.candidate_name || 'C')[0].toUpperCase()}
                  </div>
                  <span className="text-[12px] text-[rgba(255,247,238,0.60)]">
                    {entry.candidate_name || `Candidate #${entry.candidate_id}`}
                  </span>
                  <button
                    onClick={() => handleMoveStage(entry.id, 'applied')}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-[rgba(148,163,184,0.10)] text-[#94A3B8] hover:text-[#FFF7EE] transition-colors opacity-0 group-hover:opacity-100"
                  >
                    Re-open
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Activity History Panel */}
        {showHistory && history.length > 0 && (
          <div className="cq-card-elevated rounded-2xl p-5">
            <h3 className="text-[13px] font-bold text-[#FFF7EE] mb-4 flex items-center gap-2">
              <History className="w-4 h-4 text-[#F6B98A]" />
              Recent Pipeline Activity
            </h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
              {history.map(item => (
                <div key={item.id} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-[rgba(58,44,110,0.20)]">
                  <User className="w-3.5 h-3.5 text-[rgba(255,247,238,0.35)] shrink-0" />
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    <span className="text-[12px] font-medium text-[#FFF7EE] truncate">
                      {item.candidate_name || `#${item.candidate_id}`}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                      style={{
                        color: STAGE_CONFIG[item.from_stage]?.color || '#94A3B8',
                        background: STAGE_CONFIG[item.from_stage]?.bgColor || 'rgba(148,163,184,0.12)',
                      }}
                    >
                      {STAGE_CONFIG[item.from_stage]?.label || item.from_stage}
                    </span>
                    <ArrowRight className="w-3 h-3 text-[rgba(255,247,238,0.30)] shrink-0" />
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                      style={{
                        color: STAGE_CONFIG[item.to_stage]?.color || '#94A3B8',
                        background: STAGE_CONFIG[item.to_stage]?.bgColor || 'rgba(148,163,184,0.12)',
                      }}
                    >
                      {STAGE_CONFIG[item.to_stage]?.label || item.to_stage}
                    </span>
                  </div>
                  <span className="text-[10px] text-[rgba(255,247,238,0.30)] shrink-0">
                    {formatTimeAgo(item.transitioned_at)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </PageShell>
  )
}
