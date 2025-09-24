"use client"

import { DotsHorizontalIcon } from "@radix-ui/react-icons"
import type { ColumnDef } from "@tanstack/react-table"
import { format, formatDistanceToNow } from "date-fns"
import fuzzysort from "fuzzysort"
import type { AlertReadMinimal, CaseReadMinimal } from "@/client"
import { AlertBadge } from "@/components/alerts/alert-badge"
import {
  PRIORITIES,
  SEVERITIES,
  STATUSES,
} from "@/components/alerts/alert-categories"
import { DataTableColumnHeader } from "@/components/data-table"
import { TagBadge } from "@/components/tag-badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { User } from "@/lib/auth"
import { capitalizeFirst } from "@/lib/utils"

const NO_DATA = "--" as const

export function createColumns(
  setSelectedAlert: (alert_: AlertReadMinimal) => void
): ColumnDef<AlertReadMinimal>[] {
  return [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          className="border-foreground/50"
          checked={
            table.getIsAllPageRowsSelected() ||
            (table.getIsSomePageRowsSelected() && "indeterminate")
          }
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <div
          onClick={(e) => {
            e.stopPropagation()
            e.preventDefault()
          }}
        >
          <Checkbox
            className="border-foreground/50"
            checked={row.getIsSelected()}
            onCheckedChange={(value) => row.toggleSelected(!!value)}
            aria-label="Select row"
          />
        </div>
      ),
      enableSorting: false,
      enableHiding: false,
    },

    {
      accessorKey: "short_id",
      header: ({ column }) => (
        <DataTableColumnHeader className="text-xs" column={column} title="ID" />
      ),
      cell: ({ row }) => (
        <div className="w-[80px] truncate text-xs">
          {row.getValue<AlertReadMinimal["short_id"]>("short_id")}
        </div>
      ),
      enableSorting: true,
      enableHiding: false,
      filterFn: (row, id, value) => {
        return value.includes(row.getValue<AlertReadMinimal["short_id"]>(id))
      },
    },
    {
      accessorKey: "summary",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Summary" />
      ),
      cell: ({ row }) => {
        return (
          <div className="flex space-x-2">
            <span className="max-w-[300px] truncate text-xs">
              {row.getValue<AlertReadMinimal["summary"]>("summary")}
            </span>
          </div>
        )
      },
      filterFn: (row, id, value) => {
        const rowValue = String(row.getValue<AlertReadMinimal["summary"]>(id))
        return fuzzysort.single(String(value), rowValue) !== null
      },
    },
    {
      accessorKey: "status",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Status" />
      ),
      cell: ({ row }) => {
        const status = row.getValue<AlertReadMinimal["status"]>("status")
        const props = STATUSES[status]
        if (!props) {
          return null
        }

        return <AlertBadge {...props} />
      },
      filterFn: (row, id, value) => {
        return value.includes(row.getValue<AlertReadMinimal["status"]>("status"))
      },
    },
    {
      accessorKey: "priority",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Priority" />
      ),
      cell: ({ row }) => {
        const priority = row.getValue<AlertReadMinimal["priority"]>("priority")
        if (!priority) {
          return null
        }
        const props = PRIORITIES[priority]

        return <AlertBadge {...props} />
      },
      filterFn: (row, id, value) => {
        return value.includes(
          row.getValue<AlertReadMinimal["priority"]>("priority")
        )
      },
    },
    {
      accessorKey: "severity",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Severity" />
      ),
      cell: ({ row }) => {
        const severity = row.getValue<AlertReadMinimal["severity"]>("severity")
        if (!severity) {
          return null
        }

        const props = SEVERITIES[severity]
        if (!props) {
          return null
        }

        return <AlertBadge {...props} />
      },
      filterFn: (row, id, value) => {
        return value.includes(
          row.getValue<AlertReadMinimal["severity"]>("severity")
        )
      },
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Created At" />
      ),
      cell: ({ row }) => {
        const dt = new Date(
          row.getValue<AlertReadMinimal["created_at"]>("created_at")
        )
        const timeAgo = capitalizeFirst(
          formatDistanceToNow(dt, { addSuffix: true })
        )
        const fullDateTime = format(dt, "PPpp") // e.g. "Apr 13, 2024, 2:30 PM EDT"

        return (
          <Tooltip>
            <TooltipTrigger>
              <span className="truncate text-xs">{fullDateTime}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p>{timeAgo}</p>
            </TooltipContent>
          </Tooltip>
        )
      },
      filterFn: (row, id, value) => {
        const dateStr =
          row.getValue<AlertReadMinimal["created_at"]>("created_at")
        return value.includes(dateStr)
      },
    },
    {
      accessorKey: "updated_at",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Updated At" />
      ),
      cell: ({ row }) => {
        const dt = new Date(
          row.getValue<AlertReadMinimal["updated_at"]>("updated_at")
        )
        const timeAgo = capitalizeFirst(
          formatDistanceToNow(dt, { addSuffix: true })
        )
        const fullDateTime = format(dt, "PPpp") // e.g. "Apr 13, 2024, 2:30 PM EDT"

        return (
          <Tooltip>
            <TooltipTrigger>
              <span className="truncate text-xs">{fullDateTime}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p>{timeAgo}</p>
            </TooltipContent>
          </Tooltip>
        )
      },
      filterFn: (row, id, value) => {
        const dateStr =
          row.getValue<AlertReadMinimal["updated_at"]>("updated_at")
        return value.includes(dateStr)
      },
    },
    {
      id: "Tags",
      accessorKey: "tags",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="Tags" />
      ),
      cell: ({ getValue }) => {
        const tags = getValue<AlertReadMinimal["tags"]>()
        return (
          <div className="flex flex-wrap gap-1">
            {tags?.length ? (
              tags.map((tag) => <TagBadge key={tag.id} tag={tag} />)
            ) : (
              <span className="text-xs text-muted-foreground">{NO_DATA}</span>
            )}
          </div>
        )
      },
      filterFn: (row, id, value) => {
        const tags = row.getValue<AlertReadMinimal["tags"]>("tags")
        if (!tags || tags.length === 0) {
          return false
        }
        return tags.some(
          (tag) =>
            value.includes(tag.name) ||
            value.includes(tag.id) ||
            (tag.ref && value.includes(tag.ref))
        )
      },
    },
    {
      id: "actions",
      header: ({ column }) => (
        <DataTableColumnHeader column={column} title="" />
      ),
      enableHiding: false,
      enableSorting: false,
      cell: ({ row }) => {
        // Import is done dynamically to avoid circular dependency issues
        const { AlertActions } = require("@/components/alerts/alert-actions")

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="size-6 p-0"
                onClick={(e) => e.stopPropagation()}
              >
                <span className="sr-only">Open menu</span>
                <DotsHorizontalIcon className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <AlertActions
                item={row.original}
                setSelectedAlert={setSelectedAlert}
              />
            </DropdownMenuContent>
          </DropdownMenu>
        )
      },
    },
  ]
}
