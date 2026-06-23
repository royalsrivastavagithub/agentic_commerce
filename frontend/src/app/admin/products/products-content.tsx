"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState } from "react"
import { Pencil, Trash2 } from "lucide-react"
import { AdminPageShell } from "@/components/admin/page-shell"
import { AdminSearchInput } from "@/components/admin/search-input"
import { AdminTableSkeleton } from "@/components/admin/table-skeleton"
import { AdminEmptyState } from "@/components/admin/empty-state"
import { AdminPagination } from "@/components/admin/pagination"
import { DeleteConfirmDialog } from "@/components/admin/delete-dialog"
import { buildSortParams } from "@/lib/filter-utils"

const LIMIT = 20

export default function ProductsContent() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState("default")
  const [minRating, setMinRating] = useState(0)
  const [minDiscount, setMinDiscount] = useState(0)
  const [isFeatured, setIsFeatured] = useState<boolean | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [editProduct, setEditProduct] = useState<Product | null>(null)
  const [editForm, setEditForm] = useState({ price: "", stock: "", discount_percentage: "", is_featured: false })
  const [editErrors, setEditErrors] = useState<Record<string, string>>({})

  const sortParams = buildSortParams(sort)
  const skip = (page - 1) * LIMIT

  let filterParams = ""
  if (minRating > 0) filterParams += `&min_rating=${minRating}`
  if (minDiscount > 0) filterParams += `&min_discount=${minDiscount}`
  if (isFeatured !== null) filterParams += `&is_featured=${isFeatured}`

  const { data, isLoading } = useQuery({
    queryKey: ["admin-products", search, page, sort, minRating, minDiscount, isFeatured],
    queryFn: () => {
      const base = search.trim()
        ? `/products/search?q=${encodeURIComponent(search)}&skip=${skip}&limit=${LIMIT}`
        : `/products?skip=${skip}&limit=${LIMIT}`
      return api.get<{ products: Product[]; total: number }>(base + sortParams + filterParams)
    },
  })

  const products = data?.products || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / LIMIT)

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] })
      toast.success("Product deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const validateEditForm = () => {
    const errors: Record<string, string> = {}
    const price = parseFloat(editForm.price)
    if (isNaN(price) || price < 0) errors.price = "Must be a valid positive number"
    const stock = parseInt(editForm.stock, 10)
    if (isNaN(stock) || stock < 0) errors.stock = "Must be a valid non-negative integer"
    const discount = parseFloat(editForm.discount_percentage)
    if (isNaN(discount) || discount < 0 || discount > 100) errors.discount_percentage = "Must be 0–100"
    setEditErrors(errors)
    return Object.keys(errors).length === 0
  }

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

  const getDiscount = (p: Product) => p.discountPercentage ?? p.discount_percentage ?? 0
  const getFeatured = (p: Product) => p.is_featured

  return (
    <AdminPageShell title="Products">
      <div className="flex flex-wrap items-center gap-3">
        <AdminSearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search products..." />
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(1) }}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-amazon-link"
        >
          <option value="default">Default</option>
          <option value="price-asc">Price: Low to High</option>
          <option value="price-desc">Price: High to Low</option>
          <option value="rating">Top Rated</option>
          <option value="title-asc">Title A–Z</option>
          <option value="title-desc">Title Z–A</option>
          <option value="discount">Biggest Discount</option>
        </select>
        <select
          value={minRating}
          onChange={(e) => { setMinRating(Number(e.target.value)); setPage(1) }}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-amazon-link"
        >
          <option value={0}>Any rating</option>
          <option value={4}>4★ & up</option>
          <option value={3}>3★ & up</option>
          <option value={2}>2★ & up</option>
          <option value={1}>1★ & up</option>
        </select>
        <select
          value={minDiscount}
          onChange={(e) => { setMinDiscount(Number(e.target.value)); setPage(1) }}
          className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:border-amazon-link"
        >
          <option value={0}>Any discount</option>
          <option value={10}>10%+ off</option>
          <option value={20}>20%+ off</option>
          <option value={30}>30%+ off</option>
          <option value={50}>50%+ off</option>
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isFeatured === true} onChange={(e) => { setIsFeatured(e.target.checked ? true : null); setPage(1) }} />
          Featured only
        </label>
      </div>

      {isLoading ? (
        <AdminTableSkeleton rows={5} />
      ) : products.length === 0 ? (
        <AdminEmptyState label="products" />
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
            {products.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="text-muted-foreground">{p.id}</TableCell>
                <TableCell className="font-medium">{p.title}</TableCell>
                <TableCell className="text-right">₹{p.price.toFixed(2)}</TableCell>
                <TableCell className="text-right">{getDiscount(p) > 0 ? `${getDiscount(p)}%` : "—"}</TableCell>
                <TableCell className="text-right">{p.stock}</TableCell>
                <TableCell className="text-center">{getFeatured(p) ? "✓" : "✗"}</TableCell>
                <TableCell className="text-right">★{p.rating.toFixed(1)}</TableCell>
                <TableCell className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => {
                    setEditProduct(p)
                    setEditForm({
                      price: String(p.price),
                      stock: String(p.stock),
                      discount_percentage: String(getDiscount(p)),
                      is_featured: getFeatured(p),
                    })
                    setEditErrors({})
                  }}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setDeleteId(p.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
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
        title="Delete Product"
        description={deleteId ? `Are you sure you want to delete product #${deleteId}?` : ""}
        onConfirm={() => deleteMutation.mutate(deleteId!)}
        disabled={deleteMutation.isPending}
      />

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
                <Label htmlFor="edit-price">Price (₹)</Label>
                <Input id="edit-price" type="number" step="0.01" min="0"
                  value={editForm.price}
                  onChange={(e) => setEditForm((f) => ({ ...f, price: e.target.value }))}
                />
                {editErrors.price && <p className="mt-1 text-xs text-destructive">{editErrors.price}</p>}
              </div>
              <div>
                <Label htmlFor="edit-discount">Discount (%)</Label>
                <Input id="edit-discount" type="number" min="0" max="100"
                  value={editForm.discount_percentage}
                  onChange={(e) => setEditForm((f) => ({ ...f, discount_percentage: e.target.value }))}
                />
                {editErrors.discount_percentage && <p className="mt-1 text-xs text-destructive">{editErrors.discount_percentage}</p>}
              </div>
              <div>
                <Label htmlFor="edit-stock">Stock</Label>
                <Input id="edit-stock" type="number" min="0"
                  value={editForm.stock}
                  onChange={(e) => setEditForm((f) => ({ ...f, stock: e.target.value }))}
                />
                {editErrors.stock && <p className="mt-1 text-xs text-destructive">{editErrors.stock}</p>}
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="featured" checked={editForm.is_featured}
                  onChange={(e) => setEditForm((f) => ({ ...f, is_featured: e.target.checked }))}
                />
                <Label htmlFor="featured">Featured</Label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditProduct(null)}>Cancel</Button>
            <Button onClick={() => {
              if (!validateEditForm()) return
              updateMutation.mutate({
                id: editProduct!.id,
                price: parseFloat(editForm.price),
                stock: parseInt(editForm.stock, 10),
                discount_percentage: parseFloat(editForm.discount_percentage),
                is_featured: editForm.is_featured,
              })
            }} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AdminPageShell>
  )
}
