"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Product, ProductListResponse, Category } from "@/types/api"
import { useState, useMemo, useEffect } from "react"
import Link from "next/link"
import { useSearchParams, useRouter } from "next/navigation"
import { Star } from "lucide-react"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"
import { Slider } from "@/components/ui/slider"
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
  const sortFromUrl = searchParams.get("sort") ?? ""
  const pageFromUrl = parseInt(searchParams.get("page") ?? "1", 10)
  const minPriceFromUrl = searchParams.get("min_price") ?? ""
  const maxPriceFromUrl = searchParams.get("max_price") ?? ""
  const minRatingFromUrl = parseInt(searchParams.get("min_rating") ?? "0", 10)
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

  const { data: priceRange } = useQuery({
    queryKey: ["price-range"],
    queryFn: () => api.get<{ min_price: number; max_price: number }>("/products/price-range"),
  })

  const priceMin = priceRange?.min_price ?? 0
  const priceMax = priceRange?.max_price ?? 1000
  const router = useRouter()

  // Sync URL params into state (Next.js useSearchParams resolves async)
  useEffect(() => {
    if (categoryFromUrl) setCategory(categoryFromUrl)
    if (["price-asc", "price-desc", "rating"].includes(sortFromUrl)) setSort(sortFromUrl)
    if (pageFromUrl > 1) setPage(pageFromUrl)
    if (minPriceFromUrl) setMinPrice(minPriceFromUrl)
    if (maxPriceFromUrl) setMaxPrice(maxPriceFromUrl)
    if (minRatingFromUrl > 0) setMinRating(minRatingFromUrl)
    setUrlReady(true)
  }, [categoryFromUrl, sortFromUrl, pageFromUrl, minPriceFromUrl, maxPriceFromUrl, minRatingFromUrl])

  useEffect(() => {
    setPage(1)
  }, [searchFromUrl, categoryFromUrl])

  useEffect(() => {
    if (searchFromUrl && !categoryFromUrl) setCategory("all")
  }, [searchFromUrl, categoryFromUrl])

  useEffect(() => {
    if (!urlReady) return
    const params = new URLSearchParams()
    if (searchFromUrl) params.set("search", searchFromUrl)
    if (categoryFromUrl) params.set("category", categoryFromUrl)
    if (sort !== "default") params.set("sort", sort)
    if (page > 1) params.set("page", String(page))
    if (minPrice) params.set("min_price", minPrice)
    if (maxPrice) params.set("max_price", maxPrice)
    if (minRating > 0) params.set("min_rating", String(minRating))
    const qs = params.toString()
    router.replace(`/products${qs ? `?${qs}` : ""}`, { scroll: false })
  }, [sort, page, minPrice, maxPrice, minRating, searchFromUrl, categoryFromUrl, urlReady])

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

  const hasFilters = category !== "all" || sort !== "default" || minRating > 0 ||
    (minPrice !== "" && parseFloat(minPrice) > priceMin) ||
    (maxPrice !== "" && parseFloat(maxPrice) < priceMax)

  const skip = (page - 1) * LIMIT
  const catId = category !== "all" ? categoryIdMap.get(category) : undefined
  const productsQueryKey = searchFromUrl
    ? ["products", "search", searchFromUrl, catId, page, minPrice, maxPrice, minRating, sort]
    : ["products", "list", skip, LIMIT, category, sort, minPrice, maxPrice, minRating, priceMin, priceMax]

  const buildSortParams = () => {
    if (sort === "default") return ""
    if (sort === "price-asc") return "&sort_by=price&sort_order=asc"
    if (sort === "price-desc") return "&sort_by=price&sort_order=desc"
    if (sort === "rating") return "&sort_by=rating&sort_order=desc"
    return ""
  }

  const buildFilterParams = () => {
    let s = ""
    if (minPrice && parseFloat(minPrice) > priceMin) s += `&min_price=${parseFloat(minPrice)}`
    if (maxPrice && parseFloat(maxPrice) < priceMax) s += `&max_price=${parseFloat(maxPrice)}`
    if (minRating > 0) s += `&min_rating=${minRating}`
    return s
  }

  const { data: productsData, isLoading } = useQuery({
    queryKey: productsQueryKey,
    enabled: urlReady && (category === "all" || catId !== undefined),
    queryFn: () => {
      const sortParams = buildSortParams()
      const filterParams = buildFilterParams()
      if (searchFromUrl) {
        let url = `/products/search?q=${encodeURIComponent(searchFromUrl)}&skip=${skip}&limit=${LIMIT}`
        if (catId) url += `&category_id=${catId}`
        url += sortParams
        url += filterParams
        return api.get<ProductListResponse>(url)
      }
      if (catId) {
        return api.get<ProductListResponse>(`/categories/${catId}/products?skip=${skip}&limit=${LIMIT}${sortParams}${filterParams}`)
      }
      return api.get<ProductListResponse>(`/products?skip=${skip}&limit=${LIMIT}${sortParams}${filterParams}`)
    },
  })

  const allProducts = productsData?.products ?? []
  const total = productsData?.total ?? 0

  const products = allProducts

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
                <h3 className="mb-1.5 text-sm font-bold text-foreground">Sort by</h3>
                <select
                  value={sort}
                  onChange={(e) => { setSort(e.target.value); setPage(1) }}
                  className="w-full rounded-lg border border-gray-300 px-2 py-1.5 text-sm outline-none focus:border-amazon-link dark:border-border dark:bg-card dark:text-foreground"
                >
                  <option value="default">Default</option>
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="rating">Top Rated</option>
                </select>
              </div>

              {/* Price range slider */}
              <div>
                <h3 className="mb-1.5 text-sm font-bold text-foreground">Price Range</h3>
                <div className="space-y-2 pt-1">
                  <Slider
                    value={[parseInt(minPrice || String(priceMin)), parseInt(maxPrice || String(priceMax))]}
                    onValueChange={([min, max]) => {
                      setMinPrice(min.toString())
                      setMaxPrice(max.toString())
                    }}
                    min={priceMin} max={priceMax} step={10}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>₹{minPrice || priceMin}</span>
                    <span>₹{maxPrice || priceMax}</span>
                  </div>
                </div>
              </div>

              {/* Rating filter */}
              <div>
                <h3 className="mb-1.5 text-sm font-bold text-foreground">Min. Rating</h3>
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
          className="h-full w-full object-contain"
        />
      </div>

      <div className="flex flex-1 flex-col justify-between py-1">
        <div>
          <h3 className="line-clamp-1 text-sm font-medium text-foreground group-hover:text-amazon-link sm:text-base">
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
