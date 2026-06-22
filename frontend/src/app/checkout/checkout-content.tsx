"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Address, Cart, CreatePaymentResponse } from "@/types/api"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useState, useEffect } from "react"
import { ArrowLeft, MapPin, Plus } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { toast } from "sonner"

interface NewAddress {
  label: string
  street: string
  city: string
  state: string
  pincode: string
  country: string
}

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open: () => void }
  }
}

function loadRazorpayScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window !== "undefined" && (window as any).Razorpay) { resolve(); return }
    const script = document.createElement("script")
    script.src = "https://checkout.razorpay.com/v1/checkout.js"
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error("Failed to load Razorpay"))
    document.body.appendChild(script)
  })
}

export default function CheckoutContent() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return <CheckoutInner />
}

function CheckoutInner() {
  const queryClient = useQueryClient()
  const router = useRouter()
  const [selectedAddress, setSelectedAddress] = useState<number | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newAddr, setNewAddr] = useState<NewAddress>({
    label: "Home", street: "", city: "", state: "", pincode: "", country: "India",
  })

  const { data: addresses, isLoading: addrLoading } = useQuery({
    queryKey: ["addresses"],
    queryFn: () => api.get<Address[]>("/users/me/addresses"),
  })

  const { data: cart, isLoading: cartLoading } = useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/cart"),
  })

  const addAddress = useMutation({
    mutationFn: () => api.post("/users/me/addresses", newAddr),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["addresses"] })
      setShowAddForm(false)
      setNewAddr({ label: "Home", street: "", city: "", state: "", pincode: "", country: "India" })
      toast.success("Address added")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const createPayment = useMutation({
    mutationFn: () => api.post<CreatePaymentResponse>("/orders/create-payment", { address_id: selectedAddress }),
    onSuccess: async (data) => {
      try {
        await loadRazorpayScript()
      } catch {
        toast.error("Failed to load payment gateway")
        return
      }

      const options = {
        key: data.razorpay_key_id,
        amount: data.amount * 100,
        currency: data.currency,
        name: "Agentic Commerce",
        order_id: data.razorpay_order_id,
        handler: async (response: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) => {
          try {
            await api.post("/orders/verify-payment", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            })
            queryClient.invalidateQueries({ queryKey: ["cart"] })
            toast.success("Payment successful!")
            router.push(`/orders/${data.order_id}`)
          } catch {
            toast.error("Payment verification failed")
          }
        },
        modal: {
          ondismiss: () => toast.error("Payment cancelled"),
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.open()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  useEffect(() => {
    if (addresses?.length && !selectedAddress) {
      const def = addresses.find((a) => a.is_default)
      setSelectedAddress(def?.id ?? addresses[0].id)
    }
  }, [addresses, selectedAddress])

  const isLoading = addrLoading || cartLoading

  if (isLoading) {
    return (
      <Shell>
        <div className="mx-auto max-w-4xl px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-6 w-48 rounded bg-gray-200 dark:bg-muted" />
            <div className="h-32 rounded-lg bg-gray-200 dark:bg-muted" />
            <div className="h-40 rounded-lg bg-gray-200 dark:bg-muted" />
          </div>
        </div>
      </Shell>
    )
  }

  const items = cart?.items ?? []
  const addrList = addresses ?? []

  return (
    <Shell>
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <Link href="/cart" className="mb-4 flex items-center gap-1 text-sm text-amazon-link hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to cart
        </Link>

        <h1 className="mb-6 text-2xl font-bold">Checkout</h1>

        <div className="mb-6 rounded-lg border bg-white p-4 dark:border-border dark:bg-card">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-base font-semibold">
              <MapPin className="h-4 w-4" /> Shipping Address
            </h2>
            <button
              type="button"
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center gap-1 text-sm text-amazon-link hover:underline"
            >
              <Plus className="h-3.5 w-3.5" /> {showAddForm ? "Cancel" : "Add New"}
            </button>
          </div>

          {showAddForm && (
            <div className="mb-4 space-y-3 rounded-lg border bg-muted/50 p-4">
              <div className="grid grid-cols-2 gap-3">
                <input placeholder="Label (Home/Work)" value={newAddr.label} onChange={(e) => setNewAddr({ ...newAddr, label: e.target.value })} className="col-span-2 rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
                <input placeholder="Street address" value={newAddr.street} onChange={(e) => setNewAddr({ ...newAddr, street: e.target.value })} className="col-span-2 rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
                <input placeholder="City" value={newAddr.city} onChange={(e) => setNewAddr({ ...newAddr, city: e.target.value })} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
                <input placeholder="State" value={newAddr.state} onChange={(e) => setNewAddr({ ...newAddr, state: e.target.value })} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
                <input placeholder="Pincode" value={newAddr.pincode} onChange={(e) => setNewAddr({ ...newAddr, pincode: e.target.value })} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
                <input placeholder="Country" value={newAddr.country} onChange={(e) => setNewAddr({ ...newAddr, country: e.target.value })} className="rounded border px-3 py-2 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card" />
              </div>
              <button
                type="button"
                onClick={() => addAddress.mutate()}
                disabled={addAddress.isPending || !newAddr.street || !newAddr.city || !newAddr.state || !newAddr.pincode}
                className="rounded bg-amazon-link px-4 py-2 text-sm font-medium text-white hover:brightness-95 disabled:opacity-50"
              >
                Save Address
              </button>
            </div>
          )}

          {addrList.length === 0 && !showAddForm ? (
            <p className="text-sm text-muted-foreground">No addresses saved. Please add one.</p>
          ) : (
            <div className="space-y-2">
              {addrList.map((addr) => (
                <label
                  key={addr.id}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${
                    selectedAddress === addr.id ? "border-amazon-link bg-amazon-link/5" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="address"
                    checked={selectedAddress === addr.id}
                    onChange={() => setSelectedAddress(addr.id)}
                    className="mt-1"
                  />
                  <div className="text-sm">
                    <p className="font-medium">{addr.label}</p>
                    <p className="text-muted-foreground">{addr.street}, {addr.city}, {addr.state} {addr.pincode}</p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="mb-6 rounded-lg border bg-white dark:border-border dark:bg-card">
          <div className="border-b px-4 py-3">
            <h2 className="text-base font-semibold">Order Summary ({items.length} items)</h2>
          </div>
          <div className="divide-y">
            {items.map((item) => (
              <div key={item.id} className="flex items-center gap-4 px-4 py-3">
                <div className="h-16 w-16 shrink-0 overflow-hidden rounded-md bg-muted">
                  <img src={item.product.thumbnail || "/placeholder.svg"} alt={item.product.title} className="h-full w-full object-cover" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.product.title}</p>
                  <p className="text-xs text-muted-foreground">Qty: {item.quantity} × ₹{item.product.price.toFixed(2)}</p>
                </div>
                <p className="text-sm font-semibold">₹{(item.product.price * item.quantity).toFixed(2)}</p>
              </div>
            ))}
          </div>
          <div className="border-t px-4 py-3">
            <div className="flex justify-between text-base font-semibold">
              <span>Total</span>
              <span>₹{cart?.total.toFixed(2) ?? "0.00"}</span>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => createPayment.mutate()}
            disabled={createPayment.isPending || !selectedAddress || items.length === 0 || addrList.length === 0}
            className="rounded-full bg-amazon-cart px-8 py-3 text-base font-semibold text-black shadow-sm hover:brightness-95 disabled:opacity-50"
          >
            {createPayment.isPending ? "Processing..." : "Place Order"}
          </button>
        </div>
      </div>
    </Shell>
  )
}
