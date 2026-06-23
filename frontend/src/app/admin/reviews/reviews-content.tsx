"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Review } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState } from "react"
import { Trash2, Star } from "lucide-react"

export default function ReviewsContent() {
  const queryClient = useQueryClient()
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data: reviews, isLoading } = useQuery({
    queryKey: ["admin-reviews"],
    queryFn: () => api.get<Review[]>("/admin/reviews"),
  })

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
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Reviews</h1>

      {isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      ) : !reviews?.length ? (
        <p className="text-sm text-muted-foreground">No reviews found.</p>
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
                  <Dialog open={deleteId === r.id} onOpenChange={(open) => { if (!open) setDeleteId(null) }}>
                    <DialogTrigger>
                      <Button variant="ghost" size="icon" onClick={() => setDeleteId(r.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Delete Review</DialogTitle>
                        <DialogDescription>Delete this review? This will recalculate the product&apos;s rating.</DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <DialogClose><Button variant="outline">Cancel</Button></DialogClose>
                        <Button variant="destructive" onClick={() => deleteMutation.mutate(r.id)} disabled={deleteMutation.isPending}>
                          {deleteMutation.isPending ? "Deleting..." : "Delete"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
