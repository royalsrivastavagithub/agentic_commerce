"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Order, AdminOrdersResponse } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { useState, Fragment, useMemo } from "react"
import { AdminPageShell } from "@/components/admin/page-shell"
import { AdminSearchInput } from "@/components/admin/search-input"
import { AdminTableSkeleton } from "@/components/admin/table-skeleton"
import { AdminEmptyState } from "@/components/admin/empty-state"
import { AdminPagination } from "@/components/admin/pagination"

const statusColors: Record<string, string> = {
  PAID: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  CONFIRMED: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  SHIPPED: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  DELIVERED: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

const STATUSES = ["PAID", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]

const ORDER_LIMIT = 20

export default function OrdersContent() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", page],
    queryFn: () => api.get<AdminOrdersResponse>(
      `/admin/orders?skip=${(page - 1) * ORDER_LIMIT}&limit=${ORDER_LIMIT}`,
    ),
  })

  const orders = data?.orders || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / ORDER_LIMIT)

  const filtered = useMemo(() => {
    if (!orders.length) return []
    if (!search.trim()) return orders
    const q = search.toLowerCase()
    return orders.filter(
      (o) => o.id.toString().includes(q) || o.shipping_name.toLowerCase().includes(q) || o.shipping_phone.includes(q),
    )
  }, [orders, search])

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.patch(`/admin/orders/${id}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] })
      toast.success("Order status updated")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const [expandedId, setExpandedId] = useState<number | null>(null)

  return (
    <AdminPageShell title="Orders">
      <AdminSearchInput value={search} onChange={setSearch} placeholder="Search orders..." />

      {isLoading ? (
        <AdminTableSkeleton rows={5} />
      ) : filtered.length === 0 ? (
        <AdminEmptyState label="orders" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead>Date</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((o) => (
              <Fragment key={o.id}>
                <TableRow className="cursor-pointer" onClick={() => setExpandedId(expandedId === o.id ? null : o.id)}>
                  <TableCell className="font-medium">#{o.id}</TableCell>
                  <TableCell className="text-muted-foreground">{o.shipping_name}</TableCell>
                  <TableCell>
                    <select
                      value={o.status}
                      onChange={(e) => statusMutation.mutate({ id: o.id, status: e.target.value })}
                      className={`rounded-md px-2 py-0.5 text-xs font-medium capitalize outline-none ${statusColors[o.status] || "bg-gray-100 text-gray-800"}`}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {STATUSES.map((s) => <option key={s} value={s}>{s.toLowerCase()}</option>)}
                    </select>
                  </TableCell>
                  <TableCell className="text-right">₹{o.total.toFixed(2)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(o.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </TableCell>
                  <TableCell>
                    <button onClick={(e) => { e.stopPropagation(); setExpandedId(expandedId === o.id ? null : o.id) }} className="text-xs text-amazon-link hover:underline">
                      {expandedId === o.id ? "Hide" : "Details"}
                    </button>
                  </TableCell>
                </TableRow>
                {expandedId === o.id && (
                  <TableRow key={`${o.id}-details`}>
                    <TableCell colSpan={6} className="bg-muted/30 p-4">
                      <div className="space-y-2 text-sm">
                        <p><strong>Shipping:</strong> {o.shipping_name}, {o.shipping_phone}</p>
                        <p>{o.shipping_address_line_1}, {o.shipping_city}, {o.shipping_state} {o.shipping_pincode}</p>
                        <p><strong>Items:</strong> {o.items.map((i) => `${i.product_name} × ${i.quantity}`).join(", ")}</p>
                        {o.razorpay_payment_id && <p><strong>Payment ID:</strong> {o.razorpay_payment_id}</p>}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            ))}
          </TableBody>
        </Table>
      )}

      <AdminPagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </AdminPageShell>
  )
}
