"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Cart } from "@/types/api"
import Link from "next/link"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Trash2, Minus, Plus, ShoppingBag, ArrowLeft } from "lucide-react"
import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { useState } from "react"

export default function CartPage() {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()
  const queryClient = useQueryClient()

  if (!isAuthenticated) {
    router.push("/auth/login")
    return null
  }

  return <CartContent />
}

function CartContent() {
  const queryClient = useQueryClient()

  const { data: cart, isLoading } = useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/cart"),
  })

  const updateQty = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: number; quantity: number }) =>
      api.put(`/cart/items/${itemId}`, { quantity }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
    onError: (err: Error) => toast.error(err.message),
  })

  const removeItem = useMutation({
    mutationFn: (itemId: number) => api.delete(`/cart/items/${itemId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
    onError: (err: Error) => toast.error(err.message),
  })

  const clearCart = useMutation({
    mutationFn: () => api.delete("/cart"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
    onError: (err: Error) => toast.error(err.message),
  })

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="animate-pulse space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    )
  }

  const items = cart?.items ?? []

  if (items.length === 0) {
    return (
      <div className="mx-auto flex max-w-4xl flex-col items-center justify-center px-4 py-20 text-center">
        <ShoppingBag className="mb-4 h-16 w-16 text-muted-foreground" />
        <h1 className="mb-2 text-2xl font-bold">Your cart is empty</h1>
        <p className="mb-8 text-muted-foreground">Looks like you haven&apos;t added anything to your cart yet.</p>
        <Link href="/products" className={buttonVariants()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Continue Shopping
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Shopping Cart ({items.length} items)</h1>
        <Button variant="outline" size="sm" onClick={() => clearCart.mutate()} disabled={clearCart.isPending}>
          <Trash2 className="mr-2 h-4 w-4" />
          Clear Cart
        </Button>
      </div>

      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="flex gap-4 rounded-lg border p-4">
            <Link href={`/products/${item.product.id}`} className="h-24 w-24 flex-shrink-0 overflow-hidden rounded-md bg-muted">
              <img
                src={item.product.thumbnail || "/placeholder.svg"}
                alt={item.product.title}
                className="h-full w-full object-cover"
              />
            </Link>
            <div className="flex flex-1 flex-col justify-between">
              <div>
                <Link href={`/products/${item.product.id}`} className="font-medium hover:underline">
                  {item.product.title}
                </Link>
                <p className="text-sm text-muted-foreground">₹{item.product.price.toFixed(2)} each</p>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center rounded-md border">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 rounded-none"
                    onClick={() => updateQty.mutate({ itemId: item.id, quantity: Math.max(1, item.quantity - 1) })}
                    disabled={item.quantity <= 1}
                  >
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="flex h-8 w-10 items-center justify-center text-sm tabular-nums">{item.quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 rounded-none"
                    onClick={() =>
                      updateQty.mutate({
                        itemId: item.id,
                        quantity: Math.min(item.product.stock, item.quantity + 1),
                      })
                    }
                    disabled={item.quantity >= item.product.stock}
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-semibold">₹{(item.product.price * item.quantity).toFixed(2)}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive"
                    onClick={() => removeItem.mutate(item.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Separator className="my-6" />

      <div className="flex flex-col items-end gap-4">
        <div className="w-full max-w-xs space-y-2">
          <div className="flex justify-between text-lg font-semibold">
            <span>Total</span>
            <span>₹{cart?.total.toFixed(2)}</span>
          </div>
        </div>
        <div className="flex gap-3">
          <Link href="/products" className={buttonVariants({ variant: "outline" })}>
            Continue Shopping
          </Link>
          <Link href="/checkout" className={buttonVariants()}>
            Proceed to Checkout
          </Link>
        </div>
      </div>
    </div>
  )
}
