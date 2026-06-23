"use client"

import { useAuthStore } from "@/stores/auth-store"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"
import {
  LayoutDashboard, Package, ShoppingCart, Users, Star, Tags,
} from "lucide-react"

const navItems = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/products",  label: "Products",  icon: Package },
  { href: "/admin/orders",    label: "Orders",    icon: ShoppingCart },
  { href: "/admin/users",     label: "Users",     icon: Users },
  { href: "/admin/reviews",   label: "Reviews",   icon: Star },
  { href: "/admin/categories",label: "Categories",icon: Tags },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  useEffect(() => {
    if (!mounted) return
    if (!isAuthenticated) router.push("/auth/login")
    else if (user?.role !== "admin") router.push("/")
  }, [mounted, isAuthenticated, user, router])

  if (!mounted || !isAuthenticated || user?.role !== "admin") return null

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r bg-muted/30 p-4 hidden md:block">
        <Link href="/admin/dashboard" className="mb-6 block text-lg font-bold">Admin</Link>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
