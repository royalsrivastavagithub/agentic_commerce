"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Category } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState, useMemo } from "react"
import { Search, Pencil, Trash2, Plus } from "lucide-react"
import { AdminPageShell } from "@/components/admin/page-shell"
import { AdminTableSkeleton } from "@/components/admin/table-skeleton"
import { AdminEmptyState } from "@/components/admin/empty-state"
import { DeleteConfirmDialog } from "@/components/admin/delete-dialog"

export default function CategoriesContent() {
  const queryClient = useQueryClient()
  const [editItem, setEditItem] = useState<Category | null>(null)
  const [editName, setEditName] = useState("")
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")
  const [catSearch, setCatSearch] = useState("")

  const { data: categories, isLoading } = useQuery({
    queryKey: ["admin-categories"],
    queryFn: () => api.get<Category[]>("/categories"),
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => api.post("/admin/categories", { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-categories"] })
      toast.success("Category created")
      setShowCreate(false)
      setCreateName("")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      api.put(`/admin/categories/${id}`, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-categories"] })
      toast.success("Category updated")
      setEditItem(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/categories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-categories"] })
      toast.success("Category deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const cats = useMemo(() => {
    if (!categories) return []
    if (!catSearch.trim()) return categories
    return categories.filter((c) => c.name.toLowerCase().includes(catSearch.toLowerCase()))
  }, [categories, catSearch])

  return (
    <AdminPageShell title="Categories">
      <div className="flex items-center justify-between">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search categories..." value={catSearch} onChange={(e) => setCatSearch(e.target.value)} className="pl-9 h-9 text-sm" />
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}><Plus className="mr-1 h-4 w-4" /> Add Category</Button>
      </div>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Category</DialogTitle>
            <DialogDescription>Enter a name for the new category.</DialogDescription>
          </DialogHeader>
          <Input value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="Category name" />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={() => createMutation.mutate(createName)} disabled={!createName.trim() || createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {isLoading ? (
        <AdminTableSkeleton rows={5} />
      ) : cats.length === 0 ? (
        <AdminEmptyState label="categories" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {cats.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="text-muted-foreground">{c.id}</TableCell>
                <TableCell className="font-medium">{c.name}</TableCell>
                <TableCell className="flex gap-1 justify-end">
                  <Dialog open={editItem?.id === c.id} onOpenChange={(open) => { if (!open) setEditItem(null) }}>
                      <Button variant="ghost" size="icon" onClick={() => { setEditItem(c); setEditName(c.name) }}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Category</DialogTitle>
                        <DialogDescription>Rename &quot;{c.name}&quot;.</DialogDescription>
                      </DialogHeader>
                      <Input value={editName} onChange={(e) => setEditName(e.target.value)} />
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setEditItem(null)}>Cancel</Button>
                        <Button onClick={() => updateMutation.mutate({ id: c.id, name: editName })} disabled={!editName.trim() || updateMutation.isPending}>
                          {updateMutation.isPending ? "Saving..." : "Save"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <Button variant="ghost" size="icon" onClick={() => setDeleteId(c.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <DeleteConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => { if (!open) setDeleteId(null) }}
        title="Delete Category"
        description={deleteId ? `Delete category? This cannot be undone if products reference it.` : ""}
        onConfirm={() => deleteMutation.mutate(deleteId!)}
        disabled={deleteMutation.isPending}
      />
    </AdminPageShell>
  )
}
