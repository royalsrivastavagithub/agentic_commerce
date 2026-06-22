"use client"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { WishlistItem } from "@/types/api"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Heart, ShoppingCart, Trash2 } from "lucide-react"
import { useEffect } from "react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { toast } from "sonner"

export default function WishlistContent() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login")
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return <WishlistInner />
}

function WishlistInner() {
  const queryClient = useQueryClient()
  const router = useRouter()

  const { data: items, isLoading } = useQuery({
    queryKey: ["wishlist"],
    queryFn: () => api.get<WishlistItem[]>("/wishlist"),
  })

  const removeItem = useMutation({
    mutationFn: (itemId: number) => api.delete(`/wishlist/${itemId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] })
      toast.success("Removed from wishlist")
    },
  })

  const addToCart = useMutation({
    mutationFn: (productId: number) => api.post("/cart/items", { product_id: productId, quantity: 1 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
      toast.success("Added to cart")
    },
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

  if (!items?.length) {
    return (
      <Shell>
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-center px-4 py-20 text-center">
          <Heart className="mb-4 h-16 w-16 text-gray-300" />
          <h1 className="mb-2 text-2xl font-bold">Your Wishlist</h1>
          <p className="mb-8 text-muted-foreground">Your wishlist is empty.</p>
          <Link
            href="/products"
            className="rounded-full bg-amazon-accent px-6 py-2 text-sm font-semibold text-amazon-nav hover:brightness-95"
          >
            Browse Products
          </Link>
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-6 text-2xl font-bold">Your Wishlist ({items.length})</h1>
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex gap-4 rounded-lg border bg-white p-3 dark:border-border dark:bg-card"
            >
              <Link href={`/products/${item.product.id}`} className="h-24 w-24 shrink-0 overflow-hidden rounded-md bg-white dark:bg-card">
                <img
                  src={item.product.thumbnail || "/placeholder.svg"}
                  alt={item.product.title}
                  className="h-full w-full object-contain"
                />
              </Link>
              <div className="flex flex-1 flex-col justify-between py-1">
                <Link href={`/products/${item.product.id}`}>
                  <h3 className="text-base font-medium text-foreground hover:text-amazon-link hover:underline">{item.product.title}</h3>
                </Link>
                <p className="text-sm text-muted-foreground">{item.product.brand}</p>
                <p className="text-lg font-bold">₹{item.product.price.toFixed(2)}</p>
              </div>
              <div className="flex flex-col items-end justify-center gap-2">
                <button
                  type="button"
                  onClick={() => addToCart.mutate(item.product.id)}
                  disabled={addToCart.isPending}
                  className="flex items-center gap-1 rounded bg-amazon-cart px-3 py-1.5 text-xs font-semibold text-black hover:brightness-95 disabled:opacity-50"
                >
                  <ShoppingCart className="h-3.5 w-3.5" />
                  Add to Cart
                </button>
                <button
                  type="button"
                  onClick={() => removeItem.mutate(item.id)}
                  disabled={removeItem.isPending}
                  className="flex items-center gap-1 text-xs text-destructive hover:underline"
                >
                  <Trash2 className="h-3 w-3" />
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  )
}
