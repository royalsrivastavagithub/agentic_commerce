"use client"

import { Suspense } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse, Category } from "@/types/api"
import { useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Star } from "lucide-react"
import { Shell } from "@/components/features/shell"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const LIMIT = 12

export default function ProductsPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-8"><div className="animate-pulse space-y-4">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-32 rounded-lg bg-muted" />)}</div></div>}>
      <ProductsPageContent />
    </Suspense>
  )
}

function ProductsPageContent() {
  const searchParams = useSearchParams()
  const searchFromUrl = searchParams.get("search") ?? ""
  const [search, setSearch] = useState(searchFromUrl)
  const [category, setCategory] = useState<string>("all")
  const [sort, setSort] = useState<string>("default")
  const [page, setPage] = useState(1)

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories"),
  })

  const skip = (page - 1) * LIMIT
  const productsQueryKey = search
    ? ["products", "search", search, page]
    : ["products", "list", skip, LIMIT, category, sort]

  const { data: productsData, isLoading } = useQuery({
    queryKey: productsQueryKey,
    queryFn: () => {
      if (search) {
        return api.get<ProductListResponse>(`/products/search?q=${encodeURIComponent(search)}&skip=${skip}&limit=${LIMIT}`)
      }
      let url = `/products?skip=${skip}&limit=${LIMIT}`
      if (category !== "all") url += `&category=${encodeURIComponent(category)}`
      if (sort === "price-asc") url += "&sort=price&order=asc"
      else if (sort === "price-desc") url += "&sort=price&order=desc"
      else if (sort === "rating") url += "&sort=rating&order=desc"
      return api.get<ProductListResponse>(url)
    },
  })

  const products = productsData?.items ?? []
  const total = productsData?.total ?? 0
  const totalPages = Math.ceil(total / LIMIT)

  return (
    <Shell>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">
            {search ? `Results for "${search}"` : "Products"}
          </h1>
          <p className="mt-1 text-muted-foreground">{total} products found</p>
        </div>

        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setPage(1)}
              className="pl-9"
            />
          </div>

          <Select
            value={category}
            onValueChange={(v) => {
              if (v) setCategory(v)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories?.map((c) => (
                <SelectItem key={c.id} value={c.name}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={sort}
            onValueChange={(v) => {
              if (v) setSort(v)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="default">Default</SelectItem>
              <SelectItem value="price-asc">Price: Low to High</SelectItem>
              <SelectItem value="price-desc">Price: High to Low</SelectItem>
              <SelectItem value="rating">Top Rated</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="animate-pulse rounded-lg border bg-card">
                <div className="aspect-square bg-muted" />
                <div className="space-y-2 p-4">
                  <div className="h-4 w-3/4 rounded bg-muted" />
                  <div className="h-4 w-1/2 rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-lg text-muted-foreground">No products found</p>
            <Link href="/products" className={buttonVariants({ variant: "link" })}>
              Clear filters
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>

            {totalPages > 1 && (
              <Pagination className="mt-8">
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className={page <= 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    const start = Math.max(1, page - 2)
                    const p = start + i
                    if (p > totalPages) return null
                    return (
                      <PaginationItem key={p}>
                        <PaginationLink onClick={() => setPage(p)} isActive={p === page} className="cursor-pointer">
                          {p}
                        </PaginationLink>
                      </PaginationItem>
                    )
                  })}
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      className={page >= totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            )}
          </>
        )}
      </div>
    </Shell>
  )
}

function ProductCard({ product }: { product: Product }) {
  const discounted = product.price * (1 - (product.discount_percentage || 0) / 100)

  return (
    <Link href={`/products/${product.id}`} className="group rounded-lg border bg-card transition-shadow hover:shadow-md">
      <div className="aspect-square overflow-hidden rounded-t-lg bg-muted">
        <img
          src={product.thumbnail || "/placeholder.svg"}
          alt={product.title}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
      </div>
      <div className="p-4">
        <div className="mb-1 flex items-center gap-2 text-sm text-muted-foreground">
          {product.category && <span>{product.category}</span>}
        </div>
        <h3 className="line-clamp-1 font-medium">{product.title}</h3>
        <div className="mt-1 flex items-center gap-2">
          <span className="text-lg font-bold">₹{discounted.toFixed(2)}</span>
          {product.discount_percentage > 0 && (
            <span className="text-sm text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
          )}
        </div>
        <div className="mt-1 flex items-center gap-1 text-sm">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span>{product.rating.toFixed(1)}</span>
          <span className="text-muted-foreground">({product.review_count})</span>
        </div>
        {product.stock <= 5 && product.stock > 0 && (
          <Badge variant="destructive" className="mt-2">
            Only {product.stock} left
          </Badge>
        )}
        {product.stock === 0 && (
          <Badge variant="outline" className="mt-2 text-muted-foreground">
            Out of stock
          </Badge>
        )}
      </div>
    </Link>
  )
}
