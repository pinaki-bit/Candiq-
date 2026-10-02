import { useState, useEffect } from 'react'
import { Search, Filter, Briefcase, MapPin, Award, CheckCircle } from 'lucide-react'
import { getResumes, getResumeDetail } from '../services/screening'
import type { Resume, ResumeDetail } from '../services/screening'
import { PageShell } from '../components/ui/PageShell'
import { LiquidButton } from '../components/ui/liquid-glass-button'
import { getJobs } from '../services/jobs'
import type { Job } from '../services/jobs'
import { api } from '../lib/api'

export function TalentExplorer() {
  const [searchTerm, setSearchTerm] = useState('')
  const [resumes, setResumes] = useState<Resume[]>([])
  const [selectedResume, setSelectedResume] = useState<ResumeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  
  const [jobs, setJobs] = useState<Job[]>([])
  const [assignJobId, setAssignJobId] = useState<number | null>(null)
  const [assigning, setAssigning] = useState(false)

  useEffect(() => {
    fetchResumes()
    getJobs().then(setJobs).catch(console.error)
  }, [])

  const fetchResumes = async () => {
    try {
      const data = await getResumes()
      setResumes(data)
      if (data.length > 0) {
        handleSelectResume(data[0].public_id)
      }
    } catch (error) {
      console.error('Failed to fetch resumes', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectResume = async (id: string) => {
    try {
      const detail = await getResumeDetail(id)
      setSelectedResume(detail)
    } catch (error) {
      console.error('Failed to fetch resume detail', error)
    }
  }

  const handleAssignPipeline = async () => {
    if (!selectedResume || !selectedResume.candidate_id || !assignJobId) return
    setAssigning(true)
    try {
      await api.post(`/pipeline/${assignJobId}/add`, {
        candidate_id: selectedResume.candidate_id,
        stage: 'applied'
      })
      alert('Candidate successfully added to pipeline!')
    } catch (error: any) {
      console.error('Failed to assign candidate', error)
      alert(error.response?.data?.detail || 'Failed to assign candidate to pipeline.')
    } finally {
      setAssigning(false)
    }
  }

  // Filter based on candidate name or skills (if available in summary list)
  const filteredResumes = resumes.filter(r => 
    r.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const actionButton = (
    <LiquidButton className="px-4 py-2.5 bg-[#3A2C6E]/60 border border-[#F6B98A]/25 rounded-full text-sm font-semibold text-[#FBE6B8] flex items-center gap-2 shadow-md">
      <Filter className="w-4 h-4 text-[#F6B98A]" />
      Advanced Filters
    </LiquidButton>
  )

  return (
    <PageShell
      title="Talent Intelligence Search"
      subtitle="Discover and analyze candidate profiles with AI matching."
      action={actionButton}
    >
      <div className="w-full flex flex-col gap-6">
        {/* Search Bar */}
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-[#F6B98A]/70" />
          </div>
          <input
            type="text"
            className="w-full pl-11 pr-4 py-3.5 bg-[#3A2C6E]/40 border border-[#F6B98A]/20 rounded-xl text-[#FBE6B8] placeholder-[#FBE6B8]/45 focus:outline-none focus:ring-2 focus:ring-[#F6B98A]/40 focus:border-transparent transition-all shadow-lg shadow-black/20 text-sm sm:text-base"
            placeholder="Search by filename or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Responsive Content Grid */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Candidate List (4/12 Cols) */}
          <div className="lg:col-span-4 w-full flex flex-col gap-3 max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
            {loading ? (
               <div className="text-[#FBE6B8]/60 p-4">Loading candidates...</div>
            ) : filteredResumes.length === 0 ? (
               <div className="text-[#FBE6B8]/60 p-4">No candidates found. Upload a resume first.</div>
            ) : (
              filteredResumes.map((resume) => (
                <div 
                  key={resume.public_id} 
                  onClick={() => handleSelectResume(resume.public_id)}
                  className={`glass-card rounded-xl p-4 cursor-pointer border relative overflow-hidden group transition-all ${selectedResume?.public_id === resume.public_id ? 'border-[#F6B98A] bg-[#C4749B]/25 shadow-[0_0_20px_rgba(246,185,138,0.2)]' : 'border-[#F6B98A]/15 bg-[#3A2C6E]/40 hover:bg-[#C4749B]/15'}`}
                >
                  <div className="absolute top-0 right-0 p-3">
                     <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#181130]/80 border border-[#F6B98A]/30 shadow-[0_0_10px_rgba(246,185,138,0.25)]">
                        <CheckCircle className="w-3.5 h-3.5 text-[#F6B98A]" />
                     </div>
                  </div>
                  <h3 className="text-base font-semibold text-[#FBE6B8] mb-1 truncate pr-10">{resume.original_filename}</h3>
                  <p className="text-xs font-semibold text-[#F6B98A] mb-1.5">Status: {resume.status}</p>
                  <p className="text-[11px] text-[#FBE6B8]/60">Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}</p>
                </div>
              ))
            )}
          </div>

          {/* Candidate Intelligence Detail (8/12 Cols) */}
          <div className="lg:col-span-8 w-full glass-card rounded-2xl flex flex-col border border-[#F6B98A]/15 shadow-2xl overflow-hidden min-h-[500px]">
            {selectedResume ? (
              <>
                {/* Header */}
                <div className="p-6 sm:p-8 border-b border-[#F6B98A]/15 bg-gradient-to-b from-[#3A2C6E]/60 to-[#281B4B]/40">
                  <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                    <div>
                      <h2 className="text-xl sm:text-2xl font-bold text-[#FBE6B8] mb-1">{selectedResume.original_filename}</h2>
                      <p className="text-[#F6B98A] text-base font-medium">{selectedResume.predicted_domain || 'Domain Pending'}</p>
                    </div>
                    <div className="sm:text-right flex flex-col items-end">
                      <div className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#C4749B] to-[#F6B98A]">
                        {selectedResume.status}
                      </div>
                      <p className="text-xs text-[#FBE6B8]/60 uppercase tracking-wider mt-1 mb-4">Status</p>
                      
                      {/* Pipeline Assignment */}
                      {selectedResume.candidate_id && (
                        <div className="flex items-center gap-2">
                          <select
                            value={assignJobId || ''}
                            onChange={(e) => setAssignJobId(Number(e.target.value))}
                            className="appearance-none pl-3 pr-8 py-1.5 rounded-lg text-[12px] font-medium text-[#FBE6B8] outline-none cursor-pointer border border-[rgba(251,230,184,0.18)] bg-[rgba(58,44,110,0.45)]"
                          >
                            <option value="">Select Job...</option>
                            {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
                          </select>
                          <LiquidButton
                            onClick={handleAssignPipeline}
                            disabled={!assignJobId || assigning}
                            className="px-3 py-1.5 text-[12px] rounded-full bg-gradient-to-r from-[#F6B98A] to-[#C4749B] text-[#140F25] font-semibold disabled:opacity-50"
                          >
                            {assigning ? 'Adding...' : 'Add to Pipeline'}
                          </LiquidButton>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 text-xs sm:text-sm text-[#FBE6B8]/80">
                    <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-[#F6B98A]" />
                        Confidence: {selectedResume.prediction_confidence || 'N/A'}
                    </div>
                    <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-[#F6B98A]" />
                        Size: {(selectedResume.file_size_bytes / 1024).toFixed(1)} KB
                    </div>
                  </div>
                </div>

                <div className="p-6 sm:p-8 flex-1 space-y-6">
                  {/* Skill Heatmap */}
                  <div>
                    <h3 className="text-lg font-semibold text-[#FBE6B8] mb-4 flex items-center gap-2">
                      <Award className="w-5 h-5 text-[#F6B98A]" />
                      Extracted Skills Intelligence
                    </h3>
                    {selectedResume.extracted_skills && selectedResume.extracted_skills.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {selectedResume.extracted_skills.map(skill => (
                          <div key={skill.id} className="bg-[#3A2C6E]/40 p-4 rounded-xl border border-[#F6B98A]/15">
                            <div className="flex justify-between mb-2">
                              <span className="text-sm font-medium text-[#FBE6B8]">{skill.canonical_name}</span>
                              <span className="text-sm font-bold text-[#F6B98A]">{skill.frequency} mentions</span>
                            </div>
                            <div className="text-xs text-[#FBE6B8]/60 mb-2 truncate">
                              {skill.category || 'Uncategorized'} - {skill.domain || 'Generic'}
                            </div>
                            <div className="w-full bg-[#181130]/80 rounded-full h-1.5 overflow-hidden border border-[#F6B98A]/10">
                              <div className="h-1.5 rounded-full bg-gradient-to-r from-[#C4749B] to-[#F6B98A]" style={{ width: `${Math.min(100, skill.frequency * 20)}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[#FBE6B8]/60 text-sm">No skills were extracted or extraction is still pending.</p>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="p-8 flex items-center justify-center h-full text-[#FBE6B8]/50 min-h-[300px]">
                Select a candidate from the list to view intelligence details.
              </div>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  )
}

