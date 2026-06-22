"use client"

import Link from "next/link"
import { ShoppingCart, Search, Menu, LogOut, Package, Heart } from "lucide-react"
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
import type { Cart, Category } from "@/types/api"
import { useState } from "react"
import { useRouter } from "next/navigation"

export function Shell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout } = useAuthStore()
  const { isCartOpen, openCart, closeCart } = useCartStore()
  const [searchQuery, setSearchQuery] = useState("")
  const [searchCategory, setSearchCategory] = useState("all")
  const router = useRouter()

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

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const q = searchQuery.trim()
    if (!q) return
    let path = `/products?search=${encodeURIComponent(q)}`
    if (searchCategory !== "all") path += `&category=${encodeURIComponent(searchCategory)}`
    router.push(path)
  }

  const handleLogout = () => {
    logout()
    router.push("/products")
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Top bar — Amazon dark navy */}
      <header className="sticky top-0 z-50 bg-amazon-nav">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-3 sm:gap-4 sm:px-6">
          {/* Logo */}
          <Link
            href="/products"
            className="flex shrink-0 items-center text-lg font-bold tracking-tight text-white hover:opacity-80 sm:text-xl"
          >
            Agentic Commerce
          </Link>

          {/* Search bar — Amazon-style with category dropdown + search button */}
          <div className="hidden flex-1 sm:flex sm:max-w-2xl lg:max-w-3xl">
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
              <input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-3 py-1.5 text-sm text-black outline-none"
              />
              <button
                type="submit"
                className="flex items-center justify-center rounded-r-md bg-amazon-accent px-3 hover:brightness-95"
              >
                <Search className="h-5 w-5 text-amazon-nav" />
              </button>
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

            <Link
              href="/orders"
              className="hidden flex-col px-1 py-0.5 text-white hover:opacity-80 sm:flex"
            >
              <span className="text-[10px] leading-none text-gray-300 sm:text-xs">Returns</span>
              <span className="text-xs font-bold leading-tight sm:text-sm">& Orders</span>
            </Link>

            {/* Cart trigger */}
            <Sheet open={isCartOpen} onOpenChange={(open) => (open ? openCart() : closeCart())}>
              <SheetTrigger
                className="flex items-end gap-1 px-1 py-0.5 text-white hover:opacity-80"
                aria-label="Cart"
              >
                <div className="relative">
                  <ShoppingCart className="h-6 w-6 sm:h-7 sm:w-7" />
                  {cartCount > 0 && (
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
                  <Link href="/cart" onClick={closeCart}>
                    <button
                      type="button"
                      className="w-full rounded-lg bg-amazon-cart px-4 py-2 text-sm font-semibold text-black hover:brightness-95 disabled:opacity-50"
                      disabled={!cart?.items?.length}
                    >
                      View Cart
                    </button>
                  </Link>
                </div>
              </SheetContent>
            </Sheet>
          </nav>
        </div>

        {/* Secondary bar — Amazon medium dark */}
        <div className="hidden border-t border-white/10 bg-amazon-nav2 sm:block">
          <div className="mx-auto flex h-10 max-w-7xl items-center gap-4 px-6 text-sm text-white">
            <button
              type="button"
              className="flex items-center gap-1 font-bold hover:opacity-80"
              onClick={() => router.push("/products")}
            >
              <Menu className="h-5 w-5" />
              All
            </button>
            <Link href="/products?search=today%27s+deals" className="hover:opacity-80">
              Today&apos;s Deals
            </Link>
            <Link href="/products" className="hover:opacity-80">
              Customer Service
            </Link>
            <Link href="/products" className="hover:opacity-80">
              Gift Cards
            </Link>
            <Link href="/products" className="hover:opacity-80">
              Sell
            </Link>
          </div>
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
