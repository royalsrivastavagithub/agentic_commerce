"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Order } from "@/types/api"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Package } from "lucide-react"
import { useEffect } from "react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"

export default function OrdersContent() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return <OrdersInner />
}

function OrdersInner() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ["orders"],
    queryFn: () => api.get<Order[]>("/orders"),
  })

  if (isLoading) {
    return (
      <Shell>
        <div className="mx-auto max-w-4xl px-4 py-8">
          <div className="animate-pulse space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-28 rounded-lg bg-gray-200 dark:bg-muted" />
            ))}
          </div>
        </div>
      </Shell>
    )
  }

  if (!orders?.length) {
    return (
      <Shell>
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-center px-4 py-20 text-center">
          <Package className="mb-4 h-16 w-16 text-gray-300 dark:text-muted-foreground" />
          <h1 className="mb-2 text-2xl font-bold">Your Orders</h1>
          <p className="mb-8 text-muted-foreground">You haven&apos;t placed any orders yet.</p>
          <Link
            href="/products"
            className="rounded-md bg-amazon-accent px-6 py-2 text-sm font-semibold text-amazon-nav hover:brightness-95"
          >
            Start Shopping
          </Link>
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-6 text-2xl font-bold">Your Orders</h1>
        <div className="space-y-4">
          {orders.map((order) => (
            <Link
              key={order.id}
              href={`/orders/${order.id}`}
              className="block rounded-lg border bg-white p-4 transition-shadow hover:shadow dark:border-border dark:bg-card"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>
                    ORDER PLACED: {new Date(order.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </span>
                  <span>TOTAL: ₹{order.total.toFixed(2)}</span>
                </div>

              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {order.items.slice(0, 3).map((item) => (
                    <div key={item.id} className="h-14 w-14 shrink-0 overflow-hidden rounded-md bg-muted">
                      <img src={item.thumbnail || "/placeholder.svg"} alt={item.product_name} className="h-full w-full object-cover" />
                    </div>
                  ))}
                  {order.items.length > 3 && (
                    <div className="flex h-14 w-14 items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">
                      +{order.items.length - 3}
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Shell>
  )
}
