"use client"

import dynamic from "next/dynamic"

const OrdersContent = dynamic(() => import("./orders-content"), { ssr: false })

export default function OrdersPage() {
  return <OrdersContent />
}
