import { api } from '../lib/api'

export interface CandidateSkillProfile {
  skill_name: string
  domain: string | null
  category: string | null
  frequency: number
}

export interface CandidateCompareProfile {
  candidate_id: number
  candidate_name: string | null
  candidate_email: string | null
  relevance_score: number | null
  required_coverage: number | null
  preferred_coverage: number | null
  combined_match: number | null
  predicted_domain: string | null
  prediction_confidence: string | null
  skills: CandidateSkillProfile[]
  matched_required: string[]
  missing_required: string[]
  matched_preferred: string[]
  score_breakdown: Record<string, number> | null
  resume_filename: string | null
  resume_text_length: number | null
}

export interface SkillOverlap {
  shared_skills: string[]
  per_candidate: Record<string, string[]>
}

export interface RadarDimension {
  dimension: string
  values: Record<string, number>
}

export interface CompareResponse {
  job_id: number
  job_title: string
  candidates: CandidateCompareProfile[]
  skill_overlap: SkillOverlap
  radar_chart: RadarDimension[]
  ranking: { candidate_id: number; candidate_name: string | null; relevance_score: number; rank: number }[]
  ai_summary: string | null
}

export async function compareCandidates(jobId: number, candidateIds: number[]): Promise<CompareResponse> {
  const res = await api.post(`/compare/${jobId}`, { candidate_ids: candidateIds })
  return res.data
}
