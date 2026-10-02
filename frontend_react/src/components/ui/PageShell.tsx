import type { ReactNode } from 'react'

export interface PageShellProps {
  title: ReactNode
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function PageShell({
  title,
  subtitle,
  action,
  children,
  className = '',
}: PageShellProps) {
  return (
    <div className={`w-full flex flex-col gap-6 ${className}`}>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-[22px] sm:text-[26px] font-bold tracking-tight text-[#FFF7EE] leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[13px] text-[rgba(255,247,238,0.48)] mt-1.5 leading-relaxed max-w-2xl">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>

      {/* Divider */}
      <div className="cq-divider" />

      {/* Page Content */}
      <div className="w-full flex-1">
        {children}
      </div>
    </div>
  )
}

export default PageShell
