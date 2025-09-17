"use client"

import { BracesIcon, SquareStackIcon } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

export enum AlertsViewMode {
  Alerts = "alerts",
  CustomFields = "custom-fields",
}

interface AlertsViewToggleProps {
  view: AlertsViewMode
  onViewChange?: (view: AlertsViewMode) => void
  className?: string
}

export function AlertsViewToggle({
  view,
  onViewChange,
  className,
}: AlertsViewToggleProps) {
  const handleViewChange = (view: AlertsViewMode) => {
    onViewChange?.(view)
  }

  // Minimal toggle similar to workflows
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border bg-transparent",
        className
      )}
    >
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={() => handleViewChange(AlertsViewMode.Alerts)}
              className={cn(
                "flex size-7 items-center justify-center rounded-l-sm transition-colors",
                view === AlertsViewMode.Alerts
                  ? "bg-background text-accent-foreground"
                  : "bg-accent text-muted-foreground hover:bg-muted/50"
              )}
              aria-current={view === AlertsViewMode.Alerts}
              aria-label="Cases view"
            >
              <SquareStackIcon className="size-3.5" />
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Alerts table</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={() => handleViewChange(AlertsViewMode.CustomFields)}
              className={cn(
                "flex size-7 items-center justify-center rounded-r-sm transition-colors",
                view === AlertsViewMode.CustomFields
                  ? "bg-background text-accent-foreground"
                  : "bg-accent text-muted-foreground hover:bg-muted/50"
              )}
              aria-current={view === AlertsViewMode.CustomFields}
              aria-label="Custom fields view"
            >
              <BracesIcon className="size-3.5" />
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Custom fields</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
}
