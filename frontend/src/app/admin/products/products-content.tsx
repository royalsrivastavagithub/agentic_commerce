"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState } from "react"
import { Trash2 } from "lucide-react"

export default function ProductsContent() {
  const queryClient = useQueryClient()
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data: products, isLoading } = useQuery({
    queryKey: ["admin-products"],
    queryFn: () => api.get<{ products: Product[]; total: number }>("/products?limit=1000"),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] })
      toast.success("Product deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Products</h1>

      {isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      ) : !products?.products.length ? (
        <p className="text-sm text-muted-foreground">No products found.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Category</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-right">Rating</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.products.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="text-muted-foreground">{p.id}</TableCell>
                <TableCell className="font-medium">{p.title}</TableCell>
                <TableCell className="text-muted-foreground">{p.category}</TableCell>
                <TableCell className="text-right">₹{p.price.toFixed(2)}</TableCell>
                <TableCell className="text-right">{p.stock}</TableCell>
                <TableCell className="text-right">★{p.rating.toFixed(1)}</TableCell>
                <TableCell>
                  <Dialog open={deleteId === p.id} onOpenChange={(open) => { if (!open) setDeleteId(null) }}>
                    <DialogTrigger>
                      <Button variant="ghost" size="icon" onClick={() => setDeleteId(p.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Delete Product</DialogTitle>
                        <DialogDescription>Are you sure you want to delete &quot;{p.title}&quot;? This cannot be undone.</DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <DialogClose><Button variant="outline">Cancel</Button></DialogClose>
                        <Button variant="destructive" onClick={() => deleteMutation.mutate(p.id)} disabled={deleteMutation.isPending}>
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
