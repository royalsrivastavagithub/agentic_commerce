"use client"

import Link from "next/link"
import { ShoppingCart, Search, Menu, LogOut, Package, Heart, Moon, Sun } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { useAuthStore } from "@/stores/auth-store"
import { useCartStore } from "@/stores/cart-store"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Cart, Product, ProductListResponse, Category } from "@/types/api"
import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"

export function Shell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout } = useAuthStore()
  const { isCartOpen, openCart, closeCart } = useCartStore()
  const [searchQuery, setSearchQuery] = useState("")
  const [searchCategory, setSearchCategory] = useState("all")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [suggestionsOpen, setSuggestionsOpen] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { theme, setTheme } = useTheme()

  const { data: cart } = useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/cart"),
    enabled: isAuthenticated,
  })

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories"),
  })

  const cartCount = cart?.items?.reduce((sum, i) => sum + i.quantity, 0) ?? 0
  const cartTotal = cart?.total ?? 0

  const { data: suggestions } = useQuery({
    queryKey: ["search-suggestions", debouncedQuery, searchCategory],
    queryFn: () => {
      let url = `/products/search?q=${encodeURIComponent(debouncedQuery)}&skip=0&limit=5`
      if (searchCategory !== "all") {
        const cat = categories?.find((c) => c.name === searchCategory)
        if (cat) url += `&category_id=${cat.id}`
      }
      return api.get<ProductListResponse>(url)
    },
    enabled: debouncedQuery.length >= 2,
  })

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setSuggestionsOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const q = searchQuery.trim()
    if (!q) return
    setSuggestionsOpen(false)
    let path = `/products?search=${encodeURIComponent(q)}`
    if (searchCategory !== "all") path += `&category=${encodeURIComponent(searchCategory)}`
    router.push(path)
  }

  const handleLogout = () => {
    logout()
    router.push("/products")
  }

  const handleCartClick = () => {
    if (!isAuthenticated) {
      router.push("/auth/login")
      return
    }
    openCart()
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 bg-amazon-nav">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-3 sm:gap-4 sm:px-6">
          <Link
            href="/"
            className="flex shrink-0 items-center text-lg font-bold tracking-tight text-white hover:opacity-80 sm:text-xl"
          >
            Agentic Commerce
          </Link>

          {/* Search bar with category dropdown */}
          <div className="hidden flex-1 sm:flex sm:max-w-xl lg:max-w-4xl" ref={searchRef}>
            <form onSubmit={handleSearch} className="flex w-full">
              <select
                value={searchCategory}
                onChange={(e) => setSearchCategory(e.target.value)}
                className="w-28 rounded-l-md border-r border-gray-300 bg-gray-100 px-2 text-xs text-gray-700 outline-none"
              >
                <option value="all">All</option>
                {categories?.map((c) => (
                  <option key={c.id} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setSuggestionsOpen(true)
                  }}
                  onFocus={() => searchQuery.length >= 2 && setSuggestionsOpen(true)}
                  className="w-full bg-white px-3 py-1.5 text-sm text-gray-900 outline-none placeholder:text-gray-400"
                />
                <button
                  type="submit"
                  className="absolute right-0 top-0 flex h-full items-center justify-center bg-amazon-accent px-3 hover:brightness-95"
                >
                  <Search className="h-5 w-5 text-amazon-nav" />
                </button>

                {/* Search suggestions dropdown */}
                {suggestionsOpen && debouncedQuery.length >= 2 && suggestions && (
                  <div className="absolute left-0 right-0 top-full z-30 mt-1 overflow-hidden rounded-lg border bg-white shadow-lg">
                  {suggestions.products.length > 0 ? (
                    <div>
                      {suggestions.products.slice(0, 5).map((product) => (
                        <Link
                          key={product.id}
                          href={`/products/${product.id}`}
                          onClick={() => { setSuggestionsOpen(false); setSearchQuery("") }}
                          className="flex items-center gap-3 px-3 py-2 text-sm hover:bg-gray-50"
                        >
                          <img
                            src={product.thumbnail || "/placeholder.svg"}
                            alt={product.title}
                            className="h-10 w-10 flex-shrink-0 rounded object-contain"
                          />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-gray-900">{product.title}</p>
                            <p className="text-xs text-muted-foreground">₹{product.price.toFixed(2)}</p>
                          </div>
                        </Link>
                      ))}
                      <Link
                        href={`/products?search=${encodeURIComponent(debouncedQuery)}${searchCategory !== "all" ? `&category=${encodeURIComponent(searchCategory)}` : ""}`}
                        onClick={() => { setSuggestionsOpen(false); setSearchQuery("") }}
                        className="flex items-center justify-center border-t px-3 py-2 text-sm font-medium text-amazon-link hover:bg-gray-50"
                      >
                        See all results for &quot;{debouncedQuery}&quot;
                      </Link>
                    </div>
                  ) : (
                    <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                      No products found for &quot;{debouncedQuery}&quot;
                    </div>
                  )}
                </div>
              )}
            </div>
            </form>
          </div>

          {/* Right section */}
          <nav className="ml-auto flex items-center gap-1 sm:gap-3">
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger className="flex flex-col items-start px-1 py-0.5 text-left text-white hover:opacity-80">
                  <span className="text-[10px] leading-none text-gray-300 sm:text-xs">Hello, {user?.first_name || user?.email}</span>
                  <span className="text-xs font-bold leading-tight sm:text-sm">Account & Lists</span>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-2 py-1.5 text-sm font-medium text-gray-500">{user?.email}</div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => router.push("/orders")}>
                    <Package className="mr-2 h-4 w-4" />
                    Your Orders
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => router.push("/wishlist")}>
                    <Heart className="mr-2 h-4 w-4" />
                    Your Wishlist
                  </DropdownMenuItem>
                  {user?.role === "admin" && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => router.push("/admin")}>
                        <Menu className="mr-2 h-4 w-4" />
                        Admin Dashboard
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-destructive">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link
                href="/auth/login"
                className="flex flex-col px-1 py-0.5 text-white hover:opacity-80"
              >
                <span className="text-[10px] leading-none text-gray-300 sm:text-xs">Hello, Sign in</span>
                <span className="text-xs font-bold leading-tight sm:text-sm">Account & Lists</span>
              </Link>
            )}

            {/* Returns & Orders — guarded */}
            <button
              type="button"
              onClick={() => router.push(isAuthenticated ? "/orders" : "/auth/login")}
              className="hidden flex-col px-1 py-0.5 text-left text-white hover:opacity-80 sm:flex"
            >
              <span className="text-[10px] leading-none text-gray-300 sm:text-xs">Returns</span>
              <span className="text-xs font-bold leading-tight sm:text-sm">& Orders</span>
            </button>

            {/* Theme toggle */}
            <button
              type="button"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="relative flex items-center px-2 py-1.5 text-white hover:opacity-80"
              aria-label="Toggle theme"
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            </button>

            {/* Cart trigger — guarded */}
            <Sheet open={isAuthenticated ? isCartOpen : false} onOpenChange={(open) => open && handleCartClick()}>
              <SheetTrigger
                onClick={(e) => {
                  if (!isAuthenticated) {
                    e.preventDefault()
                    router.push("/auth/login")
                  }
                }}
                className="flex items-end gap-1 px-1 py-0.5 text-white hover:opacity-80"
                aria-label="Cart"
              >
                <div className="relative">
                  <ShoppingCart className="h-6 w-6 sm:h-7 sm:w-7" />
                  {cartCount > 0 && isAuthenticated && (
                    <Badge className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-amazon-accent p-0 text-[10px] font-bold text-amazon-nav sm:h-5 sm:w-5 sm:text-xs">
                      {cartCount}
                    </Badge>
                  )}
                </div>
                <span className="hidden text-xs font-bold leading-tight sm:inline">Cart</span>
              </SheetTrigger>
              <SheetContent className="flex w-full flex-col sm:max-w-md">
                <SheetHeader>
                  <SheetTitle>Shopping Cart</SheetTitle>
                </SheetHeader>
                <div className="flex-1 overflow-auto">
                  {!cart?.items?.length ? (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                      Your cart is empty
                    </div>
                  ) : (
                    <div className="space-y-4 p-4">
                      {cart.items.map((item) => (
                        <div key={item.id} className="flex gap-4 rounded-lg border p-3">
                          <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-md bg-muted">
                            <img
                              src={item.product.thumbnail || "/placeholder.svg"}
                              alt={item.product.title}
                              className="h-full w-full object-cover"
                            />
                          </div>
                          <div className="flex flex-1 flex-col justify-between">
                            <div>
                              <p className="text-sm font-medium">{item.product.title}</p>
                              <p className="text-sm text-muted-foreground">
                                ₹{item.product.price} × {item.quantity}
                              </p>
                            </div>
                            <p className="text-sm font-semibold">₹{(item.product.price * item.quantity).toFixed(2)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="border-t p-4">
                  <div className="mb-4 flex justify-between text-base font-semibold">
                    <span>Total</span>
                    <span>₹{cartTotal.toFixed(2)}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => { closeCart(); router.push("/cart") }}
                    className="w-full rounded-lg bg-amazon-cart px-4 py-2 text-sm font-semibold text-black hover:brightness-95 disabled:opacity-50"
                    disabled={!cart?.items?.length}
                  >
                    View Cart
                  </button>
                </div>
              </SheetContent>
            </Sheet>
          </nav>
        </div>

      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t bg-amazon-nav2 py-8">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-gray-400 sm:px-6 lg:px-8">
          &copy; {new Date().getFullYear()} Agentic Commerce. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
