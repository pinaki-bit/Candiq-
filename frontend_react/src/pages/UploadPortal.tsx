import React, { useState, useRef } from 'react'
import { FileUp, File, X, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { PageShell } from '../components/ui/PageShell'
import { LiquidButton } from '../components/ui/liquid-glass-button'

export function UploadPortal() {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [results, setResults] = useState<any>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files))
    }
  }

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    let processed = 0
    let failed = 0

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        
        try {
          await api.post('/resumes/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
          processed++
        } catch (err) {
          console.error(`Failed to upload ${file.name}`, err)
          failed++
        }
      }

      setResults({
        status: failed > 0 ? 'warning' : 'success',
        message: `Successfully processed ${processed} resumes. ${failed > 0 ? `${failed} failed.` : ''}`,
        processed_count: processed,
      })
      if (processed === files.length) {
         setFiles([])
      }
    } catch (error) {
      console.error('Upload process failed:', error)
      setResults({ status: 'error', message: 'Upload process failed entirely.', processed_count: 0 })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <PageShell
      title="Resume Intelligence"
      subtitle="Upload candidate resumes and let Candiq extract, classify, and understand every signal."
    >
      <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Upload Zone & Selected Files — 7/12 Cols on Desktop */}
        <div className="lg:col-span-7 w-full flex flex-col gap-6">
          <div 
            className={`cq-dropzone flex flex-col items-center justify-center p-10 sm:p-14 transition-all duration-200 ${
              isDragging ? 'cq-dropzone-active' : ''
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="w-14 h-14 rounded-2xl bg-[rgba(58,44,110,0.50)] border border-[rgba(255,255,255,0.10)] flex items-center justify-center mb-5">
              <FileUp className={`w-8 h-8 ${isDragging ? 'text-[#F6B98A]' : 'text-[#F6B98A]/70'}`} />
            </div>
            <h3 className="text-[16px] font-semibold text-[#FFF7EE] mb-2 text-center">Drag and drop resumes here</h3>
            <p className="text-[13px] text-[rgba(255,247,238,0.50)] mb-6 text-center">Supports PDF format up to 10MB.</p>
            <LiquidButton 
              onClick={() => fileInputRef.current?.click()}
              className="text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.30)] rounded-xl"
            >
              Browse Files
            </LiquidButton>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              multiple 
              accept="application/pdf"
              onChange={handleFileSelect}
            />
          </div>

          {files.length > 0 && (
            <div className="cq-card-elevated rounded-2xl p-5">
              <h3 className="text-[13px] font-bold text-[#FFF7EE] mb-4">Selected Files ({files.length})</h3>
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-[rgba(58,44,110,0.35)] border border-[rgba(255,255,255,0.06)] group hover:border-[rgba(246,185,138,0.15)] transition-colors">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <File className="w-5 h-5 text-[#F6B98A] shrink-0" />
                      <span className="text-[12px] text-[#FFF7EE] truncate">{file.name}</span>
                      <span className="text-[11px] text-[rgba(255,247,238,0.40)] shrink-0">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                    <LiquidButton 
                      onClick={() => removeFile(index)}
                      variant="destructive"
                      size="icon"
                      className="p-1 h-6 w-6 opacity-80 sm:opacity-0 sm:group-hover:opacity-100 transition-all"
                    >
                      <X className="w-3 h-3" />
                    </LiquidButton>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex justify-end">
                <LiquidButton 
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="text-[#140F25] font-semibold bg-gradient-to-r from-[#F6B98A] to-[#C4749B] shadow-[0_4px_14px_rgba(246,185,138,0.30)] rounded-xl disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#181130]" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <FileUp className="w-4 h-4 text-[#181130]" />
                      Upload to Pipeline
                    </>
                  )}
                </LiquidButton>
              </div>
            </div>
          )}
        </div>

        {/* Processing Rules & Ingest Results — 5/12 Cols on Desktop */}
        <div className="lg:col-span-5 w-full flex flex-col gap-6">
          <div className="cq-card-elevated rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <h3 className="text-[13px] font-bold text-[#FFF7EE] mb-4">Processing Rules</h3>
              <ul className="space-y-4 text-[13px] text-[rgba(255,247,238,0.65)]">
                <li className="flex gap-3 items-start">
                  <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Files are securely encrypted in transit and at rest.</span>
                </li>
                <li className="flex gap-3 items-start">
                  <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Text is extracted using pdfminer.six with optional OCR fallback.</span>
                </li>
                <li className="flex gap-3 items-start">
                  <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>NLP Pipeline identifies named entities and structures sections.</span>
                </li>
                <li className="flex gap-3 items-start">
                  <AlertTriangle className="w-5 h-5 text-[#F6B98A] shrink-0 mt-0.5" />
                  <span>Duplicate uploads (based on file hash) will be skipped.</span>
                </li>
              </ul>
            </div>

            {results && (
              <div className="mt-5 p-4 rounded-xl bg-[rgba(74,222,128,0.07)] border border-[rgba(74,222,128,0.18)] text-[#4ADE80] text-[13px] flex gap-3 items-start">
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5 text-emerald-400" />
                <div>
                  <p className="font-semibold mb-0.5">{results.message}</p>
                  <p className="text-[rgba(74,222,128,0.70)]">Analyzed {results.processed_count} documents. Available in Talent Explorer.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageShell>
  )
}
