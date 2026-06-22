"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, Review } from "@/types/api"
import { useParams } from "next/navigation"
import { Button, buttonVariants } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Star, ShoppingCart, Heart, Minus, Plus } from "lucide-react"
import { useAuthStore } from "@/stores/auth-store"
import { useCartStore } from "@/stores/cart-store"
import { toast } from "sonner"
import { useState } from "react"
import Link from "next/link"
import { Shell } from "@/components/features/shell"

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuthStore()
  const { openCart } = useCartStore()
  const queryClient = useQueryClient()
  const [quantity, setQuantity] = useState(1)

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", id],
    queryFn: () => api.get<Product>(`/products/${id}`),
  })

  const addToCart = useMutation({
    mutationFn: () => api.post("/cart/items", { product_id: Number(id), quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
      toast.success("Added to cart")
      openCart()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const addToWishlist = useMutation({
    mutationFn: () => api.post("/wishlist", { product_id: Number(id) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] })
      toast.success("Added to wishlist")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  if (isLoading) {
    return (
      <Shell>
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-2">
            <div className="aspect-square animate-pulse rounded-lg bg-muted" />
            <div className="space-y-4">
              <div className="h-8 w-3/4 animate-pulse rounded bg-muted" />
              <div className="h-6 w-1/4 animate-pulse rounded bg-muted" />
              <div className="h-20 animate-pulse rounded bg-muted" />
            </div>
          </div>
        </div>
      </Shell>
    )
  }

  if (!product) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-lg text-muted-foreground">Product not found</p>
          <Link href="/products" className={buttonVariants({ variant: "link" })}>
            Back to products
          </Link>
        </div>
      </Shell>
    )
  }

  const discounted = product.price * (1 - (product.discount_percentage || 0) / 100)

  return (
    <Shell>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="overflow-hidden rounded-lg border bg-muted">
              <img
                src={product.thumbnail || "/placeholder.svg"}
                alt={product.title}
                className="h-full w-full object-cover"
              />
            </div>
            {product.images?.length > 1 && (
              <div className="flex gap-2 overflow-auto">
                {product.images.map((img, i) => (
                  <div key={i} className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-md border bg-muted">
                    <img src={img || "/placeholder.svg"} alt="" className="h-full w-full object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div>
              <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                {product.category && (
                  <Link href={`/categories/${product.category}`} className="hover:underline">
                    {product.category}
                  </Link>
                )}
                {product.brand && <span>| {product.brand}</span>}
                <span>| SKU: {product.sku}</span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight">{product.title}</h1>
              <div className="mt-2 flex items-center gap-2">
                <div className="flex items-center">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"}`}
                    />
                  ))}
                </div>
                <span className="text-sm text-muted-foreground">
                  {product.rating.toFixed(1)} ({product.review_count} reviews)
                </span>
              </div>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">₹{discounted.toFixed(2)}</span>
              {product.discount_percentage > 0 && (
                <>
                  <span className="text-lg text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
                  <Badge variant="secondary">-{product.discount_percentage}%</Badge>
                </>
              )}
            </div>

            <p className="text-muted-foreground">{product.description}</p>

            <div className="space-y-2 text-sm">
              <p>
                <span className="font-medium">Availability:</span>{" "}
                {product.stock > 0 ? (
                  <span className="text-green-600">{product.availability_status}</span>
                ) : (
                  <span className="text-destructive">Out of stock</span>
                )}
              </p>
              <p>
                <span className="font-medium">Shipping:</span> {product.shipping_information}
              </p>
              <p>
                <span className="font-medium">Warranty:</span> {product.warranty_information}
              </p>
              <p>
                <span className="font-medium">Return Policy:</span> {product.return_policy}
              </p>
              <p>
                <span className="font-medium">Min Order:</span> {product.minimum_order_quantity}
              </p>
            </div>

            {product.stock > 0 && (
              <div className="flex items-center gap-4">
                <div className="flex items-center rounded-md border">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-10 w-10 rounded-none"
                    onClick={() => setQuantity((q) => Math.max(product.minimum_order_quantity, q - 1))}
                    disabled={quantity <= product.minimum_order_quantity}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="flex h-10 w-14 items-center justify-center text-sm font-medium tabular-nums">
                    {quantity}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-10 w-10 rounded-none"
                    onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))}
                    disabled={quantity >= product.stock}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              {isAuthenticated ? (
                <>
                  <Button
                    size="lg"
                    className="flex-1"
                    disabled={product.stock === 0 || addToCart.isPending}
                    onClick={() => addToCart.mutate()}
                  >
                    <ShoppingCart className="mr-2 h-5 w-5" />
                    Add to Cart
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => addToWishlist.mutate()}
                    disabled={addToWishlist.isPending}
                  >
                    <Heart className="h-5 w-5" />
                  </Button>
                </>
              ) : (
                <Link href="/auth/login" className={buttonVariants({ size: "lg", className: "flex-1" })}>
                  Login to Purchase
                </Link>
              )}
            </div>
          </div>
        </div>

        <div className="mt-12">
          <h2 className="mb-6 text-2xl font-bold">Reviews</h2>
          <ReviewSection productId={product.id} />
        </div>
      </div>
    </Shell>
  )
}

function ReviewSection({ productId }: { productId: number }) {
  const { data: reviews } = useQuery({
    queryKey: ["reviews", productId],
    queryFn: () => api.get<Review[]>(`/products/${productId}/reviews`),
  })

  if (!reviews?.length) {
    return <p className="text-muted-foreground">No reviews yet.</p>
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <div key={review.id} className="rounded-lg border p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-medium">{review.user?.first_name || review.user?.email || "Anonymous"}</span>
              <div className="flex">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`h-3 w-3 ${i < review.rating ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"}`}
                  />
                ))}
              </div>
            </div>
            <span className="text-xs text-muted-foreground">{new Date(review.created_at).toLocaleDateString()}</span>
          </div>
          <p className="text-sm text-muted-foreground">{review.comment}</p>
        </div>
      ))}
    </div>
  )
}
