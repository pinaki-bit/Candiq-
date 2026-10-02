import { useState, useEffect } from 'react'
import { Activity, Users, FileText, Clock, AlertTriangle, CheckCircle } from 'lucide-react'
import { getAnalyticsSummary, getAuditLogs, getModelVersions } from '../services/analyticsApi'
import type { AnalyticsSummary, AuditEvent, ModelVersion } from '../services/analyticsApi'
import { PageShell } from '../components/ui/PageShell'

export function AdminAnalytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([])
  const [activeModel, setActiveModel] = useState<ModelVersion | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumData, logsData, modelsData] = await Promise.all([
          getAnalyticsSummary(),
          getAuditLogs(10),
          getModelVersions()
        ])
        setSummary(sumData)
        setAuditLogs(logsData.events)
        const active = modelsData.find(m => m.is_active)
        setActiveModel(active || modelsData[0] || null)
      } catch (err) {
        console.error("Failed to fetch analytics data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <PageShell title="Intelligence Telemetry" subtitle="Real-time system health, ML model performance, and security audit trail.">
        <div className="p-12 flex items-center justify-center text-[rgba(255,247,238,0.45)] text-sm">Loading real-time analytics...</div>
      </PageShell>
    )
  }

  const formatTimeAgo = (isoDate: string) => {
    if (!isoDate) return 'Unknown'
    const ms = Date.now() - new Date(isoDate).getTime()
    const mins = Math.floor(ms / 60000)
    if (mins < 60) return `${mins} mins ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} hours ago`
    return `${Math.floor(hours / 24)} days ago`
  }

  return (
    <PageShell
      title="Intelligence Telemetry"
      subtitle="Real-time system health, ML model performance, and security audit trail."
    >
      <div className="w-full flex flex-col gap-6">
        {/* Top Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Total Resumes', value: summary?.total_resumes || 0, icon: FileText, change: `${summary?.processing_rate_pct || 0}% processed`, color: 'text-[#F6B98A]' },
            { label: 'Total Candidates', value: summary?.total_candidates || 0, icon: Users, change: 'In database', color: 'text-[#C4749B]' },
            { label: 'Active Jobs', value: summary?.total_active_jobs || 0, icon: Activity, change: 'Open positions', color: 'text-emerald-400' },
            { label: 'Pending Reviews', value: summary?.pending_reviews || 0, icon: Clock, change: 'Needs attention', color: 'text-amber-400' }
          ].map(metric => (
            <div key={metric.label} className="cq-stat-card group">
              <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-100 transition-opacity">
                <metric.icon className={`w-12 h-12 ${metric.color}`} />
              </div>
              <p className="cq-label mb-2 block">{metric.label}</p>
              <p className="text-3xl font-bold text-[#FFF7EE] mb-1">{metric.value}</p>
              <p className={`text-xs ${metric.color} relative z-10 font-medium`}>
                {metric.change}
              </p>
            </div>
          ))}
        </div>

        {/* 2-Column Dashboard Grid */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* ML Model Health (6/12 Cols) */}
          <div className="lg:col-span-6 w-full cq-card-elevated rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#FFF7EE] mb-5 flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#F6B98A]" />
                ML Model Telemetry
              </h3>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2 font-medium">
                    <span className="text-[rgba(255,247,238,0.65)]">Classification Accuracy (Test)</span>
                    <span className="text-emerald-400 font-bold">{activeModel ? (activeModel.test_accuracy * 100).toFixed(1) : 'N/A'}%</span>
                  </div>
                  <div className="cq-progress">
                    <div className="cq-progress-fill" style={{ width: activeModel ? `${activeModel.test_accuracy * 100}%` : '0%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2 font-medium">
                    <span className="text-[rgba(255,247,238,0.65)]">Macro F1 Score</span>
                    <span className="text-[#F6B98A] font-bold">{activeModel ? (activeModel.test_macro_f1 * 100).toFixed(1) : 'N/A'}%</span>
                  </div>
                  <div className="cq-progress">
                    <div className="cq-progress-fill" style={{ width: activeModel ? `${activeModel.test_macro_f1 * 100}%` : '0%' }} />
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 p-4 rounded-xl bg-[rgba(74,222,128,0.06)] border border-[rgba(74,222,128,0.15)]">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-[#FBE6B8] font-semibold">Model Checksums Verified</p>
                  <p className="text-xs text-[#FBE6B8]/60 mt-1">Active Version: {activeModel?.version_tag || 'Unknown'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Audit Logs Preview (6/12 Cols) */}
          <div className="lg:col-span-6 w-full cq-card-elevated rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#FFF7EE] mb-5">Recent Security Events</h3>
              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
                {auditLogs.length > 0 ? auditLogs.map((log) => (
                  <div key={log.id} className="flex items-center gap-3 p-3 rounded-xl bg-[rgba(58,44,110,0.35)] border border-[rgba(255,255,255,0.06)] hover:border-[rgba(246,185,138,0.15)] transition-colors">
                    {log.outcome === 'failure' || log.event_type.includes('fail') || log.event_type.includes('denied') ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                    ) : (
                      <Activity className="w-5 h-5 text-[#F6B98A] shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] text-[#FFF7EE] font-medium truncate">{log.summary}</p>
                      <p className="text-[11px] text-[rgba(255,247,238,0.45)]">by {log.actor_email}</p>
                    </div>
                    <span className="text-[11px] text-[rgba(255,247,238,0.35)] whitespace-nowrap">{formatTimeAgo(log.occurred_at)}</span>
                  </div>
                )) : (
                  <p className="text-[#FBE6B8]/60 text-sm">No recent events found.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  )
}
