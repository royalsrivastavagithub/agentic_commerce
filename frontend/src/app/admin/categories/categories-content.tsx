"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Category } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState } from "react"
import { Pencil, Trash2, Plus } from "lucide-react"

export default function CategoriesContent() {
  const queryClient = useQueryClient()
  const [editItem, setEditItem] = useState<Category | null>(null)
  const [editName, setEditName] = useState("")
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createName, setCreateName] = useState("")

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

  const cats = categories || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Categories</h1>
        <Button size="sm" onClick={() => setShowCreate(true)}><Plus className="mr-1 h-4 w-4" /> Add Category</Button>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Category</DialogTitle>
              <DialogDescription>Enter a name for the new category.</DialogDescription>
            </DialogHeader>
            <Input value={createName} onChange={(e) => setCreateName(e.target.value)} placeholder="Category name" />
            <DialogFooter>
              <DialogClose><Button variant="outline">Cancel</Button></DialogClose>
              <Button onClick={() => createMutation.mutate(createName)} disabled={!createName.trim() || createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      ) : cats.length === 0 ? (
        <p className="text-sm text-muted-foreground">No categories found.</p>
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
                    <DialogTrigger>
                      <Button variant="ghost" size="icon" onClick={() => { setEditItem(c); setEditName(c.name) }}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Category</DialogTitle>
                        <DialogDescription>Rename &quot;{c.name}&quot;.</DialogDescription>
                      </DialogHeader>
                      <Input value={editName} onChange={(e) => setEditName(e.target.value)} />
                      <DialogFooter>
                        <DialogClose><Button variant="outline">Cancel</Button></DialogClose>
                        <Button onClick={() => updateMutation.mutate({ id: c.id, name: editName })} disabled={!editName.trim() || updateMutation.isPending}>
                          {updateMutation.isPending ? "Saving..." : "Save"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <Dialog open={deleteId === c.id} onOpenChange={(open) => { if (!open) setDeleteId(null) }}>
                    <DialogTrigger>
                      <Button variant="ghost" size="icon" onClick={() => setDeleteId(c.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Delete Category</DialogTitle>
                        <DialogDescription>Delete &quot;{c.name}&quot;? This cannot be undone if products reference it.</DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <DialogClose><Button variant="outline">Cancel</Button></DialogClose>
                        <Button variant="destructive" onClick={() => deleteMutation.mutate(c.id)} disabled={deleteMutation.isPending}>
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
