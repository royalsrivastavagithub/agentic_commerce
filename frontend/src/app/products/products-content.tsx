"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse, Category } from "@/types/api"
import { useState, useMemo, useEffect } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Star } from "lucide-react"
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
  const [category, setCategory] = useState<string>("all")
  const [urlReady, setUrlReady] = useState(false)
  const [sort, setSort] = useState<string>("default")
  const [page, setPage] = useState(1)
  const [minPrice, setMinPrice] = useState("")
  const [maxPrice, setMaxPrice] = useState("")
  const [minRating, setMinRating] = useState<number>(0)

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories"),
  })

  // Sync URL params into state (Next.js useSearchParams resolves async)
  useEffect(() => {
    if (categoryFromUrl) setCategory(categoryFromUrl)
    setUrlReady(true)
  }, [categoryFromUrl])

  useEffect(() => {
    setPage(1)
  }, [searchFromUrl, categoryFromUrl])

  useEffect(() => {
    if (searchFromUrl) setCategory("all")
  }, [searchFromUrl])

  const categoryIdMap = useMemo(() => {
    const m = new Map<string, number>()
    categories?.forEach((c) => m.set(c.name, c.id))
    return m
  }, [categories])

  const resetFilters = () => {
    setCategory("all")
    setSort("default")
    setPage(1)
    setMinPrice("")
    setMaxPrice("")
    setMinRating(0)
  }

  const hasFilters = category !== "all" || sort !== "default" || minPrice || maxPrice || minRating > 0

  const skip = (page - 1) * LIMIT
  const activeCategory = searchFromUrl ? "all" : category
  const catId = activeCategory !== "all" ? categoryIdMap.get(activeCategory) : undefined
  const productsQueryKey = searchFromUrl
    ? ["products", "search", searchFromUrl, catId, page, minPrice, maxPrice, minRating]
    : ["products", "list", skip, LIMIT, category, sort, minPrice, maxPrice, minRating]

  const { data: productsData, isLoading } = useQuery({
    queryKey: productsQueryKey,
    enabled: urlReady && (category === "all" || catId !== undefined),
    queryFn: () => {
      if (searchFromUrl) {
        let url = `/products/search?q=${encodeURIComponent(searchFromUrl)}&skip=${skip}&limit=${LIMIT}`
        if (catId) url += `&category_id=${catId}`
        return api.get<ProductListResponse>(url)
      }
      if (catId) {
        return api.get<ProductListResponse>(`/categories/${catId}/products?skip=${skip}&limit=${LIMIT}`)
      }
      return api.get<ProductListResponse>(`/products?skip=${skip}&limit=${LIMIT}`)
    },
  })

  const allProducts = productsData?.products ?? []
  const total = productsData?.total ?? 0

  const products = useMemo(() => {
    let p = [...allProducts]

    if (minPrice) {
      const m = parseFloat(minPrice)
      if (!isNaN(m)) p = p.filter((x) => (x.price * (1 - (x.discount_percentage || 0) / 100)) >= m)
    }
    if (maxPrice) {
      const m = parseFloat(maxPrice)
      if (!isNaN(m)) p = p.filter((x) => (x.price * (1 - (x.discount_percentage || 0) / 100)) <= m)
    }
    if (minRating > 0) {
      p = p.filter((x) => x.rating >= minRating)
    }

    if (sort === "price-asc") p.sort((a, b) => a.price - b.price)
    else if (sort === "price-desc") p.sort((a, b) => b.price - a.price)
    else if (sort === "rating") p.sort((a, b) => b.rating - a.rating)

    return p
  }, [allProducts, minPrice, maxPrice, minRating, sort])

  const totalPages = Math.ceil(total / LIMIT)
  const displayProducts = products.slice(0, LIMIT)

  return (
    <Shell>
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">


        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="hidden w-56 shrink-0 md:block">
            <div className="space-y-5">
              {/* Sort */}
              <div>
                <h3 className="mb-1.5 text-sm font-bold text-gray-900">Sort by</h3>
                <select
                  value={sort}
                  onChange={(e) => { setSort(e.target.value); setPage(1) }}
                  className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-amazon-link"
                >
                  <option value="default">Default</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="rating">Top Rated</option>
                </select>
              </div>

              {/* Price range */}
              <div>
                <h3 className="mb-1.5 text-sm font-bold text-gray-900">Price Range</h3>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-amazon-link"
                  />
                  <span className="text-xs text-gray-400">to</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-amazon-link"
                  />
                </div>
              </div>

              {/* Rating filter */}
              <div>
                <h3 className="mb-1.5 text-sm font-bold text-gray-900">Min. Rating</h3>
                <div className="space-y-1">
                  {[4, 3, 2, 1].map((r) => (
                    <button
                      key={r}
                      onClick={() => setMinRating(minRating === r ? 0 : r)}
                      className={`flex w-full items-center gap-1 rounded px-2 py-1 text-sm hover:bg-gray-50 ${
                        minRating === r ? "bg-gray-100 font-medium" : "text-gray-600"
                      }`}
                    >
                      <div className="flex">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={`h-3.5 w-3.5 ${
                              i < r ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-xs">& up</span>
                    </button>
                  ))}
                </div>
              </div>

              {hasFilters && (
                <button onClick={resetFilters} className="text-sm font-medium text-amazon-link hover:underline">
                  Clear all filters
                </button>
              )}
            </div>
          </aside>

          {/* Main */}
          <div className="flex-1">
            {isLoading ? (
              <div className="flex flex-col gap-3">
                {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex animate-pulse gap-4 rounded-lg border bg-white p-3 dark:border-border dark:bg-card">
                    <div className="h-28 w-28 shrink-0 rounded-md bg-gray-200" />
                    <div className="flex flex-1 flex-col justify-center space-y-2">
                      <div className="h-4 w-3/4 rounded bg-gray-200" />
                      <div className="h-3 w-1/2 rounded bg-gray-200" />
                      <div className="h-5 w-1/4 rounded bg-gray-200" />
                    </div>
                  </div>
                ))}
              </div>
            ) : displayProducts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <p className="text-lg text-gray-600">No results found</p>
                <p className="mt-1 text-sm text-muted-foreground">Try adjusting your search or filters</p>
                <button onClick={resetFilters} className="mt-4 text-sm font-medium text-amazon-link hover:underline">
                  Clear all filters
                </button>
              </div>
            ) : (
              <>


                <div className="flex flex-col gap-3">
                  {displayProducts.map((product) => (
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
      className="flex gap-4 rounded-lg border border-gray-200 bg-white p-3 transition-shadow hover:shadow-lg dark:border-border dark:bg-card"
    >
      <div className="h-28 w-28 shrink-0 overflow-hidden rounded-md bg-white sm:h-32 sm:w-32">
        <img
          src={product.thumbnail || "/placeholder.svg"}
          alt={product.title}
          className="h-full w-full object-contain mix-blend-multiply"
        />
      </div>

      <div className="flex flex-1 flex-col justify-between py-1">
        <div>
          <h3 className="line-clamp-1 text-sm font-medium text-amazon-link group-hover:underline sm:text-base">
            {product.title}
          </h3>

          <p className="mt-1 line-clamp-1 text-xs text-muted-foreground sm:line-clamp-2">
            {product.description}
          </p>

          <div className="mt-1 flex items-center gap-1">
            <div className="flex">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`h-3 w-3 ${i < Math.round(product.rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-300"}`}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">({product.review_count})</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{product.brand}</span>
          {product.brand && <span>•</span>}
          <span className={product.stock > 0 ? "text-green-600" : "text-destructive"}>
            {product.stock > 0 ? "In Stock" : "Out of stock"}
          </span>
        </div>
      </div>

      <div className="flex w-24 shrink-0 flex-col items-end justify-center sm:w-28">
        {product.discount_percentage > 0 ? (
          <>
            <span className="text-lg font-bold sm:text-xl">₹{discounted.toFixed(2)}</span>
            <span className="text-xs text-muted-foreground line-through">₹{product.price.toFixed(2)}</span>
            <span className="mt-1 rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700">
              -{product.discount_percentage}%
            </span>
          </>
        ) : (
          <span className="text-lg font-bold sm:text-xl">₹{product.price.toFixed(2)}</span>
        )}
        {product.stock <= 5 && product.stock > 0 && (
          <p className="mt-1 text-[10px] text-destructive">Only {product.stock} left</p>
        )}
      </div>
    </Link>
  )
}
