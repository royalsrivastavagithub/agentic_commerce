"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Order } from "@/types/api"
import { useParams, useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"
import Link from "next/link"
import { ArrowLeft, Package } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { toast } from "sonner"

export default function OrderDetailContent() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()

  if (!isAuthenticated) {
    router.push("/auth/login")
    return null
  }

  return <OrderDetailInner />
}

function OrderDetailInner() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const router = useRouter()

  const { data: order, isLoading } = useQuery({
    queryKey: ["order", id],
    queryFn: () => api.get<Order>(`/orders/${id}`),
  })

  const cancelOrder = useMutation({
    mutationFn: () => api.put(`/orders/${id}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", id] })
      queryClient.invalidateQueries({ queryKey: ["orders"] })
      toast.success("Order cancelled")
    },
  })

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    confirmed: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    shipped: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    delivered: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    cancelled: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  }

  if (isLoading) {
    return (
      <Shell>
        <div className="mx-auto max-w-4xl px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-6 w-48 rounded bg-gray-200 dark:bg-muted" />
            <div className="h-40 rounded-lg bg-gray-200 dark:bg-muted" />
            <div className="h-32 rounded-lg bg-gray-200 dark:bg-muted" />
          </div>
        </div>
      </Shell>
    )
  }

  if (!order) {
    return (
      <Shell>
        <div className="mx-auto flex max-w-4xl flex-col items-center px-4 py-20 text-center">
          <Package className="mb-4 h-16 w-16 text-gray-300" />
          <h1 className="mb-2 text-2xl font-bold">Order not found</h1>
          <Link href="/orders" className="text-sm text-amazon-link hover:underline">Back to orders</Link>
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <Link href="/orders" className="mb-4 flex items-center gap-1 text-sm text-amazon-link hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to orders
        </Link>

        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Order #{order.id}</h1>
            <p className="text-sm text-muted-foreground">
              Placed on {new Date(order.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-sm font-medium capitalize ${statusColors[order.status] || "bg-gray-100 text-gray-800"}`}>
            {order.status}
          </span>
        </div>

        <div className="mb-6 rounded-lg border bg-white p-4 dark:border-border dark:bg-card">
          <h2 className="mb-3 text-base font-semibold">Shipping Address</h2>
          <p className="text-sm">{order.shipping_name}</p>
          <p className="text-sm text-muted-foreground">{order.shipping_phone}</p>
          <p className="text-sm text-muted-foreground">{order.shipping_address_line_1}</p>
          {order.shipping_address_line_2 && <p className="text-sm text-muted-foreground">{order.shipping_address_line_2}</p>}
          <p className="text-sm text-muted-foreground">{order.shipping_city}, {order.shipping_state} {order.shipping_pincode}</p>
        </div>

        <div className="mb-6 rounded-lg border bg-white dark:border-border dark:bg-card">
          <div className="border-b px-4 py-3">
            <h2 className="text-base font-semibold">Order Items ({order.items.length})</h2>
          </div>
          <div className="divide-y">
            {order.items.map((item) => (
              <div key={item.id} className="flex items-center gap-4 px-4 py-3">
                <div className="h-16 w-16 shrink-0 overflow-hidden rounded-md bg-muted">
                  <img src="/placeholder.svg" alt={item.product_name} className="h-full w-full object-cover" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.product_name}</p>
                  <p className="text-xs text-muted-foreground">Qty: {item.quantity} × ₹{item.product_price.toFixed(2)}</p>
                </div>
                <p className="text-sm font-semibold">₹{item.subtotal.toFixed(2)}</p>
              </div>
            ))}
          </div>
          <div className="border-t px-4 py-3">
            <div className="flex justify-between text-base font-semibold">
              <span>Total</span>
              <span>₹{order.total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {order.razorpay_order_id && (
          <div className="mb-6 rounded-lg border bg-white p-4 text-sm dark:border-border dark:bg-card">
            <h2 className="mb-2 text-base font-semibold">Payment</h2>
            <p className="text-muted-foreground">Payment Status: <span className="font-medium text-foreground capitalize">{order.payment_status || "Pending"}</span></p>
            {order.razorpay_payment_id && <p className="text-muted-foreground">Payment ID: {order.razorpay_payment_id}</p>}
          </div>
        )}

        {order.status === "pending" && (
          <button
            type="button"
            onClick={() => cancelOrder.mutate()}
            disabled={cancelOrder.isPending}
            className="rounded-lg border border-destructive px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/5 disabled:opacity-50"
          >
            Cancel Order
          </button>
        )}
      </div>
    </Shell>
  )
}
