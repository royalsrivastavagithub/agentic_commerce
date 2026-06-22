"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse, Category } from "@/types/api"
import { useState, useMemo } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Star, ChevronDown } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"

const LIMIT = 12

export default function ProductsContent() {
  const searchParams = useSearchParams()
  const searchFromUrl = searchParams.get("search") ?? ""
  const categoryFromUrl = searchParams.get("category") ?? ""
  const [category, setCategory] = useState<string>(categoryFromUrl || "all")
  const [sort, setSort] = useState<string>("default")
  const [page, setPage] = useState(1)

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories"),
  })

  const categoryIdMap = useMemo(() => {
    const m = new Map<string, number>()
    categories?.forEach((c) => m.set(c.name, c.id))
    return m
  }, [categories])

  const resetFilters = () => {
    setCategory("all")
    setSort("default")
    setPage(1)
  }

  const skip = (page - 1) * LIMIT
  const productsQueryKey = searchFromUrl
    ? ["products", "search", searchFromUrl, page]
    : ["products", "list", skip, LIMIT, category, sort]

  const { data: productsData, isLoading } = useQuery({
    queryKey: productsQueryKey,
    queryFn: () => {
      if (searchFromUrl) {
        return api.get<ProductListResponse>(
          `/products/search?q=${encodeURIComponent(searchFromUrl)}&skip=${skip}&limit=${LIMIT}`,
        )
      }
      if (category !== "all") {
        const catId = categoryIdMap.get(category)
        if (catId) {
          return api.get<ProductListResponse>(`/categories/${catId}/products?skip=${skip}&limit=${LIMIT}`)
        }
      }
      let url = `/products?skip=${skip}&limit=${LIMIT}`
      if (sort === "price-asc") url += "&sort=price&order=asc"
      else if (sort === "price-desc") url += "&sort=price&order=desc"
      else if (sort === "rating") url += "&sort=rating&order=desc"
      return api.get<ProductListResponse>(url)
    },
  })

  const products = productsData?.products ?? []
  const total = productsData?.total ?? 0
  const totalPages = Math.ceil(total / LIMIT)

  return (
    <Shell>
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        {/* Breadcrumb + Result count */}
        <div className="mb-4">
          <p className="text-sm text-muted-foreground">
            {searchFromUrl ? (
              <>
                <Link href="/products" className="text-amazon-link hover:underline">
                  All
                </Link>
                <span className="mx-1">›</span>
                <span>Results for &quot;{searchFromUrl}&quot;</span>
              </>
            ) : (
              <span>{total} results</span>
            )}
          </p>
        </div>

        <div className="flex gap-6">
          {/* Left Sidebar — Amazon-style filters */}
          <aside className="hidden w-56 shrink-0 md:block">
            <div className="space-y-6">
              {/* Category filter */}
              <div>
                <h3 className="mb-2 text-base font-bold">Category</h3>
                <div className="space-y-1">
                  <button
                    onClick={() => {
                      setCategory("all")
                      setPage(1)
                    }}
                    className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-gray-100 ${
                      category === "all" ? "font-bold text-amazon-link" : "text-gray-700"
                    }`}
                  >
                    All Categories
                  </button>
                  {categories?.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        setCategory(c.name)
                        setPage(1)
                      }}
                      className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-gray-100 ${
                        category === c.name ? "font-bold text-amazon-link" : "text-gray-700"
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort */}
              <div>
                <h3 className="mb-2 text-base font-bold">Sort by</h3>
                <select
                  value={sort}
                  onChange={(e) => {
                    setSort(e.target.value)
                    setPage(1)
                  }}
                  className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-amazon-link"
                >
                  <option value="default">Default</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="rating">Top Rated</option>
                </select>
              </div>

              {/* Clear filters */}
              {(category !== "all" || sort !== "default") && (
                <button
                  onClick={resetFilters}
                  className="text-sm font-medium text-amazon-link hover:underline"
                >
                  Clear all filters
                </button>
              )}
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1">
            {isLoading ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="aspect-square rounded-lg bg-gray-200" />
                    <div className="mt-2 space-y-1.5">
                      <div className="h-4 w-3/4 rounded bg-gray-200" />
                      <div className="h-3 w-1/2 rounded bg-gray-200" />
                      <div className="h-5 w-1/3 rounded bg-gray-200" />
                    </div>
                  </div>
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <p className="text-lg text-gray-600">No results found</p>
                <p className="mt-1 text-sm text-muted-foreground">Try adjusting your search or filters</p>
                <button onClick={resetFilters} className="mt-4 text-sm font-medium text-amazon-link hover:underline">
                  Clear all filters
                </button>
              </div>
            ) : (
              <>
                {/* Active filters summary */}
                <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    1-{Math.min(products.length, LIMIT)} of {total} results
                  </span>
                  {category !== "all" && (
                    <Badge variant="secondary" className="gap-1">
                      {category}
                      <button onClick={() => { setCategory("all"); setPage(1) }} className="ml-1 hover:text-foreground">
                        ✕
                      </button>
                    </Badge>
                  )}
                </div>

                {/* Product grid */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

                {totalPages > 1 && (
                  <Pagination className="mt-6">
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
                            <PaginationLink
                              onClick={() => setPage(p)}
                              isActive={p === page}
                              className="cursor-pointer"
                            >
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
        </div>
      </div>
    </Shell>
  )
}

function ProductCard({ product }: { product: Product }) {
  const discounted = product.price * (1 - (product.discount_percentage || 0) / 100)

  return (
    <Link
      href={`/products/${product.id}`}
      className="group rounded-lg border border-gray-200 bg-white p-3 transition-shadow hover:shadow-lg"
    >
      <div className="mb-2 flex items-center justify-center overflow-hidden rounded-md bg-white">
        <img
          src={product.thumbnail || "/placeholder.svg"}
          alt={product.title}
          className="h-48 w-full object-contain mix-blend-multiply transition-transform group-hover:scale-105"
        />
      </div>

      <h3 className="line-clamp-2 text-sm font-medium text-amazon-link group-hover:underline">
        {product.title}
      </h3>

      <div className="mt-1 flex items-center gap-1">
        <div className="flex">
          {Array.from({ length: 5 }).map((_, i) => (
            <Star
              key={i}
              className={`h-3 w-3 ${
                i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
              }`}
            />
          ))}
        </div>
        <span className="text-xs text-muted-foreground">({product.review_count})</span>
      </div>

      <div className="mt-2">
        {product.discount_percentage > 0 ? (
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold">₹{discounted.toFixed(2)}</span>
            <span className="text-xs text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
          </div>
        ) : (
          <span className="text-lg font-bold">₹{product.price.toFixed(2)}</span>
        )}
        {product.discount_percentage > 0 && (
          <span className="ml-1 text-xs text-green-700">({product.discount_percentage}% off)</span>
        )}
      </div>

      {product.stock <= 5 && product.stock > 0 && (
        <p className="mt-1 text-xs text-destructive">Only {product.stock} left in stock.</p>
      )}
      {product.stock === 0 && (
        <p className="mt-1 text-xs text-muted-foreground">Out of stock</p>
      )}
    </Link>
  )
}
