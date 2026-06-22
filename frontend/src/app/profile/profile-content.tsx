"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { User } from "@/types/api"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import { useState, useEffect } from "react"
import { User as UserIcon, Save } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { toast } from "sonner"

export default function ProfileContent() {
  const { isAuthenticated, user } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return <ProfileInner />
}

function ProfileInner() {
  const { user, login } = useAuthStore()
  const queryClient = useQueryClient()
  const router = useRouter()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    phone: user?.phone || "",
  })

  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: () => api.get<User>("/auth/users/me"),
  })

  const updateProfile = useMutation({
    mutationFn: () => api.put<User>("/auth/users/me", form),
    onSuccess: (data) => {
      login(useAuthStore.getState().token!, data)
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      setEditing(false)
      toast.success("Profile updated")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const p = profile || user

  return (
    <Shell>
      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amazon-nav text-white">
            <UserIcon className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Your Profile</h1>
            <p className="text-sm text-muted-foreground">{p?.email}</p>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-6 dark:border-border dark:bg-card">
          {editing ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium">First Name</label>
                  <input
                    value={form.first_name}
                    onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                    className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Last Name</label>
                  <input
                    value={form.last_name}
                    onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                    className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Phone</label>
                <input
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => updateProfile.mutate()}
                  disabled={updateProfile.isPending}
                  className="flex items-center gap-1 rounded bg-amazon-link px-4 py-2 text-sm font-medium text-white hover:brightness-95 disabled:opacity-50"
                >
                  <Save className="h-4 w-4" /> Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="rounded border px-4 py-2 text-sm dark:border-border"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">First Name</p>
                  <p className="text-sm font-medium">{p?.first_name || "-"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Last Name</p>
                  <p className="text-sm font-medium">{p?.last_name || "-"}</p>
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="text-sm font-medium">{p?.email}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Phone</p>
                <p className="text-sm font-medium">{p?.phone || "-"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Role</p>
                <p className="text-sm font-medium capitalize">{p?.role}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setForm({ first_name: p?.first_name || "", last_name: p?.last_name || "", phone: p?.phone || "" })
                  setEditing(true)
                }}
                className="rounded bg-amazon-cart px-4 py-2 text-sm font-semibold text-black hover:brightness-95"
              >
                Edit Profile
              </button>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}
