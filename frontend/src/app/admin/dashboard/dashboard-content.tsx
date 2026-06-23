"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api-client"
import type { DashboardSummary, TopProduct, RecentOrder, RecentUser, RevenuePoint } from "@/types/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Users, Package, ShoppingCart, IndianRupee } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const statusBadge: Record<string, string> = {
  PAID: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  CONFIRMED: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  SHIPPED: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  DELIVERED: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  CANCELLED: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
}

function SkeletonCard() { return <div className="h-28 animate-pulse rounded-lg bg-muted" /> }
function SkeletonTable() { return <div className="h-48 animate-pulse rounded-lg bg-muted" /> }

export default function DashboardContent() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["admin-summary"],
    queryFn: () => api.get<DashboardSummary>("/admin/dashboard/summary"),
  })

  const { data: revenue } = useQuery({
    queryKey: ["admin-revenue"],
    queryFn: () => api.get<RevenuePoint[]>("/admin/dashboard/revenue-over-time?days=14"),
  })

  const { data: topProducts } = useQuery({
    queryKey: ["admin-top-products"],
    queryFn: () => api.get<TopProduct[]>("/admin/dashboard/top-products?limit=5"),
  })

  const { data: recentOrders } = useQuery({
    queryKey: ["admin-recent-orders"],
    queryFn: () => api.get<RecentOrder[]>("/admin/dashboard/recent-orders?limit=5"),
  })

  const { data: recentUsers } = useQuery({
    queryKey: ["admin-recent-users"],
    queryFn: () => api.get<RecentUser[]>("/admin/dashboard/recent-users?limit=5"),
  })

  const cards = summary ? [
    { label: "Total Users",    value: summary.total_users,      icon: Users },
    { label: "Total Products", value: summary.total_products,   icon: Package },
    { label: "Total Orders",   value: summary.total_orders,     icon: ShoppingCart },
    { label: "Total Revenue",  value: `₹${summary.total_revenue.toFixed(2)}`, icon: IndianRupee },
  ] : []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryLoading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : cards.map((c) => (
              <Card key={c.label}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">{c.label}</CardTitle>
                  <c.icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{c.value}</div>
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Revenue chart */}
      <Card>
        <CardHeader><CardTitle className="text-base">Revenue (14 days)</CardTitle></CardHeader>
        <CardContent>
          {!revenue
            ? <SkeletonTable />
            : revenue.length === 0
              ? <p className="text-sm text-muted-foreground">No revenue data yet.</p>
              : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={revenue}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="revenue" fill="hsl(221.2, 83.2%, 53.3%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
        </CardContent>
      </Card>

      {/* Top Products + Recent Orders */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Top Products</CardTitle></CardHeader>
          <CardContent>
            {!topProducts
              ? <SkeletonTable />
              : topProducts.length === 0
                ? <p className="text-sm text-muted-foreground">No product sales yet.</p>
                : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Product</TableHead>
                        <TableHead className="text-right">Sold</TableHead>
                        <TableHead className="text-right">Revenue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {topProducts.map((p) => (
                        <TableRow key={p.id}>
                          <TableCell className="font-medium">{p.title}</TableCell>
                          <TableCell className="text-right">{p.total_quantity}</TableCell>
                          <TableCell className="text-right">₹{p.total_revenue.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Recent Orders</CardTitle></CardHeader>
          <CardContent>
            {!recentOrders
              ? <SkeletonTable />
              : recentOrders.length === 0
                ? <p className="text-sm text-muted-foreground">No orders yet.</p>
                : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Order</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recentOrders.map((o) => (
                        <TableRow key={o.id}>
                          <TableCell>#{o.id}</TableCell>
                          <TableCell className="text-muted-foreground">{o.user_email}</TableCell>
                          <TableCell>
                            <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusBadge[o.status] || "bg-gray-100 text-gray-800"}`}>
                              {o.status.toLowerCase()}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">₹{o.total.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Users */}
      <Card>
        <CardHeader><CardTitle className="text-base">Recent Users</CardTitle></CardHeader>
        <CardContent>
          {!recentUsers
            ? <SkeletonTable />
            : recentUsers.length === 0
              ? <p className="text-sm text-muted-foreground">No users yet.</p>
              : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Active</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentUsers.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.email}</TableCell>
                        <TableCell className="text-muted-foreground">{[u.first_name, u.last_name].filter(Boolean).join(" ") || "—"}</TableCell>
                        <TableCell>{u.is_active ? <Badge variant="outline" className="text-green-600">Yes</Badge> : <Badge variant="outline" className="text-red-600">No</Badge>}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
        </CardContent>
      </Card>
    </div>
  )
}
