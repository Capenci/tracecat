"use client"

import type React from "react"
import type { AlertReadMinimal, CaseReadMinimal } from "@/client"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { useDeleteAlert, useDeleteCase } from "@/lib/hooks"
import { useWorkspaceId } from "@/providers/workspace-id"

export function DeleteAlertAlertDialog({
  selectedAlert,
  setSelectedAlert,
  children,
}: React.PropsWithChildren<{
  selectedAlert: AlertReadMinimal | null
  setSelectedAlert: (selectedAlert: AlertReadMinimal | null) => void
}>) {
  const workspaceId = useWorkspaceId()
  const { deleteAlert } = useDeleteAlert({ workspaceId })

  return (
    <AlertDialog
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          setSelectedAlert(null)
        }
      }}
    >
      {children}
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete alert</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete this alert? This action cannot be
            undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            onClick={async () => {
              if (selectedAlert) {
                console.log("Deleting case", selectedAlert)
                await deleteAlert(selectedAlert.id)
              }
              setSelectedAlert(null)
            }}
          >
            Confirm
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export const DeleteAlertAlertDialogTrigger = AlertDialogTrigger
