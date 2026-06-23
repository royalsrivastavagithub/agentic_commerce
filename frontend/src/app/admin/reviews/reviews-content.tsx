"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Review, AdminReviewsResponse } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { toast } from "sonner"
import { useState } from "react"
import { Trash2, Star } from "lucide-react"
import { AdminPageShell } from "@/components/admin/page-shell"
import { AdminSearchInput } from "@/components/admin/search-input"
import { AdminTableSkeleton } from "@/components/admin/table-skeleton"
import { AdminEmptyState } from "@/components/admin/empty-state"
import { AdminPagination } from "@/components/admin/pagination"
import { DeleteConfirmDialog } from "@/components/admin/delete-dialog"

const REVIEW_LIMIT = 20

export default function ReviewsContent() {
  const queryClient = useQueryClient()
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ["admin-reviews", search, page],
    queryFn: () => {
      let url = `/admin/reviews?page=${page}&per_page=${REVIEW_LIMIT}`
      if (search.trim()) url += `&product_id=${search.trim()}`
      return api.get<AdminReviewsResponse>(url)
    },
  })

  const reviews = data?.reviews || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / REVIEW_LIMIT)

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/reviews/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-reviews"] })
      toast.success("Review deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <AdminPageShell title="Reviews">
      <AdminSearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search by product ID..." />

      {isLoading ? (
        <AdminTableSkeleton rows={5} />
      ) : !reviews?.length ? (
        <AdminEmptyState label="reviews" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Rating</TableHead>
              <TableHead>Comment</TableHead>
              <TableHead>Date</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {reviews.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="text-muted-foreground">{r.id}</TableCell>
                <TableCell className="font-medium">#{r.product_id}</TableCell>
                <TableCell className="text-muted-foreground">{r.user?.email || `#${r.user_id}`}</TableCell>
                <TableCell>
                  <div className="flex">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className={`h-3.5 w-3.5 ${i < r.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}`} />
                    ))}
                  </div>
                </TableCell>
                <TableCell className="max-w-xs truncate text-muted-foreground">{r.comment}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(r.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                </TableCell>
                <TableCell>
                  <button onClick={() => setDeleteId(r.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <AdminPagination page={page} totalPages={totalPages} onPageChange={setPage} />

      <DeleteConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => { if (!open) setDeleteId(null) }}
        title="Delete Review"
        description="Delete this review? This will recalculate the product's rating."
        onConfirm={() => deleteMutation.mutate(deleteId!)}
        disabled={deleteMutation.isPending}
      />
    </AdminPageShell>
  )
}
