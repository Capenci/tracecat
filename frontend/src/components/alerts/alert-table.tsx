"use client"

import type { Row } from "@tanstack/react-table"
import { useRouter } from "next/navigation"
import { useCallback, useMemo, useState } from "react"
import type {
  AlertPriority,
  AlertReadMinimal,
  AlertSeverity,
  AlertStatus,
  
} from "@/client"
// import { createColumns } from "@/components/cases/case-table-columns"
import { createColumns } from "@/components/alerts/alert-table-columns"
import { DataTable } from "@/components/data-table"
import { TooltipProvider } from "@/components/ui/tooltip"
import { useToast } from "@/components/ui/use-toast"
import { useAlertsPagination } from "@/hooks"
import { useAuth } from "@/hooks/use-auth"
import { useDebounce } from "@/hooks/use-debounce"
import { useDeleteAlert } from "@/lib/hooks"
import { useWorkspaceId } from "@/providers/workspace-id"
import { AlertTableFilters } from "./alert-table-filters"
import { DeleteAlertAlertDialog } from "./delete-alert-dialog"

export default function AlertTable() {
  const { user } = useAuth()
  const workspaceId = useWorkspaceId()
  const [pageSize, setPageSize] = useState(20)
  const [selectedAlert, setSelectedAlert] = useState<AlertReadMinimal | null>(null)
  const router = useRouter()

  // Server-side filter states
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [statusFilter, setStatusFilter] = useState<AlertStatus | null>(null)
  const [priorityFilter, setPriorityFilter] = useState<AlertPriority | null>(
    null
  )
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | null>(
    null
  )
  const [tagsFilter, _setTagsFilter] = useState<string[] | null>(null)

  // Debounce search term for better performance
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300)

  const {
    data: alerts,
    isLoading: alertsIsLoading,
    error: alertsError,
    goToNextPage,
    goToPreviousPage,
    goToFirstPage,
    hasNextPage,
    hasPreviousPage,
    currentPage,
    totalEstimate,
    startItem,
    endItem,
  } = useAlertsPagination({
    workspaceId,
    limit: pageSize,
    searchTerm: debouncedSearchTerm || null,
    status: statusFilter,
    priority: priorityFilter,
    severity: severityFilter,
    tags: tagsFilter,
  })
  const { toast } = useToast()
  const [isDeleting, setIsDeleting] = useState(false)
  const { deleteAlert } = useDeleteAlert({
    workspaceId,
  })

  const memoizedColumns = useMemo(
    () => createColumns(setSelectedAlert),
    [setSelectedAlert]
  )

  function handleClickRow(row: Row<AlertReadMinimal>) {
    return () =>
      router.push(`/workspaces/${workspaceId}/alerts/${row.original.id}`)
  }

  const handleDeleteRows = useCallback(
    async (selectedRows: Row<AlertReadMinimal>[]) => {
      if (selectedRows.length === 0) return

      try {
        setIsDeleting(true)
        // Get IDs of selected cases
        const alertIds = selectedRows.map((row) => row.original.id)

        // Call the delete operation
        await Promise.all(alertIds.map((alertId) => deleteAlert(alertId)))

        // Show success toast
        toast({
          title: `${alertIds.length} alert(s) deleted`,
          description: "The selected alerts have been deleted successfully.",
        })

        // Refresh the cases list
      } catch (error) {
        console.error("Failed to delete alerts:", error)
      } finally {
        setIsDeleting(false)
      }
    },
    [deleteAlert, toast]
  )

  // Handle filter changes
  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchTerm(value)
      if (value !== searchTerm) {
        goToFirstPage()
      }
    },
    [searchTerm, goToFirstPage]
  )

  const handleStatusChange = useCallback(
    (value: AlertStatus | null) => {
      setStatusFilter(value)
      goToFirstPage()
    },
    [goToFirstPage]
  )

  const handlePriorityChange = useCallback(
    (value: AlertPriority | null) => {
      setPriorityFilter(value)
      goToFirstPage()
    },
    [goToFirstPage]
  )

  const handleSeverityChange = useCallback(
    (value: AlertSeverity | null) => {
      setSeverityFilter(value)
      goToFirstPage()
    },
    [goToFirstPage]
  )


  return (
    <DeleteAlertAlertDialog
      selectedAlert={selectedAlert}
      setSelectedAlert={setSelectedAlert}
    >
      <TooltipProvider>
        <div className="space-y-4">
          <AlertTableFilters
            workspaceId={workspaceId}
            searchTerm={searchTerm}
            onSearchChange={handleSearchChange}
            statusFilter={statusFilter}
            onStatusChange={handleStatusChange}
            priorityFilter={priorityFilter}
            onPriorityChange={handlePriorityChange}
            severityFilter={severityFilter}
            onSeverityChange={handleSeverityChange}
          />
          <DataTable
            data={alerts || []}
            isLoading={alertsIsLoading || isDeleting}
            error={(alertsError as Error) || undefined}
            columns={memoizedColumns}
            onClickRow={handleClickRow}
            getRowHref={(row) =>
              `/workspaces/${workspaceId}/alerts/${row.original.id}`
            }
            onDeleteRows={handleDeleteRows}
            tableId={`${user?.id}-${workspaceId}-alerts`}
            serverSidePagination={{
              currentPage,
              hasNextPage,
              hasPreviousPage,
              pageSize,
              totalEstimate,
              startItem,
              endItem,
              onNextPage: goToNextPage,
              onPreviousPage: goToPreviousPage,
              onFirstPage: goToFirstPage,
              onPageSizeChange: setPageSize,
              isLoading: alertsIsLoading || isDeleting,
            }}
          />
        </div>
      </TooltipProvider>
    </DeleteAlertAlertDialog>
  )
}

