"use client"

import { useParams } from "next/navigation"
import { useEffect } from "react"
import { useGetAlert } from "@/lib/hooks"
import { useWorkspaceId } from "@/providers/workspace-id"
import { AlertPanelView } from "@/components/alerts/alert-panel-view"

export default function AlertDetailPage() {
  const params = useParams<{ alertId: string }>()
  const alertId = params?.alertId
  const workspaceId = useWorkspaceId()

  const { alertData } = useGetAlert({
    alertId: alertId || "",
    workspaceId,
  })

  useEffect(() => {
    if (alertData?.short_id && alertData?.summary) {
      document.title = `${alertData.short_id} | ${alertData.summary}`
    }
  }, [alertData])

  if (!alertId) {
    return null
  }

  return <AlertPanelView alertId={alertId} />
}


