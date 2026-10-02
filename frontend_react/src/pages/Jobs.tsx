import React, { useEffect, useState } from 'react'
import { getJobs, createJob, deleteJob } from '../services/jobs'
import type { Job } from '../services/jobs'
import { Briefcase, Plus, Trash2, MapPin, Tag } from 'lucide-react'
import { PageShell } from '../components/ui/PageShell'
import { LiquidButton } from '../components/ui/liquid-glass-button'

export function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // Form State
  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('')
  const [description, setDescription] = useState('')
  const [domain, setDomain] = useState('')
  
  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const data = await getJobs()
      setJobs(data)
    } catch (error) {
      console.error('Failed to fetch jobs', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createJob({
        title,
        department,
        description,
        domain,
        requirements: [] // simplify for now
      })
      setShowForm(false)
      setTitle('')
      setDepartment('')
      setDescription('')
      setDomain('')
      fetchJobs()
    } catch (error) {
      console.error('Failed to create job', error)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this job?')) return
    try {
      await deleteJob(id)
      fetchJobs()
    } catch (error) {
      console.error('Failed to delete job', error)
    }
  }

  const actionButton = (
    <LiquidButton 
      onClick={() => setShowForm(!showForm)}
      className="text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.30)] rounded-xl"
    >
      <Plus className="w-4 h-4 text-[#181130]" />
      {showForm ? 'Cancel' : 'New Job'}
    </LiquidButton>
  )

  return (
    <PageShell
      title="Jobs Intelligence"
      subtitle="Create and manage job postings, define requirements, and match candidates."
      action={actionButton}
    >
      <div className="w-full flex flex-col gap-6">
        {showForm && (
          <div className="glass-card p-6 rounded-2xl border border-[#F6B98A]/25 animate-in fade-in duration-300">
            <h2 className="text-lg font-bold text-[#FFF7EE] mb-4">Create New Job Posting</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="cq-label mb-1.5 block">Job Title</label>
                  <input required value={title} onChange={e => setTitle(e.target.value)} className="cq-input" placeholder="e.g. Senior ML Engineer" />
                </div>
                <div>
                  <label className="cq-label mb-1.5 block">Department</label>
                  <input required value={department} onChange={e => setDepartment(e.target.value)} className="cq-input" placeholder="e.g. Engineering" />
                </div>
                <div>
                  <label className="cq-label mb-1.5 block">Domain</label>
                  <input value={domain} onChange={e => setDomain(e.target.value)} className="cq-input" placeholder="e.g. AI / NLP" />
                </div>
              </div>
              <div>
                <label className="cq-label mb-1.5 block">Description</label>
                <textarea required value={description} onChange={e => setDescription(e.target.value)} rows={4} className="cq-textarea" placeholder="Detailed job description and requirements..." />
              </div>
              <LiquidButton type="submit" className="text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.30)] rounded-xl">Save Job</LiquidButton>
            </form>
          </div>
        )}

        {loading ? (
          <div className="p-12 flex items-center justify-center text-[rgba(255,247,238,0.50)] text-sm">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="p-12 flex flex-col items-center justify-center cq-card rounded-2xl min-h-[300px]">
            <Briefcase className="w-12 h-12 text-[#F6B98A]/70 mb-4" />
            <h3 className="text-xl font-semibold text-[#FBE6B8]">No Jobs Found</h3>
            <p className="text-[#FBE6B8]/60 mt-2 text-center">Create your first job posting to start matching candidates.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {jobs.map(job => (
              <div key={job.public_id} className="cq-card-intelligence rounded-2xl p-6 relative group flex flex-col justify-between">
                <div>
                  <LiquidButton 
                    onClick={() => handleDelete(job.public_id)}
                    variant="destructive"
                    size="icon"
                    className="absolute top-4 right-4 p-2 opacity-80 sm:opacity-0 sm:group-hover:opacity-100 transition-all h-8 w-8"
                  >
                    <Trash2 className="w-4 h-4" />
                  </LiquidButton>
                  
                  <h3 className="text-base font-bold text-[#FFF7EE] mb-2 pr-8">{job.title}</h3>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="cq-badge cq-badge-plum flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-[#F6B98A]" />
                      {job.department}
                    </span>
                    {job.domain && (
                      <span className="cq-badge cq-badge-peach flex items-center gap-1">
                        <Tag className="w-3 h-3 text-[#F6B98A]" />
                        {job.domain}
                      </span>
                    )}
                  </div>
                  <p className="text-[13px] text-[rgba(255,247,238,0.55)] line-clamp-3 mb-4">{job.description}</p>
                </div>
                
                <div className="pt-4 border-t border-[#F6B98A]/15">
                  <div className="text-[11px] font-semibold text-[rgba(255,247,238,0.50)]">Requirements: {job.requirements?.length || 0} skills</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  )
}

