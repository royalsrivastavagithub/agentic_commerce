"use client"

import { useAuthStore } from "@/stores/auth-store"
import { useRouter, usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"
import { Menu, LayoutDashboard, Package, ShoppingCart, Users, Star, Tags } from "lucide-react"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

const navItems = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/products",  label: "Products",  icon: Package },
  { href: "/admin/orders",    label: "Orders",    icon: ShoppingCart },
  { href: "/admin/users",     label: "Users",     icon: Users },
  { href: "/admin/reviews",   label: "Reviews",   icon: Star },
  { href: "/admin/categories",label: "Categories",icon: Tags },
]

function NavLink({ href, label, icon: Icon, onClick }: { href: string; label: string; icon: React.ComponentType<{ className?: string }>; onClick?: () => void }) {
  const pathname = usePathname()
  const active = pathname === href || pathname.startsWith(href + "/")
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
        active
          ? "bg-accent text-accent-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </Link>
  )
}

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
      {/* Mobile sidebar trigger */}
      <div className="fixed left-0 right-0 top-0 z-40 flex items-center gap-2 border-b bg-background px-4 py-2 md:hidden">
        <Sheet>
          <SheetTrigger className="p-1 hover:text-foreground/80" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="p-4">
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
            </div>
          </SheetContent>
        </Sheet>
        <span className="text-sm font-medium">Agentic Commerce Admin</span>
      </div>

      <aside className="hidden w-56 shrink-0 border-r bg-muted/30 p-4 md:block">
        <Link href="/admin/dashboard" className="mb-6 block text-lg font-bold">Admin</Link>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink key={item.href} href={item.href} label={item.label} icon={item.icon} />
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-4 pt-14 md:p-6 md:pt-6">{children}</main>
    </div>
  )
}
