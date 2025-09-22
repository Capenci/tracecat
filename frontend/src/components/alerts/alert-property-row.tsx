import type { ReactNode } from "react"

interface AlertPropertyRowProps {
  label: string
  value: ReactNode
}

export function AlertPropertyRow({ label, value }: AlertPropertyRowProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground">{label}</span>
      {value}
    </div>
  )
}
