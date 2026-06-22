"use client"

import Link from "next/link"
import { ShoppingCart, Heart, User, Package, Menu, Search, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { useAuthStore } from "@/stores/auth-store"
import { useCartStore } from "@/stores/cart-store"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { Cart } from "@/types/api"
import { useState } from "react"
import { useRouter } from "next/navigation"

export function Shell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout } = useAuthStore()
  const { isCartOpen, openCart, closeCart } = useCartStore()
  const [searchQuery, setSearchQuery] = useState("")
  const router = useRouter()

  const { data: cart } = useQuery({
    queryKey: ["cart"],
    queryFn: () => api.get<Cart>("/cart"),
    enabled: isAuthenticated,
  })

  const initials = user
    ? `${user.first_name?.[0] ?? ""}${user.last_name?.[0] ?? ""}`.toUpperCase() || user.email[0].toUpperCase()
    : "?"

  const cartCount = cart?.items?.reduce((sum, i) => sum + i.quantity, 0) ?? 0
  const cartTotal = cart?.total ?? 0

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b bg-background">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
          <Link href="/products" className="text-xl font-bold tracking-tight">
            Agentic Commerce
          </Link>

          <div className="hidden flex-1 sm:flex sm:max-w-md">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (searchQuery.trim()) router.push(`/products?search=${encodeURIComponent(searchQuery.trim())}`)
              }}
              className="relative w-full"
            >
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </form>
          </div>

          <nav className="ml-auto flex items-center gap-2">
            {isAuthenticated && (
              <>
                <Link href="/wishlist">
                  <Button variant="ghost" size="icon" aria-label="Wishlist">
                    <Heart className="h-5 w-5" />
                  </Button>
                </Link>

                <Sheet open={isCartOpen} onOpenChange={openCart}>
                  <SheetTrigger className="relative inline-flex items-center justify-center rounded-lg p-2 hover:bg-muted" aria-label="Cart">
                    <ShoppingCart className="h-5 w-5" />
                    {cartCount > 0 && (
                      <Badge className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full p-0 text-xs">
                        {cartCount}
                      </Badge>
                    )}
                  </SheetTrigger>
                  <SheetContent className="flex w-full flex-col sm:max-w-md">
                    <SheetHeader>
                      <SheetTitle>Shopping Cart</SheetTitle>
                    </SheetHeader>
                    <div className="flex-1 overflow-auto">
                      {!cart?.items?.length ? (
                        <div className="flex h-full items-center justify-center text-muted-foreground">
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
                                <p className="text-sm font-semibold">
                                  ₹{(item.product.price * item.quantity).toFixed(2)}
                                </p>
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
                        <Button className="w-full" disabled={!cart?.items?.length}>
                          View Cart
                        </Button>
                      </Link>
                    </div>
                  </SheetContent>
                </Sheet>
              </>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-full hover:bg-muted">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {isAuthenticated ? (
                  <>
                    <div className="px-2 py-1.5 text-sm font-medium">{user?.email}</div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <Link href="/orders" className="flex items-center gap-1.5">
                        <Package className="h-4 w-4" />
                        Orders
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Link href="/wishlist" className="flex items-center gap-1.5">
                        <Heart className="h-4 w-4" />
                        Wishlist
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {user?.role === "admin" && (
                      <>
                        <DropdownMenuItem>
                          <Link href="/admin" className="flex items-center gap-1.5">
                            <Menu className="h-4 w-4" />
                            Admin Dashboard
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                      </>
                    )}
                    <DropdownMenuItem
                      onClick={() => {
                        logout()
                        router.push("/products")
                      }}
                      className="cursor-pointer text-destructive"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      Logout
                    </DropdownMenuItem>
                  </>
                ) : (
                  <>
                    <DropdownMenuItem>
                      <Link href="/auth/login" className="flex items-center gap-1.5">
                        <User className="h-4 w-4" />
                        Login
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Link href="/auth/signup" className="flex items-center gap-1.5">
                        <User className="h-4 w-4" />
                        Sign Up
                      </Link>
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t py-8">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-muted-foreground sm:px-6 lg:px-8">
          &copy; {new Date().getFullYear()} Agentic Commerce. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
