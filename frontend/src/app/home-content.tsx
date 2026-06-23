"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse } from "@/types/api"
import Link from "next/link"
import { Star, Sparkles, Truck, RotateCcw, Shield } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"

function SkeletonGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="flex flex-wrap gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="w-40 animate-pulse rounded-lg border bg-white p-2 dark:border-border dark:bg-card">
          <div className="mb-2 h-28 rounded-md bg-gray-200 dark:bg-muted" />
          <div className="mb-1 h-3 w-3/4 rounded bg-gray-200 dark:bg-muted" />
          <div className="h-4 w-1/2 rounded bg-gray-200 dark:bg-muted" />
        </div>
      ))}
    </div>
  )
}

export default function HomeContent() {
  const { data: featured, isLoading: featuredLoading, isError: featuredError } = useQuery({
    queryKey: ["home-featured"],
    queryFn: () => api.get<ProductListResponse>("/products/featured?limit=10"),
  })

  const { data: deals, isLoading: dealsLoading, isError: dealsError } = useQuery({
    queryKey: ["home-deals"],
    queryFn: () => api.get<ProductListResponse>("/products?min_discount=10&limit=8"),
  })

  const products = featured?.products ?? []
  const dealProducts = deals?.products ?? []

  return (
    <Shell>
      {/* Hero Banner */}
      <div className="bg-gradient-to-b from-amazon-nav2 to-amazon-nav">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center text-center text-white">
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Welcome to Agentic Commerce
            </h1>
            <p className="mt-4 max-w-2xl text-base text-gray-300 sm:text-lg">
              Discover amazing products at unbeatable prices. Free shipping on orders over ₹500.
            </p>

          </div>
        </div>
      </div>

      {/* Trust badges */}
      <div className="border-b bg-gray-50 dark:bg-muted dark:border-border">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-4 px-4 py-4 sm:grid-cols-4 sm:px-6 lg:px-8">
          {[
            { icon: Truck, label: "Free Shipping", desc: "On orders ₹500+" },
            { icon: RotateCcw, label: "Easy Returns", desc: "30-day return policy" },
            { icon: Shield, label: "Secure Payment", desc: "100% secure checkout" },
            { icon: Sparkles, label: "Premium Quality", desc: "Verified products" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-3">
              <item.icon className="h-8 w-8 shrink-0 text-amazon-link" />
              <div>
                <p className="text-sm font-semibold text-foreground">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Today's Deals */}
        {dealsError ? (
          <section className="mb-10">
            <h2 className="mb-4 text-xl font-bold text-foreground">Today&apos;s Deals</h2>
            <p className="text-sm text-muted-foreground">Could not load deals. Please try again later.</p>
          </section>
        ) : dealsLoading ? (
          <section className="mb-10">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">Today&apos;s Deals</h2>
            </div>
            <SkeletonGrid count={4} />
          </section>
        ) : dealProducts.length > 0 && (
          <section className="mb-10">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">Today&apos;s Deals</h2>
              <Link href="/products?min_discount=10" className="text-sm font-medium text-amazon-link hover:underline">View All</Link>
            </div>
            <div className="flex flex-wrap gap-4">
              {dealProducts.slice(0, 7).map((product) => (
                <MiniCard key={product.id} product={product} />
              ))}
            </div>
          </section>
        )}

        {/* Featured Products */}
        {featuredError ? (
          <section className="mb-10">
            <h2 className="mb-4 text-xl font-bold text-foreground">Featured Products</h2>
            <p className="text-sm text-muted-foreground">Could not load featured products. Please try again later.</p>
          </section>
        ) : featuredLoading ? (
          <section className="mb-10">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">Featured Products</h2>
            </div>
            <SkeletonGrid count={4} />
          </section>
        ) : (
          <section className="mb-10">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">Featured Products</h2>
              <Link href="/products?is_featured=true" className="text-sm font-medium text-amazon-link hover:underline">View All</Link>
            </div>
            <div className="flex flex-wrap gap-4">
              {products.slice(0, 7).map((product) => (
                <MiniCard key={product.id} product={product} />
              ))}
            </div>
          </section>
        )}
      </div>
    </Shell>
  )
}

function FeaturedCard({ product }: { product: Product }) {
  const discounted = product.price * (1 - (product.discountPercentage ?? product.discount_percentage ?? 0) / 100)

  return (
    <Link
      href={`/products/${product.id}`}
      className="flex gap-4 rounded-lg border bg-white p-3 transition-shadow hover:shadow-md dark:border-border dark:bg-card"
    >
      <div className="h-32 w-32 shrink-0 overflow-hidden rounded-md bg-white sm:h-36 sm:w-36 dark:bg-card">
        <img
          src={product.thumbnail || "/placeholder.svg"}
          alt={product.title}
          className="h-full w-full object-contain"
        />
      </div>
      <div className="flex flex-1 flex-col justify-between py-1">
        <div>
          <h3 className="line-clamp-1 text-base font-bold text-foreground group-hover:text-amazon-link sm:text-lg">
            {product.title}
          </h3>
          <p className="mt-1 line-clamp-1 text-sm text-muted-foreground sm:line-clamp-2">
            {product.description}
          </p>
          <div className="mt-2 flex items-center gap-1">
            <div className="flex" role="img" aria-label={`${Math.round(product.rating)} out of 5 stars`}>
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-3.5 w-3.5 ${
                    i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">({product.review_count})</span>
          </div>
          <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
            <span>{product.brand}</span>
            {product.brand && <span>•</span>}
            <span className={product.stock > 0 ? "text-green-600" : "text-destructive"}>
              {product.stock > 0 ? "In Stock" : "Out of stock"}
            </span>
          </div>
        </div>
      </div>
      <div className="flex w-24 shrink-0 flex-col items-end justify-center sm:w-28">
        {(product.discountPercentage ?? product.discount_percentage ?? 0) > 0 ? (
          <>
            <span className="text-lg font-bold sm:text-xl">₹{discounted.toFixed(2)}</span>
            <span className="text-xs text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
            <span className="mt-1 rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
              -{product.discountPercentage ?? product.discount_percentage ?? 0}%
            </span>
          </>
        ) : (
          <span className="text-lg font-bold sm:text-xl">₹{product.price.toFixed(2)}</span>
        )}
      </div>
    </Link>
  )
}

function MiniCard({ product }: { product: Product }) {
  const discounted = product.price * (1 - (product.discountPercentage ?? product.discount_percentage ?? 0) / 100)

  return (
    <Link
      href={`/products/${product.id}`}
      className="w-40 shrink-0 snap-start rounded-lg border bg-white p-2 transition-all hover:shadow-lg hover:-translate-y-0.5 dark:border-border dark:bg-card"
    >
      <div className="mb-2 h-28 overflow-hidden rounded-md bg-white">
        <img src={product.thumbnail || "/placeholder.svg"} alt={product.title} className="h-full w-full object-contain" />
      </div>
      <p className="line-clamp-1 text-xs font-bold text-foreground">{product.title}</p>
      {(product.discountPercentage ?? product.discount_percentage ?? 0) > 0 ? (
        <div className="mt-1">
          <span className="text-sm font-bold">₹{discounted.toFixed(2)}</span>
          <span className="ml-1 text-[10px] text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
          <span className="ml-1 rounded bg-red-100 px-1 py-0.5 text-[10px] font-medium text-red-700">-{product.discountPercentage ?? product.discount_percentage ?? 0}%</span>
        </div>
      ) : (
        <p className="mt-1 text-sm font-bold">₹{product.price.toFixed(2)}</p>
      )}
      <div className="mt-1 flex items-center gap-0.5" role="img" aria-label={`${Math.round(product.rating)} out of 5 stars`}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Star key={i} className={`h-2.5 w-2.5 ${i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}`} />
        ))}
      </div>
    </Link>
  )
}
