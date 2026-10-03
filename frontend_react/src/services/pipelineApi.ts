import { api } from '../lib/api'

// --- Types ---

export interface PipelineEntry {
  id: number
  public_id: string
  candidate_id: number
  candidate_name: string | null
  candidate_email: string | null
  job_id: number
  stage: string
  notes: string | null
  entered_at: string
  stage_changed_at: string
  relevance_score: number | null
  predicted_domain: string | null
}

export interface PipelineHistoryItem {
  id: number
  candidate_id: number
  candidate_name: string | null
  job_id: number
  from_stage: string
  to_stage: string
  notes: string | null
  transitioned_at: string
}

export interface PipelineStats {
  job_id: number
  job_title: string
  total_candidates: number
  stage_counts: Record<string, number>
  avg_time_in_stage_hours: Record<string, number>
  conversion_rates: Record<string, number>
}

export interface Job {
  id: number
  public_id: string
  title: string
  department: string | null
  domain: string | null
  is_active: boolean
}

// --- Pipeline Stages ---

export const PIPELINE_STAGES = [
  'applied',
  'screened',
  'shortlisted',
  'interview',
  'offer',
  'hired',
  'rejected',
] as const

export const STAGE_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  applied:     { label: 'Applied',     color: '#94A3B8', bgColor: 'rgba(148,163,184,0.12)' },
  screened:    { label: 'Screened',    color: '#60A5FA', bgColor: 'rgba(96,165,250,0.12)' },
  shortlisted: { label: 'Shortlisted', color: '#F6B98A', bgColor: 'rgba(246,185,138,0.12)' },
  interview:   { label: 'Interview',   color: '#C084FC', bgColor: 'rgba(192,132,252,0.12)' },
  offer:       { label: 'Offer',       color: '#4ADE80', bgColor: 'rgba(74,222,128,0.12)' },
  hired:       { label: 'Hired',       color: '#34D399', bgColor: 'rgba(52,211,153,0.15)' },
  rejected:    { label: 'Rejected',    color: '#FB7185', bgColor: 'rgba(251,113,133,0.12)' },
}

// --- API Calls ---

export async function getPipelineForJob(jobId: number): Promise<PipelineEntry[]> {
  const res = await api.get(`/pipeline/${jobId}`)
  return res.data
}

export async function addToPipeline(jobId: number, candidateId: number, stage = 'applied', notes?: string): Promise<PipelineEntry> {
  const res = await api.post(`/pipeline/${jobId}/add`, {
    candidate_id: candidateId,
    stage,
    notes,
  })
  return res.data
}

export async function movePipelineStage(entryId: number, toStage: string, notes?: string): Promise<PipelineEntry> {
  const res = await api.patch(`/pipeline/${entryId}/move`, {
    to_stage: toStage,
    notes,
  })
  return res.data
}

export async function getPipelineHistory(jobId: number, limit = 50): Promise<PipelineHistoryItem[]> {
  const res = await api.get(`/pipeline/${jobId}/history`, { params: { limit } })
  return res.data
}

export async function getPipelineStats(jobId: number): Promise<PipelineStats> {
  const res = await api.get(`/pipeline/stats/${jobId}`)
  return res.data
}

export async function sendPipelineEmail(entryId: number): Promise<{ message: string }> {
  const res = await api.post(`/pipeline/${entryId}/send-email`)
  return res.data
}

export async function getJobsList(): Promise<Job[]> {
  const res = await api.get('/jobs/')
  return res.data
}
