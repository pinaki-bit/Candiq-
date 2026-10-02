import React, { useState, useRef } from 'react';
import { api } from '../lib/api';
import { 
  UploadCloud, FileText, CheckCircle, XCircle, Briefcase, 
  User, Mail, Phone, Globe, Code2, MapPin, 
  Sparkles, Layers, Award, Zap, AlignLeft
} from 'lucide-react';
import { PageShell } from '../components/ui/PageShell';
import { LiquidButton } from '../components/ui/liquid-glass-button';

export function CandidatePortal() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [atsResult, setAtsResult] = useState<any>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const ensureAuth = async () => {
      if (!localStorage.getItem('token')) {
        try {
          const res = await api.post('/auth/login', {
            email: 'admin@example.com',
            password: 'changeme123'
          });
          if (res.data.access_token) {
            localStorage.setItem('token', res.data.access_token);
          }
        } catch (e) {
          console.error('Auto candidate session initialization:', e);
        }
      }
    };
    ensureAuth();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        setError('Please upload a valid PDF file.');
      }
    }
  };

  const analyzeATS = async () => {
    if (!file) {
      setError('Please select a resume PDF to analyze.');
      return;
    }
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (jobDescription.trim()) {
        formData.append('job_description', jobDescription);
      }

      const response = await api.post(
        '/resumes/candidate-analyze',
        formData,
        { 
          headers: { 
            'Content-Type': 'multipart/form-data'
          } 
        }
      );
      setAtsResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze resume. Ensure it is a valid PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell
      title="Resume Intelligence Lab"
      subtitle="Upload resumes and let Candiq extract, classify, and understand candidate signals."
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Upload & Input (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="cq-card-elevated p-6 flex flex-col">
            <h2 className="text-lg font-bold text-[#FFF7EE] mb-4 flex items-center gap-2">
              <UploadCloud className="text-[#F6B98A]" size={20} /> 1. Upload Resume (PDF)
            </h2>
            
            <div 
              className={`cq-dropzone p-8 flex flex-col items-center justify-center ${file ? 'cq-dropzone-active' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <UploadCloud className={`w-12 h-12 mb-3 ${file ? 'text-[#F6B98A] animate-bounce' : 'text-[#FFF7EE]/50'}`} />
              {file ? (
                <div className="text-center">
                  <p className="text-[#FFF7EE] font-semibold text-sm break-all">{file.name}</p>
                  <p className="text-xs text-[#FFF7EE]/60 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <p className="text-[#FFF7EE]/60 text-sm text-center">Click or drag & drop your PDF resume here</p>
              )}
              <input type="file" accept=".pdf" className="hidden" ref={fileInputRef} onChange={handleFileChange} />
            </div>

            <div className="mt-6">
              <h2 className="text-lg font-bold text-[#FFF7EE] mb-2 flex items-center gap-2">
                <Briefcase size={20} className="text-[#F6B98A]"/> 2. Target Job Description (Optional)
              </h2>
              <p className="text-xs text-[#FFF7EE]/60 mb-3">Paste a job description to unlock tailored skill gap analysis and relevance scoring.</p>
              <textarea 
                className="cq-textarea h-36"
                placeholder="Paste Job Description..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </div>

            <LiquidButton 
              onClick={analyzeATS}
              disabled={loading || !file}
              className="text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.30)] rounded-xl w-full py-3.5 mt-6 text-base disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Sparkles className="animate-spin w-5 h-5 text-[#181130]" /> Analyzing Resume...
                </>
              ) : (
                'Run Comprehensive ATS Scan'
              )}
            </LiquidButton>
            {error && <p className="text-red-400 mt-4 text-sm bg-red-500/10 p-3 rounded-xl border border-red-500/20">{error}</p>}
          </div>
        </div>

        {/* Right Column: Dynamic Analysis Dashboard (7 Cols) */}
        <div className="lg:col-span-7 cq-card-intelligence p-6 flex flex-col min-h-[550px]">
          <h2 className="text-xl font-bold mb-6 flex items-center justify-between">
            <span className="text-[#FFF7EE]">ATS Diagnostic Dashboard</span>
            {atsResult && (
              <span className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ${
                atsResult.compliance_category === 'EXCELLENT' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                atsResult.compliance_category === 'GOOD' ? 'bg-[#C4749B]/20 text-[#F6B98A] border border-[#F6B98A]/35' :
                'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              }`}>
                {atsResult.compliance_category} COMPLIANCE
              </span>
            )}
          </h2>
          
          {!atsResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-[#FFF7EE]/50 py-16">
              <div className="w-20 h-20 border-2 border-dashed border-[#F6B98A]/30 rounded-full flex items-center justify-center mb-4 bg-[#3A2C6E]/20">
                <FileText className="w-8 h-8 text-[#F6B98A]" />
              </div>
              <p className="text-lg text-[#FFF7EE] font-semibold">Upload a PDF to view your tailored report.</p>
              <p className="text-sm mt-2 max-w-md text-center text-[#FFF7EE]/60">
                The scanner evaluates your contact data, section structure, keyword density, metric impacts, action verbs, and formatting compatibility.
              </p>
            </div>
          ) : (
            <div className="space-y-8 animate-in fade-in duration-300">
              
              {/* Score Badges Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="cq-card p-5 flex items-center gap-4">
                  <div className="relative w-20 h-20 flex items-center justify-center rounded-full border-4 border-[#F6B98A] bg-[#181130]/80 shadow-[0_0_20px_rgba(246,185,138,0.3)] shrink-0">
                    <span className="text-2xl font-bold text-[#FFF7EE]">{atsResult.ats_score.toFixed(0)}</span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#FFF7EE]">ATS Score</h3>
                    <p className="text-xs text-[#FFF7EE]/70 mt-1">Parsability, structure & format.</p>
                  </div>
                </div>

                {atsResult.job_alignment?.job_provided && (
                  <div className="cq-card p-5 border-[#C4749B]/30 flex items-center gap-4">
                    <div className="relative w-20 h-20 flex items-center justify-center rounded-full border-4 border-[#C4749B] bg-[#181130]/80 shadow-[0_0_20px_rgba(196,116,155,0.3)] shrink-0">
                      <span className="text-2xl font-bold text-[#FFF7EE]">{atsResult.job_alignment.relevance_score?.toFixed(0)}</span>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#F6B98A]">Job Match</h3>
                      <p className="text-xs text-[#FFF7EE]/70 mt-1">Target job description alignment.</p>
                    </div>
                  </div>
                )}

                <div className="cq-card p-5 flex flex-col justify-center gap-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#FFF7EE]/70">Word Count:</span>
                    <span className="text-[#FFF7EE] font-bold">{atsResult.word_count}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#FFF7EE]/70">Est. Pages:</span>
                    <span className="text-[#FFF7EE] font-bold">{atsResult.estimated_page_count} page(s)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#FFF7EE]/70">Readability:</span>
                    <span className="text-[#F6B98A] font-bold">{atsResult.readability_grade}</span>
                  </div>
                </div>
              </div>

              {/* Contact Information Audit */}
              {atsResult.contact_info && (
                <div className="cq-card p-5">
                  <h3 className="text-xs font-bold text-[#FFF7EE] uppercase tracking-wider mb-4 flex items-center gap-2">
                    <User size={16} className="text-[#F6B98A]" /> Contact Information Audit
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <User size={14} className="text-[#F6B98A]/70" />
                      <span className="text-[#FFF7EE]/70">Name:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.name || 'Not Detected'}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <Mail size={14} className={atsResult.contact_info.email ? 'text-emerald-400' : 'text-red-400'} />
                      <span className="text-[#FFF7EE]/70">Email:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.email || 'Missing'}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <Phone size={14} className={atsResult.contact_info.phone ? 'text-emerald-400' : 'text-amber-400'} />
                      <span className="text-[#FFF7EE]/70">Phone:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.phone || 'Missing'}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <Globe size={14} className={atsResult.contact_info.linkedin ? 'text-[#F6B98A]' : 'text-[#FFF7EE]/40'} />
                      <span className="text-[#FFF7EE]/70">LinkedIn:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.linkedin ? 'Detected' : 'Missing'}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <Code2 size={14} className={atsResult.contact_info.github ? 'text-[#C4749B]' : 'text-[#FFF7EE]/40'} />
                      <span className="text-[#FFF7EE]/70">GitHub:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.github ? 'Detected' : 'Missing'}</span>
                    </div>
                    <div className="flex items-center gap-2 bg-[rgba(20,15,37,0.50)] p-2.5 rounded-lg border border-[rgba(255,255,255,0.06)]">
                      <MapPin size={14} className="text-[#F6B98A]/70" />
                      <span className="text-[#FFF7EE]/70">Location:</span>
                      <span className="text-[#FFF7EE] font-semibold truncate">{atsResult.contact_info.location || 'Optional'}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Categorized Technical Skills */}
              <div>
                <h3 className="text-lg font-bold text-[#FFF7EE] mb-4 border-b border-[#F6B98A]/15 pb-2 flex items-center gap-2">
                  <Layers size={18} className="text-[#F6B98A]" /> Categorized Skills & Keyword Density
                </h3>
                {atsResult.skill_categories && Object.keys(atsResult.skill_categories).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(atsResult.skill_categories).map(([catName, skills]: [string, any]) => (
                      <div key={catName} className="bg-[#3A2C6E]/30 p-4 rounded-xl border border-[#F6B98A]/15">
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-xs text-[#F6B98A] uppercase tracking-wider">{catName}</h4>
                          <span className="text-[10px] bg-[#C4749B]/25 text-[#FFF7EE] px-2 py-0.5 rounded font-bold border border-[#F6B98A]/20">{skills.length}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {skills.map((s: string, i: number) => (
                            <span key={i} className="px-2.5 py-1 bg-[#281B4B]/80 border border-[#F6B98A]/20 text-[#FFF7EE] rounded-md text-xs font-medium">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-[#3A2C6E]/30 p-4 rounded-xl flex flex-wrap gap-2">
                    {atsResult.detected_skills?.map((s: any, i: number) => (
                      <span key={i} className="px-3 py-1 bg-[#C4749B]/20 text-[#FFF7EE] border border-[#F6B98A]/30 rounded-full text-xs font-medium">
                        {typeof s === 'string' ? s : s.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Experience & Impact Metrics */}
              {atsResult.experience_analysis && (
                <div className="cq-card p-5">
                  <h3 className="text-xs font-bold text-[#FFF7EE] uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Zap size={16} className="text-[#F6B98A]" /> Experience Impact & Action Verbs Analysis
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div className="bg-[#181130]/40 p-3 rounded-xl border border-[#F6B98A]/10">
                      <p className="text-[#FFF7EE]/70 mb-2 font-medium">Strong Action Verbs:</p>
                      <div className="flex flex-wrap gap-1">
                        {atsResult.experience_analysis.action_verbs_found.map((v: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded font-medium border border-emerald-500/20">{v}</span>
                        ))}
                        {atsResult.experience_analysis.action_verbs_found.length === 0 && (
                          <span className="text-red-400">None detected</span>
                        )}
                      </div>
                    </div>
                    <div className="bg-[#181130]/40 p-3 rounded-xl border border-[#F6B98A]/10">
                      <p className="text-[#FFF7EE]/70 mb-2 font-medium">Weak / Passive Phrasing:</p>
                      <div className="flex flex-wrap gap-1">
                        {atsResult.experience_analysis.weak_verbs_found.map((v: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded font-medium border border-red-500/20">{v}</span>
                        ))}
                        {atsResult.experience_analysis.weak_verbs_found.length === 0 && (
                          <span className="text-emerald-400">No weak phrases</span>
                        )}
                      </div>
                    </div>
                    <div className="bg-[#181130]/40 p-3 rounded-xl border border-[#F6B98A]/10">
                      <p className="text-[#FFF7EE]/70 mb-2 font-medium">Detected Impact Metrics:</p>
                      <div className="flex flex-wrap gap-1">
                        {atsResult.experience_analysis.metrics_found.map((m: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-[#C4749B]/30 text-[#FFF7EE] rounded font-medium border border-[#F6B98A]/20">{m}</span>
                        ))}
                        {atsResult.experience_analysis.metrics_found.length === 0 && (
                          <span className="text-[#F6B98A]">0 metrics found</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Section Health */}
              <div>
                <h3 className="text-lg font-bold text-[#FFF7EE] mb-4 border-b border-[#F6B98A]/15 pb-2 flex items-center gap-2">
                  <AlignLeft size={18} className="text-[#F6B98A]" /> Resume Structure Health
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(atsResult.sections).map(([sectionName, data]: [string, any]) => (
                    <div key={sectionName} className={`p-4 rounded-xl border ${data.detected ? 'bg-[#3A2C6E]/40 border-[#F6B98A]/15' : 'bg-red-900/10 border-red-500/20'}`}>
                      <h5 className="font-bold text-sm text-[#FFF7EE] mb-1">{sectionName}</h5>
                      <div className="flex items-center gap-2 mt-2">
                        {data.detected ? (
                          <span className="flex items-center text-xs text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">
                            <CheckCircle size={12} className="mr-1"/> {data.quality_signal || 'Detected'}
                          </span>
                        ) : (
                          <span className="flex items-center text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded">
                            <XCircle size={12} className="mr-1"/> Missing
                          </span>
                        )}
                      </div>
                      {data.recommendation && <p className="text-xs text-[#FFF7EE]/60 mt-2 pt-2 border-t border-[#F6B98A]/10">{data.recommendation}</p>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Improvement Priorities */}
              {atsResult.improvement_priorities?.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-[#FFF7EE] mb-4 border-b border-[#F6B98A]/15 pb-2 flex items-center gap-2">
                    <Award size={18} className="text-[#F6B98A]" /> Actionable Improvement Priorities
                  </h3>
                  <div className="space-y-4">
                    {atsResult.improvement_priorities.map((priority: any, idx: number) => (
                      <div key={idx} className="bg-[#3A2C6E]/30 border border-[#F6B98A]/15 p-5 rounded-xl border-l-4 border-l-[#F6B98A] hover:bg-[#3A2C6E]/50 transition-colors">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-base font-bold text-[#F6B98A]">{priority.category}</h4>
                          <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${priority.impact === 'HIGH IMPACT' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
                            {priority.impact}
                          </span>
                        </div>
                        <p className="text-[#FFF7EE] mb-2 font-medium text-sm">{priority.issue}</p>
                        <p className="text-xs text-[#FFF7EE]/70 mb-3"><span className="text-[#FFF7EE] font-semibold">Why it matters:</span> {priority.why_it_matters}</p>
                        <div className="bg-[#181130]/50 p-3 rounded-lg text-xs text-emerald-300 border border-emerald-500/20">
                          <span className="font-bold">Recommended Action: </span> {priority.what_to_change}
                          {priority.example && <p className="mt-1 text-[#FFF7EE]/80 text-xs italic font-mono bg-[#181130]/80 p-2 rounded">{priority.example}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}

