"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState, useMemo } from "react"
import { Search, Pencil, Trash2 } from "lucide-react"

export default function ProductsContent() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [editProduct, setEditProduct] = useState<Product | null>(null)
  const [editForm, setEditForm] = useState({ price: 0, stock: 0, discount_percentage: 0, is_featured: false })

  const { data, isLoading } = useQuery({
    queryKey: ["admin-products"],
    queryFn: () => api.get<{ products: Product[]; total: number }>("/products?limit=1000"),
  })

  const filtered = useMemo(() => {
    if (!data?.products) return []
    if (!search.trim()) return data.products
    const q = search.toLowerCase()
    return data.products.filter(
      (p) => p.title.toLowerCase().includes(q) || p.brand?.toLowerCase().includes(q) || p.category?.toLowerCase().includes(q),
    )
  }, [data, search])

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] })
      toast.success("Product deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number; price: number; stock: number; discount_percentage: number; is_featured: boolean }) =>
      api.put(`/admin/products/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] })
      toast.success("Product updated")
      setEditProduct(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Products</h1>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search products..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
      </div>

      {isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      ) : filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground">No products found.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Discount</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-center">Featured</TableHead>
              <TableHead className="text-right">Rating</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="text-muted-foreground">{p.id}</TableCell>
                <TableCell className="font-medium">{p.title}</TableCell>
                <TableCell className="text-right">₹{p.price.toFixed(2)}</TableCell>
                <TableCell className="text-right">{p.discount_percentage > 0 ? `${p.discount_percentage}%` : "—"}</TableCell>
                <TableCell className="text-right">{p.stock}</TableCell>
                <TableCell className="text-center">{p.is_featured ? "✓" : "—"}</TableCell>
                <TableCell className="text-right">★{p.rating.toFixed(1)}</TableCell>
                <TableCell className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => { setEditProduct(p); setEditForm({ price: p.price, stock: p.stock, discount_percentage: p.discount_percentage, is_featured: p.is_featured }) }}>
                    <Pencil className="h-4 w-4" />
                  </Button>

                  <Dialog open={deleteId === p.id} onOpenChange={(open) => { if (!open) setDeleteId(null) }}>
                    <Button variant="ghost" size="icon" onClick={() => setDeleteId(p.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Delete Product</DialogTitle>
                        <DialogDescription>Are you sure you want to delete &quot;{p.title}&quot;?</DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
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

      {/* Edit dialog */}
      <Dialog open={editProduct !== null} onOpenChange={(open) => { if (!open) setEditProduct(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Product — {editProduct?.title}</DialogTitle>
            <DialogDescription>Update price, stock, discount, or featured status.</DialogDescription>
          </DialogHeader>
          {editProduct && (
            <div className="space-y-4 py-2">
              <div>
                <label className="text-sm font-medium">Price (₹)</label>
                <input type="number" step="0.01" value={editForm.price} onChange={(e) => setEditForm((f) => ({ ...f, price: parseFloat(e.target.value) || 0 }))} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-amazon-link" />
              </div>
              <div>
                <label className="text-sm font-medium">Discount (%)</label>
                <input type="number" min="0" max="100" value={editForm.discount_percentage} onChange={(e) => setEditForm((f) => ({ ...f, discount_percentage: parseInt(e.target.value) || 0 }))} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-amazon-link" />
              </div>
              <div>
                <label className="text-sm font-medium">Stock</label>
                <input type="number" min="0" value={editForm.stock} onChange={(e) => setEditForm((f) => ({ ...f, stock: parseInt(e.target.value) || 0 }))} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-amazon-link" />
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="featured" checked={editForm.is_featured} onChange={(e) => setEditForm((f) => ({ ...f, is_featured: e.target.checked }))} />
                <label htmlFor="featured" className="text-sm font-medium">Featured</label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditProduct(null)}>Cancel</Button>
            <Button onClick={() => updateMutation.mutate({ id: editProduct!.id, ...editForm })} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
