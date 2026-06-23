"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { AdminUserResponse, AdminUsersResponse } from "@/types/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"
import { useState } from "react"
import { Shield, Trash2 } from "lucide-react"
import { AdminPageShell } from "@/components/admin/page-shell"
import { AdminSearchInput } from "@/components/admin/search-input"
import { AdminTableSkeleton } from "@/components/admin/table-skeleton"
import { AdminEmptyState } from "@/components/admin/empty-state"
import { AdminPagination } from "@/components/admin/pagination"
import { DeleteConfirmDialog } from "@/components/admin/delete-dialog"

export default function UsersContent() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [editUser, setEditUser] = useState<AdminUserResponse | null>(null)
  const [editRole, setEditRole] = useState("user")
  const [editActive, setEditActive] = useState(true)
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", search, page],
    queryFn: () => api.get<AdminUsersResponse>(`/admin/users?search=${encodeURIComponent(search)}&page=${page}&per_page=20`),
  })

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      api.patch(`/admin/users/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      toast.success("User updated")
      setEditUser(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] })
      toast.success("User deleted")
      setDeleteId(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const users = data?.users || []
  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1

  return (
    <AdminPageShell title="Users">
      <AdminSearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search users..." />

      {isLoading ? (
        <AdminTableSkeleton rows={5} />
      ) : users.length === 0 ? (
        <AdminEmptyState label="users" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Active</TableHead>
              <TableHead className="text-right">Orders</TableHead>
              <TableHead className="text-right">Spent</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="text-muted-foreground">{u.id}</TableCell>
                <TableCell className="font-medium">{u.email}</TableCell>
                <TableCell className="text-muted-foreground">{[u.first_name, u.last_name].filter(Boolean).join(" ") || "—"}</TableCell>
                <TableCell>
                  <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${u.role === "admin" ? "bg-purple-100 text-purple-800" : "bg-gray-100 text-gray-800"}`}>
                    {u.role}
                  </span>
                </TableCell>
                <TableCell>{u.is_active ? <span className="text-green-600">Yes</span> : <span className="text-red-600">No</span>}</TableCell>
                <TableCell className="text-right">{u.order_count}</TableCell>
                <TableCell className="text-right">₹{u.total_spent.toFixed(2)}</TableCell>
                <TableCell className="flex gap-1">
                  <Dialog open={editUser?.id === u.id} onOpenChange={(open) => { if (!open) setEditUser(null) }}>
                      <Button variant="ghost" size="icon" onClick={() => { setEditUser(u); setEditRole(u.role); setEditActive(u.is_active) }}>
                        <Shield className="h-4 w-4" />
                      </Button>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit User — {u.email}</DialogTitle>
                        <DialogDescription>Change role or account status.</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-2">
                        <div>
                          <label className="text-sm font-medium">Role</label>
                          <select
                            value={editRole}
                            onChange={(e) => setEditRole(e.target.value)}
                            className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none"
                          >
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                          </select>
                        </div>
                        <div className="flex items-center gap-2">
                          <input type="checkbox" id="active" checked={editActive} onChange={(e) => setEditActive(e.target.checked)} />
                          <label htmlFor="active" className="text-sm font-medium">Active</label>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setEditUser(null)}>Cancel</Button>
                        <Button onClick={() => editMutation.mutate({ id: u.id, data: { role: editRole, is_active: editActive } })} disabled={editMutation.isPending}>
                          {editMutation.isPending ? "Saving..." : "Save"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <Button variant="ghost" size="icon" onClick={() => setDeleteId(u.id)}>
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
        title="Delete User"
        description={deleteId ? `Delete user #${deleteId}? This cannot be undone.` : ""}
        onConfirm={() => deleteMutation.mutate(deleteId!)}
        disabled={deleteMutation.isPending}
      />
    </AdminPageShell>
  )
}
