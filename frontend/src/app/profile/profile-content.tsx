"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { User, Address } from "@/types/api"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import { useState, useEffect } from "react"
import { User as UserIcon, Save, Plus, Pencil, Trash2, CalendarIcon } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button, buttonVariants } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { format } from "date-fns"
import { toast } from "sonner"
import { INDIA_STATES, INDIA_LOCATIONS } from "@/lib/india-locations"

export default function ProfileContent() {
  const { isAuthenticated } = useAuthStore()
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
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [editingAddr, setEditingAddr] = useState<Address | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [form, setForm] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    phone: user?.phone || "",
    date_of_birth: user?.date_of_birth || "",
    gender: user?.gender || "",
  })

  const [newAddr, setNewAddr] = useState({
    label: "Home", street: "", city: "", state: "", pincode: "", country: "India",
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
      toast.success("Profile updated")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const createAddress = useMutation({
    mutationFn: () => api.post("/users/me/addresses", newAddr),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      toast.success("Address added")
      setShowAddForm(false)
      setNewAddr({ label: "Home", street: "", city: "", state: "", pincode: "", country: "India" })
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const updateAddress = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      api.put(`/users/me/addresses/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      toast.success("Address updated")
      setEditingAddr(null)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const deleteAddress = useMutation({
    mutationFn: (addrId: number) => api.delete(`/users/me/addresses/${addrId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      toast.success("Address deleted")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const p = profile || user
  const addresses = (p as User & { addresses?: Address[] })?.addresses || []

  const resetAddrForm = (addr?: Address) => {
    if (addr) {
      setNewAddr({ label: addr.label, street: addr.street, city: addr.city, state: addr.state, pincode: addr.pincode, country: addr.country || "India" })
    } else {
      setNewAddr({ label: "Home", street: "", city: "", state: "", pincode: "", country: "India" })
    }
  }

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
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium">First Name</label>
                <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Last Name</label>
                <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Email</label>
              <p className="py-2 text-sm text-muted-foreground">{p?.email}</p>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Phone</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Date of Birth</label>
                <div className="flex items-center gap-1">
                  {["DD", "MM", "YYYY"].map((placeholder, i) => {
                    const labels = ["day", "month", "year"]
                    const maxLen = [2, 2, 4]
                    return (
                      <input key={i} type="text" inputMode="numeric" maxLength={maxLen[i]} placeholder={placeholder}
                        value={form.date_of_birth ? (() => { const parts = form.date_of_birth.split("-"); return ["", undefined].includes(parts[i]) ? "" : parts[i] })() : ""}
                        onChange={(e) => {
                          const val = e.target.value.replace(/\D/g, "").slice(0, maxLen[i])
                          const parts = form.date_of_birth ? form.date_of_birth.split("-") : ["", "", ""]
                          parts[i] = val
                          setForm({ ...form, date_of_birth: parts.join("-") })
                          if (val.length === maxLen[i] && i < 2) {
                            const next = (e.target.parentElement?.children[i * 2 + 1] as HTMLElement) || (e.target.nextElementSibling?.nextElementSibling as HTMLElement)
                            setTimeout(() => next?.focus(), 10)
                          }
                        }}
                        className={`w-${i < 2 ? "12" : "14"} rounded border px-2 py-2 text-sm text-center outline-none focus:border-amazon-link dark:border-border dark:bg-card`}
                      />
                    )
                  })}
                  <Popover>
                    <PopoverTrigger className="flex h-8 w-8 items-center justify-center text-muted-foreground hover:text-foreground rounded-md hover:bg-accent shrink-0">
                      <CalendarIcon className="h-4 w-4" />
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="end">
                      <Calendar mode="single"
                        selected={form.date_of_birth && /^\d{4}-\d{2}-\d{2}$/.test(form.date_of_birth) ? new Date(form.date_of_birth + "T00:00:00") : undefined}
                        onSelect={(date) => { if (date) setForm({ ...form, date_of_birth: format(date, "yyyy-MM-dd") }) }}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Gender</label>
                <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card">
                  <option value="">Select</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="unspecified">Prefer not to say</option>
                </select>
              </div>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">Email Verified</p>
              <p className="text-sm font-medium">{p?.is_verified ? "Yes" : "No"}</p>
            </div>

            <div className="flex gap-3">
              <button type="button" onClick={() => updateProfile.mutate()} disabled={updateProfile.isPending}
                className="flex items-center gap-1 rounded bg-amazon-link px-4 py-2 text-sm font-medium text-white hover:brightness-95 disabled:opacity-50">
                <Save className="h-4 w-4" /> {updateProfile.isPending ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>

        {/* Addresses */}
        <div className="mt-6 rounded-lg border bg-white p-6 dark:border-border dark:bg-card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold">Addresses</h2>
            {!showAddForm && (
              <button onClick={() => { setShowAddForm(true); resetAddrForm() }}
                className="flex items-center gap-1 rounded bg-amazon-link px-3 py-1.5 text-sm font-medium text-white hover:brightness-95">
                <Plus className="h-4 w-4" /> Add Address
              </button>
            )}
          </div>

          {/* Add/Edit form */}
          {(showAddForm || editingAddr) && (
            <div className="mb-4 space-y-3 rounded-lg border bg-muted/50 p-4">
              <input placeholder="Label (Home/Work)" value={newAddr.label} onChange={(e) => setNewAddr({ ...newAddr, label: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              <input placeholder="Street address" value={newAddr.street} onChange={(e) => setNewAddr({ ...newAddr, street: e.target.value })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              <div className="grid grid-cols-2 gap-3">
                <select value={newAddr.city} onChange={(e) => setNewAddr({ ...newAddr, city: e.target.value })} disabled={!newAddr.state} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card disabled:opacity-50 disabled:cursor-not-allowed">
                  <option value="">{newAddr.state ? "Select city" : "Select state first"}</option>
                  {newAddr.state && INDIA_LOCATIONS[newAddr.state]?.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <select value={newAddr.state} onChange={(e) => { setNewAddr({ ...newAddr, state: e.target.value, city: '' }) }} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card">
                  <option value="">State</option>
                  {INDIA_STATES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <input placeholder="Pincode" inputMode="numeric" maxLength={6} value={newAddr.pincode} onChange={(e) => setNewAddr({ ...newAddr, pincode: e.target.value.replace(/\D/g, '') })} className="w-full rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              <div className="flex gap-2">
                <button type="button"
                  onClick={() => editingAddr ? updateAddress.mutate({ id: editingAddr.id, data: newAddr }) : createAddress.mutate()}
                  disabled={createAddress.isPending || updateAddress.isPending || !newAddr.street || !newAddr.city || !newAddr.state || newAddr.pincode.length !== 6}
                  className="rounded bg-amazon-link px-4 py-2 text-sm font-medium text-white hover:brightness-95 disabled:opacity-50">
                  {createAddress.isPending || updateAddress.isPending ? "Saving..." : "Save Address"}
                </button>
                <button type="button" onClick={() => { setShowAddForm(false); setEditingAddr(null) }} className="rounded border px-4 py-2 text-sm dark:border-border">
                  Cancel
                </button>
              </div>
            </div>
          )}

          {addresses.length === 0 ? (
            <p className="text-sm text-muted-foreground">No addresses saved.</p>
          ) : (
            <div className="space-y-2">
              {addresses.map((addr) => (
                <div key={addr.id} className="flex items-start justify-between rounded-md border bg-muted/50 p-3 text-sm dark:border-border">
                  <div>
                    <p className="font-medium">{addr.label}</p>
                    <p className="text-muted-foreground">{addr.street}, {addr.city}, {addr.state} {addr.pincode}</p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button onClick={() => { setEditingAddr(addr); resetAddrForm(addr); setShowAddForm(false) }} className="p-1 text-muted-foreground hover:text-foreground"><Pencil className="h-4 w-4" /></button>
                    <Dialog>
                      <DialogTrigger className="p-1 text-destructive"><Trash2 className="h-4 w-4" /></DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete Address</DialogTitle>
                          <DialogDescription>Are you sure you want to delete this address?</DialogDescription>
                        </DialogHeader>
                        <div className="flex justify-end gap-3">
                          <button type="button" className={buttonVariants({ variant: "outline" })} onClick={() => {}}>Cancel</button>
                          <Button variant="destructive" onClick={() => { deleteAddress.mutate(addr.id); setDeletingId(addr.id) }} disabled={deleteAddress.isPending && deletingId === addr.id}>
                            Delete
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}
