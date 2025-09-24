"use client"

import { UserIcon } from "lucide-react"
import type {
  AlertPriority,
  AlertSeverity,
  AlertStatus,
} from "@/client"
import { AlertBadge } from "@/components/alerts/alert-badge"
import {
  PRIORITIES,
  SEVERITIES,
  STATUSES,
} from "@/components/alerts/alert-categories"
import { CaseValueDisplay } from "@/components/cases/case-value-display"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import UserAvatar from "@/components/user-avatar"
import { User } from "@/lib/auth"
import { cn, linearStyles } from "@/lib/utils"

// Color mappings for Linear-style display
function getPriorityColor(priority: AlertPriority): string {
  switch (priority) {
    case "high":
    case "critical":
      return "text-red-600"
    case "medium":
      return "text-orange-600"
    case "low":
      return "text-gray-600"
    default:
      return "text-muted-foreground"
  }
}

function getSeverityColor(severity: AlertSeverity): string {
  switch (severity) {
    case "high":
    case "critical":
    case "fatal":
      return "text-red-600"
    case "medium":
      return "text-orange-600"
    case "low":
      return "text-gray-600"
    default:
      return "text-muted-foreground"
  }
}

interface StatusSelectProps {
  status: AlertStatus
  onValueChange: (status: AlertStatus) => void
}

export function StatusSelect({ status, onValueChange }: StatusSelectProps) {
  const currentStatus = STATUSES[status]

  return (
    <Select value={status} onValueChange={onValueChange}>
      <SelectTrigger
        className={cn(linearStyles.trigger.base, linearStyles.trigger.hover)}
      >
        <SelectValue>
          <CaseValueDisplay
            icon={currentStatus.icon}
            label={currentStatus.label}
            color={
              currentStatus.value === "unknown"
                ? "text-muted-foreground"
                : undefined
            }
          />
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {Object.values(STATUSES).map((props) => (
          <SelectItem
            key={props.value}
            value={props.value}
            className="flex w-full"
          >
            <AlertBadge {...props} className="text-[10px] px-1.5 py-0.5" />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface PrioritySelectProps {
  priority: AlertPriority
  onValueChange: (priority: AlertPriority) => void
}

export function PrioritySelect({
  priority,
  onValueChange,
}: PrioritySelectProps) {
  const currentPriority = PRIORITIES[priority]

  return (
    <Select value={priority} onValueChange={onValueChange}>
      <SelectTrigger
        className={cn(linearStyles.trigger.base, linearStyles.trigger.hover)}
      >
        <SelectValue>
          <CaseValueDisplay
            icon={currentPriority.icon}
            label={currentPriority.label}
            color={getPriorityColor(currentPriority.value)}
          />
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="flex w-full">
        {Object.values(PRIORITIES).map((props) => (
          <SelectItem
            key={props.value}
            value={props.value}
            className="flex w-full"
          >
            <AlertBadge {...props} className="text-[10px] px-1.5 py-0.5" />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface SeveritySelectProps {
  severity: AlertSeverity
  onValueChange: (severity: AlertSeverity) => void
}

export function SeveritySelect({
  severity,
  onValueChange,
}: SeveritySelectProps) {
  const currentSeverity = SEVERITIES[severity]

  return (
    <Select value={severity} onValueChange={onValueChange}>
      <SelectTrigger
        className={cn(linearStyles.trigger.base, linearStyles.trigger.hover)}
      >
        <SelectValue>
          <CaseValueDisplay
            icon={currentSeverity.icon}
            label={currentSeverity.label}
            color={getSeverityColor(currentSeverity.value)}
          />
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {Object.values(SEVERITIES).map((props) => (
          <SelectItem
            key={props.value}
            value={props.value}
            className="flex w-full"
          >
            <AlertBadge {...props} className="text-[10px] px-1.5 py-0.5" />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
