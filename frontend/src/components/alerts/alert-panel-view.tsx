"use client"

import {
  Activity,
  BoxIcon,
  Braces,
  MessageSquare,
  MoreHorizontal,
  Paperclip,
} from "lucide-react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useCallback, useState } from "react"
import type {
  AlertPriority,
  AlertSeverity,
  AlertStatus,
  AlertUpdate,
  CasePriority,
  CaseSeverity,
  CaseStatus,
  CaseUpdate,
  UserRead,
} from "@/client"
import { CaseActivityFeed } from "@/components/cases/case-activity-feed"
import { CaseAttachmentsSection } from "@/components/cases/case-attachments-section"
import { CommentSection } from "@/components/alerts/alert-comments-section"
import { CustomField } from "@/components/cases/case-panel-custom-fields"
import { CasePanelDescription } from "@/components/cases/case-panel-description"
import { CasePanelSection } from "@/components/cases/case-panel-section"
import {
  AssigneeSelect,
  PrioritySelect,
  SeveritySelect,
  StatusSelect,
} from "@/components/cases/case-panel-selectors"
import { CasePanelSummary } from "@/components/cases/case-panel-summary"
import { CasePayloadSection } from "@/components/cases/case-payload-section"
import { CasePropertyRow } from "@/components/cases/case-property-row"
import { CaseRecordsSection } from "@/components/cases/case-records-section"
import { CaseWorkflowTrigger } from "@/components/cases/case-workflow-trigger"
import { AlertNotification } from "@/components/notifications"
import { TagBadge } from "@/components/tag-badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import { useWorkspaceMembers } from "@/hooks/use-workspace"
import {
  useAddAlertTag,
  useAddCaseTag,
  useGetAlert,
  useGetCase,
  useRemoveAlertTag,
  useRemoveCaseTag,
  useTags,
  useUpdateAlert,
  useUpdateCase,
} from "@/lib/hooks"
import { useWorkspaceId } from "@/providers/workspace-id"
import { AlertPanelSummary } from "./alert-panel-summary"
import { AlertPanelSection } from "./alert-panel-section"
import { AlertPropertyRow } from "./alert-property-row"
import { AlertPanelDescription } from "./alert-panel-description"
import { AlertActivityFeed } from "./alert-activity-feed"

type AlertPanelTab =
  | "comments"
  | "activity"
  | "attachments"
  | "records"
  | "payload"

interface AlertPanelContentProps {
  alertId: string
}

export function AlertPanelView({ alertId }: AlertPanelContentProps) {
  const workspaceId = useWorkspaceId()
  const { members } = useWorkspaceMembers(workspaceId)
  const router = useRouter()
  const searchParams = useSearchParams()

  const { alertData, alertDataIsLoading, alertDataError } = useGetAlert({
    alertId,
    workspaceId,
  })
  const { updateAlert } = useUpdateAlert({
    workspaceId,
    alertId,
  })
  const { addAlertTag } = useAddAlertTag({ alertId, workspaceId })
  const { removeAlertTag } = useRemoveAlertTag({ alertId, workspaceId })
  const { tags } = useTags(workspaceId)
  const { toast } = useToast()
  const [propertiesOpen, setPropertiesOpen] = useState(true)
  const [workflowOpen, setWorkflowOpen] = useState(true)

  // Get active tab from URL query params, default to "comments"
  const activeTab = (
    searchParams &&
    ["comments", "activity", "attachments", "records", "payload"].includes(
      searchParams.get("tab") || ""
    )
      ? (searchParams.get("tab") ?? "comments")
      : "comments"
  ) as AlertPanelTab

  // Function to handle tab changes and update URL
  const handleTabChange = useCallback(
    (tab: string) => {
      router.push(`/workspaces/${workspaceId}/alerts/${alertId}?tab=${tab}`)
    },
    [router, workspaceId, alertId]
  )

  if (alertDataIsLoading) {
    return (
      <div className="flex h-full flex-col space-y-4 p-4">
        <div className="flex items-center justify-between border-b p-4">
          <div className="flex items-center space-x-4">
            <Skeleton className="h-4 w-16" />
            <div className="flex items-center space-x-2">
              <Skeleton className="h-3 w-32" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
        </div>
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-[200px] w-full" />
        <div className="flex space-x-4">
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-6 w-20" />
        </div>
      </div>
    )
  }
  if (alertDataError || !alertData) {
    return (
      <AlertNotification
        level="error"
        message={alertDataError?.message ?? "Error occurred loading alert data"}
      />
    )
  }

  const handleStatusChange = async (newStatus: AlertStatus) => {
    const updateParams = {
      status: newStatus,
    } as Partial<AlertUpdate>
    await updateAlert(updateParams)
  }

  const handlePriorityChange = async (newPriority: AlertPriority) => {
    const params = {
      priority: newPriority,
    }
    await updateAlert(params)
  }

  const handleSeverityChange = async (newSeverity: AlertSeverity) => {
    const params = {
      severity: newSeverity,
    }
    await updateAlert(params)
  }


  const handleTagToggle = async (tagId: string, hasTag: boolean) => {
    try {
      if (hasTag) {
        // Remove tag
        await removeAlertTag(tagId)
      } else {
        // Add tag
        await addAlertTag({ tag_id: tagId })
      }
    } catch (error) {
      console.error("Failed to modify tag:", error)
      toast({
        title: "Error",
        description: `Failed to ${hasTag ? "remove" : "add"} tag ${hasTag ? "from" : "to"} case. Please try again.`,
        variant: "destructive",
      })
    }
  }

  const customFields = alertData.fields.filter((field) => !field.reserved)

  return (
    <div className="h-full flex w-full">
      <div className="h-full w-full min-w-0 flex">
        {/* Case properties section */}
        <div className="w-64 min-w-[200px] max-w-[300px] border-r">
          <div className="h-full overflow-y-auto p-4 min-w-0">
            <div className="space-y-10">
              {/* Properties Section */}
              <AlertPanelSection
                title="Properties"
                isOpen={propertiesOpen}
                onOpenChange={setPropertiesOpen}
              >
                <div className="space-y-4">
                  {/* Assign */}

                  {/* Status */}
                  <CasePropertyRow
                    label="Status"
                    value={
                      <StatusSelect
                        status={alertData.status}
                        onValueChange={handleStatusChange}
                      />
                    }
                  />

                  {/* Priority */}
                  <CasePropertyRow
                    label="Priority"
                    value={
                      <PrioritySelect
                        priority={alertData.priority || "unknown"}
                        onValueChange={handlePriorityChange}
                      />
                    }
                  />

                  {/* Severity */}
                  <CasePropertyRow
                    label="Severity"
                    value={
                      <SeveritySelect
                        severity={alertData.severity || "unknown"}
                        onValueChange={handleSeverityChange}
                      />
                    }
                  />

                  {/* Tags */}
                  <div className="pt-2">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs">Tags</span>
                      {tags && tags.length > 0 && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-5 w-5 p-0"
                            >
                              <MoreHorizontal className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="text-xs">
                            {tags.map((tag) => {
                              const hasTag = alertData.tags?.some(
                                (t) => t.id === tag.id
                              )
                              return (
                                <DropdownMenuCheckboxItem
                                  key={tag.id}
                                  className="text-xs"
                                  checked={hasTag}
                                  onClick={async (e) => {
                                    e.stopPropagation()
                                    await handleTagToggle(tag.id, !!hasTag)
                                  }}
                                >
                                  <div
                                    className="mr-2 flex size-2 rounded-full"
                                    style={{
                                      backgroundColor: tag.color || undefined,
                                    }}
                                  />
                                  <span>{tag.name}</span>
                                </DropdownMenuCheckboxItem>
                              )
                            })}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {alertData.tags?.length ? (
                        alertData.tags.map((tag) => (
                          <TagBadge key={tag.id} tag={tag} />
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          No tags
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Custom fields */}
                  <div className="pt-2">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs">Custom fields</span>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-5 w-5 p-0"
                          >
                            <MoreHorizontal className="h-3 w-3" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="text-xs">
                          <DropdownMenuItem asChild>
                            <Link
                              href={`/workspaces/${workspaceId}/custom-fields`}
                            >
                              Manage fields
                            </Link>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    {customFields.length === 0 ? (
                      <div className="text-xs text-muted-foreground">
                        No fields configured.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {customFields.map((field) => (
                          <AlertPropertyRow
                            key={field.id}
                            label={field.id}
                            value={
                              <CustomField
                                customField={field}
                                updateCase={updateAlert}
                              />
                            }
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </AlertPanelSection>
              {/* Workflow Triggers */}
              <AlertPanelSection
                title="Workflows"
                isOpen={workflowOpen}
                onOpenChange={setWorkflowOpen}
              >
                <CaseWorkflowTrigger caseData={alertData} />
              </AlertPanelSection>
            </div>
          </div>
        </div>
        {/* Main section */}
        <div className="flex-1 min-w-0">
          <div className="h-full overflow-auto min-w-0">
            <div className="py-8 pb-24 px-6 max-w-4xl mx-auto">
              {/* Header with Chat Toggle */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex-1">
                  {/* Case Summary */}
                  <AlertPanelSummary
                    alertData={alertData}
                    updateAlert={updateAlert}
                  />
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <AlertPanelDescription
                  alertData={alertData}
                  updateAlert={updateAlert}
                />
              </div>

              {/* Tabs using shadcn components */}
              <Tabs
                value={activeTab}
                onValueChange={handleTabChange}
                className="w-full"
              >
                <TabsList className="h-8 justify-start rounded-none bg-transparent p-0 border-b border-border w-full">
                  <TabsTrigger
                    className="flex h-full items-center justify-center rounded-none border-b-2 border-transparent py-0 text-xs font-medium data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    value="comments"
                  >
                    <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                    Comments
                  </TabsTrigger>
                  <TabsTrigger
                    className="flex h-full items-center justify-center rounded-none border-b-2 border-transparent py-0 text-xs font-medium ml-6 data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    value="activity"
                  >
                    <Activity className="mr-1.5 h-3.5 w-3.5" />
                    Activity
                  </TabsTrigger>
                  <TabsTrigger
                    className="flex h-full items-center justify-center rounded-none border-b-2 border-transparent py-0 text-xs font-medium ml-6 data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    value="attachments"
                  >
                    <Paperclip className="mr-1.5 h-3.5 w-3.5" />
                    Attachments
                  </TabsTrigger>
                  <TabsTrigger
                    className="flex h-full items-center justify-center rounded-none border-b-2 border-transparent py-0 text-xs font-medium ml-6 data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    value="records"
                  >
                    <BoxIcon className="mr-1.5 h-3.5 w-3.5" />
                    Records
                  </TabsTrigger>
                  <TabsTrigger
                    className="flex h-full items-center justify-center rounded-none border-b-2 border-transparent py-0 text-xs font-medium ml-6 data-[state=active]:border-foreground data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                    value="payload"
                  >
                    <Braces className="mr-1.5 h-3.5 w-3.5" />
                    Payload
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="comments" className="mt-4">
                  <CommentSection alertId={alertId} workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="activity" className="mt-4">
                  <AlertActivityFeed alertId={alertId} workspaceId={workspaceId} />
                </TabsContent>

                <TabsContent value="attachments" className="mt-4">
                  <CaseAttachmentsSection
                    caseId={alertId}
                    workspaceId={workspaceId}
                  />
                </TabsContent>

                <TabsContent value="records" className="mt-4">
                  <CaseRecordsSection
                    caseId={alertId}
                    workspaceId={workspaceId}
                  />
                </TabsContent>

                <TabsContent value="payload" className="mt-4">
                  <CasePayloadSection caseData={alertData} />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
