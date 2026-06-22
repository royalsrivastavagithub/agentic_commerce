"use client"
import dynamic from "next/dynamic"
const OrderDetailContent = dynamic(() => import("./order-detail-content"), { ssr: false })
export default function OrderDetailPage() {
  return <OrderDetailContent />
}
