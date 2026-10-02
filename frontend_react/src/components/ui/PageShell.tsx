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
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-[22px] sm:text-[26px] font-bold tracking-tight text-[#FFF7EE] leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-[rgba(255,247,238,0.52)] mt-1 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div className="cq-divider" />
      <div className="w-full flex-1">
        {children}
      </div>
    </div>
  )
}

export default PageShell
