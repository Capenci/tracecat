import type { LucideIcon } from "lucide-react"
import type React from "react"
import type { PropsWithChildren } from "react"
import type { AlertPriority, AlertSeverity, AlertStatus } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type AlertBadgeValue = AlertStatus | AlertPriority | AlertSeverity
export interface AlertBadgeProps<T extends AlertBadgeValue>
  extends PropsWithChildren<React.HTMLAttributes<HTMLElement>> {
  value: T
  label: string
  icon: LucideIcon
  color?: string
}

const defaultColor = "border-slate-400/70 bg-slate-50 text-slate-600/80"

export function AlertBadge<T extends AlertBadgeValue>({
  label,
  icon: Icon,
  className,
  color,
}: AlertBadgeProps<T>) {
  return (
    <Badge
      variant="outline"
      className={cn(
        defaultColor,
        "items-center gap-1 border-0",
        color,
        className
      )}
    >
      <Icon className="stroke-inherit/5 size-3 flex-1" strokeWidth={3} />
      <span>{label}</span>
    </Badge>
  )
}
