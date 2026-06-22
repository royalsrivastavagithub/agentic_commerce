"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse } from "@/types/api"
import Link from "next/link"
import { Star, Sparkles, Truck, RotateCcw, Shield } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"

export default function HomeContent() {
  const { data: featured } = useQuery({
    queryKey: ["home-featured"],
    queryFn: () => api.get<ProductListResponse>("/products/featured?limit=10"),
  })

  const products = featured?.products ?? []

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
        {/* Featured Products */}
        <section className="mb-10">
          <div className="mb-4">
            <h2 className="text-xl font-bold text-foreground">Featured Products</h2>
          </div>
          <div className="flex flex-col gap-3">
            {products.map((product) => (
              <FeaturedCard key={product.id} product={product} />
            ))}
          </div>
        </section>

      </div>
    </Shell>
  )
}

function FeaturedCard({ product }: { product: Product }) {
  const discounted = product.price * (1 - (product.discount_percentage || 0) / 100)

  return (
    <Link
      href={`/products/${product.id}`}
      className="flex gap-4 rounded-lg border bg-white p-3 transition-shadow hover:shadow-lg dark:border-border dark:bg-card"
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
          <h3 className="line-clamp-1 text-base font-medium text-amazon-link group-hover:underline sm:text-lg">
            {product.title}
          </h3>
          <p className="mt-1 line-clamp-1 text-sm text-muted-foreground sm:line-clamp-2">
            {product.description}
          </p>
          <div className="mt-1 flex items-center gap-1">
            <div className="flex">
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
          <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
            <span>{product.brand}</span>
            {product.brand && <span>•</span>}
            <span className={product.stock > 0 ? "text-green-600" : "text-destructive"}>
              {product.stock > 0 ? "In Stock" : "Out of stock"}
            </span>
          </div>
        </div>
      </div>
      <div className="flex w-24 shrink-0 flex-col items-end justify-center sm:w-28">
        {product.discount_percentage > 0 ? (
          <>
            <span className="text-lg font-bold sm:text-xl">₹{discounted.toFixed(2)}</span>
            <span className="text-xs text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
            <span className="mt-1 rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
              -{product.discount_percentage}%
            </span>
          </>
        ) : (
          <span className="text-lg font-bold sm:text-xl">₹{product.price.toFixed(2)}</span>
        )}
      </div>
    </Link>
  )
}
