"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, Review } from "@/types/api"
import { useParams, useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Star, ChevronRight } from "lucide-react"
import { useAuthStore } from "@/stores/auth-store"
import { toast } from "sonner"
import { useState } from "react"
import Link from "next/link"
import { buttonVariants } from "@/components/ui/button"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"

export default function ProductDetailContent() {
  const { id } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuthStore()
  const queryClient = useQueryClient()
  const router = useRouter()
  const [quantity, setQuantity] = useState(1)
  const [selectedImage, setSelectedImage] = useState(0)

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", id],
    queryFn: () => api.get<Product>(`/products/${id}`),
  })

  const addToCart = useMutation({
    mutationFn: () => api.post("/cart/items", { product_id: Number(id), quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
      toast.success("Added to cart")
      router.push("/cart")
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const buyNow = useMutation({
    mutationFn: () => api.post("/cart/items", { product_id: Number(id), quantity }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] })
      router.push("/checkout")
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
          <div className="animate-pulse">
            <div className="mb-4 h-4 w-48 rounded bg-gray-200 dark:bg-muted" />
            <div className="grid gap-8 lg:grid-cols-2">
              <div className="aspect-square rounded-lg bg-gray-200 dark:bg-muted" />
              <div className="space-y-4">
                <div className="h-8 w-3/4 rounded bg-gray-200 dark:bg-muted" />
                <div className="h-4 w-1/3 rounded bg-gray-200 dark:bg-muted" />
                <div className="h-6 w-1/4 rounded bg-gray-200 dark:bg-muted" />
                <div className="h-20 rounded bg-gray-200 dark:bg-muted" />
              </div>
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
          <Link href="/products" className="mt-2 text-sm text-amazon-link hover:underline">
            Back to results
          </Link>
        </div>
      </Shell>
    )
  }

  const discounted = product.price * (1 - (product.discount_percentage || 0) / 100)

  return (
    <Shell>
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <div className="mb-4 text-sm text-muted-foreground">
          <Link href="/products" className="text-amazon-link hover:underline">
            All
          </Link>
          {product.category && (
            <>
              <ChevronRight className="mx-1 inline h-3 w-3" />
              <Link
                href={`/products?category=${encodeURIComponent(product.category)}`}
                className="text-amazon-link hover:underline"
              >
                {product.category}
              </Link>
            </>
          )}
          <ChevronRight className="mx-1 inline h-3 w-3" />
          <span className="text-muted-foreground">{product.title}</span>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left: Image gallery */}
          <div>
            <div className="mb-3 flex items-center justify-center overflow-hidden rounded-lg border bg-white p-4 dark:bg-card">
              <img
                src={product.images?.[selectedImage] || product.thumbnail || "/placeholder.svg"}
                alt={product.title}
                className="h-96 w-full object-contain"
              />
            </div>
            {product.images?.length > 1 && (
              <div className="flex gap-2 overflow-auto">
                {product.images.map((img, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedImage(i)}
                    className={`h-16 w-16 flex-shrink-0 overflow-hidden rounded-md border-2 bg-white p-1 dark:bg-card ${
                      selectedImage === i ? "border-amazon-link" : "border-gray-200 dark:border-border"
                    }`}
                  >
                    <img src={img || "/placeholder.svg"} alt="" className="h-full w-full object-contain" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right: Product info */}
          <div>
            <h1 className="text-xl font-medium leading-snug text-foreground lg:text-2xl">{product.title}</h1>

            {/* Rating */}
            <div className="mt-2 flex items-center gap-2">
              <div className="flex">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`h-4 w-4 ${
                      i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-amazon-link hover:underline hover:cursor-pointer">
                {product.review_count} ratings
              </span>
              <span className="text-xs text-muted-foreground">|</span>
            </div>

            <div className="my-3 border-b" />

            {/* Price box */}
            <div className="space-y-1">
              {product.discount_percentage > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground line-through">-{product.discount_percentage}%</span>
                </div>
              )}
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-medium text-price">
                  ₹{discounted.toFixed(2)}
                </span>
                {product.discount_percentage > 0 && (
                  <span className="text-sm text-muted-foreground line-through">
                    ₹{product.price.toFixed(2)}
                  </span>
                )}
              </div>
              {product.discount_percentage > 0 && (
                <p className="text-sm text-green-700 dark:text-green-500">You save ₹{(product.price - discounted).toFixed(2)}</p>
              )}
            </div>

            <div className="my-3 border-b" />

            {/* Stock status */}
            <p className="text-sm">
              {product.stock > 0 ? (
                <span className="font-medium text-green-700 dark:text-green-500">In Stock</span>
              ) : (
                <span className="font-medium text-destructive">Currently Unavailable</span>
              )}
            </p>

            {product.stock > 0 && (
              <div className="mt-3 space-y-3">
                {/* Quantity selector — Amazon-style dropdown */}
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-foreground">Quantity:</label>
                  <select
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="rounded-lg border border-gray-300 px-2 py-1 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                  >
                    {Array.from({ length: Math.min(product.stock, 10) }, (_, i) => (
                      <option key={i + 1} value={i + 1}>
                        {i + 1}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Action buttons */}
                {isAuthenticated ? (
                  <div className="space-y-2">
                    <button
                      type="button"
                      onClick={() => addToCart.mutate()}
                      disabled={addToCart.isPending}
                      className="w-full rounded-full bg-[#FFD814] px-6 py-2 text-sm font-semibold text-black shadow-sm hover:brightness-95 disabled:opacity-50"
                    >
                      Add to Cart
                    </button>
                    <button
                      type="button"
                      onClick={() => buyNow.mutate()}
                      disabled={buyNow.isPending}
                      className="w-full rounded-full bg-[#FFA41C] px-6 py-2 text-sm font-semibold text-black shadow-sm hover:brightness-95 disabled:opacity-50"
                    >
                      Buy Now
                    </button>
                  </div>
                ) : (
                  <Link
                    href="/auth/login"
                    className={buttonVariants({ className: "w-full rounded-full bg-[#FFD814] text-black hover:brightness-95" })}
                  >
                    Sign in to purchase
                  </Link>
                )}

                <p className="text-xs text-muted-foreground">
                  Secure transaction. Free shipping on orders over ₹500.
                </p>
              </div>
            )}

            {/* Feature bullets */}
            <div className="my-4 space-y-2">
              <h3 className="text-base font-medium">About this item</h3>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                <li>{product.description || "No description available."}</li>
                {product.brand && <li>Brand: {product.brand}</li>}
                <li>Material: Premium quality</li>
                <li>Warranty: {product.warranty_information}</li>
                <li>Return Policy: {product.return_policy}</li>
                <li>Shipping: {product.shipping_information}</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Product details list */}
        <div className="mt-8 border-t pt-6">
          <h2 className="mb-4 text-xl font-bold">Product Details</h2>
          <div className="space-y-1">
            {[
              { label: "Brand", value: product.brand },
              { label: "Weight", value: `${product.weight} g` },
              { label: "Dimensions", value: `${product.dimensions.width} × ${product.dimensions.height} × ${product.dimensions.depth} cm` },
              { label: "Min. Order", value: `${product.minimum_order_quantity}` },
              { label: "Availability", value: product.availability_status },
              { label: "Shipping", value: product.shipping_information },
              { label: "Warranty", value: product.warranty_information },
              { label: "Return Policy", value: product.return_policy },
            ]
              .filter((r) => r.value)
              .map((row) => (
                <div key={row.label} className="flex gap-2 rounded-md bg-muted px-3 py-2 text-sm">
                  <span className="w-32 shrink-0 font-medium text-muted-foreground">{row.label}</span>
                  <span className="text-foreground">{row.value}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Reviews section */}
        <div className="mt-8 border-t pt-6">
          <h2 className="mb-4 text-xl font-bold">Customer Reviews</h2>
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
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <p className="text-sm text-muted-foreground">No reviews yet. Be the first to review this product!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <div key={review.id} className="rounded-lg border p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground">
                {(review.user?.first_name?.[0] || review.user?.email?.[0] || "A").toUpperCase()}
              </div>
              <span className="text-sm font-medium">
                {review.user?.first_name || review.user?.email?.split("@")[0] || "Anonymous"}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              {new Date(review.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </span>
          </div>
          <div className="mb-1 flex">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={`h-3.5 w-3.5 ${
                  i < review.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                }`}
              />
            ))}
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">{review.comment}</p>
        </div>
      ))}
    </div>
  )
}
