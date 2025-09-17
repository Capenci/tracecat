"use client"

import { useEffect } from "react"
import { AlertsViewMode } from "@/components/alerts/alerts-view-toggle"
import { CustomFieldsView } from "@/components/cases/custom-fields-view"
import { useLocalStorage } from "@/hooks/use-local-storage"
import AlertTable from "@/components/alerts/alert-table"

export default function AlertsPage() {
  const [view] = useLocalStorage("alerts-view", AlertsViewMode.Alerts)

  // Update document title based on view
  useEffect(() => {
    if (typeof window !== "undefined") {
      document.title =
        view === AlertsViewMode.CustomFields ? "Custom fields" : "Alerts"
    }
  }, [view])

  return (
    <>
      {view === AlertsViewMode.Alerts ? (
        <div className="size-full overflow-auto p-6 space-y-6">
          <AlertTable />
        </div>
      ) : (
        <CustomFieldsView />
      )}
    </>
  )
}
