"use client"

import type {
  AlertPriority,
  CaseReadMinimal,
  AlertSeverity,
  AlertStatus,
  CasesListCasesData,
} from "@/client"
import { alertsListAlerts, casesListCases } from "@/client"
import {
  type CursorPaginationResponse,
  useCursorPagination,
} from "./use-cursor-pagination"

// Convenience hook for cases specifically
export interface UseAlertsPaginationParams {
  workspaceId: string
  limit?: number
  searchTerm?: string | null
  status?: AlertStatus | null
  priority?: AlertPriority | null
  severity?: AlertSeverity | null
  tags?: string[] | null
}

export function useAlertsPagination({
  workspaceId,
  limit,
  searchTerm,
  status,
  priority,
  severity,
  tags,
}: UseAlertsPaginationParams) {
  // Wrapper function to adapt the API response to our generic interface
  const adaptedCasesListCases = async (
    params: CasesListCasesData
  ): Promise<CursorPaginationResponse<CaseReadMinimal>> => {
    const response = await alertsListAlerts({
      ...params,
      searchTerm,
      status,
      priority,
      severity,
      tags,
    })
    return {
      items: response.items,
      next_cursor: response.next_cursor,
      prev_cursor: response.prev_cursor,
      has_more: response.has_more,
      has_previous: response.has_previous,
      total_estimate: response.total_estimate,
    }
  }

  return useCursorPagination<CaseReadMinimal, CasesListCasesData>({
    workspaceId,
    limit,
    queryKey: [
      "cases",
      "paginated",
      workspaceId,
      searchTerm ?? null,
      status ?? null,
      priority ?? null,
      severity ?? null,
      tags ? [...tags].sort().join(",") : null,
    ],
    queryFn: adaptedCasesListCases,
  })
}
