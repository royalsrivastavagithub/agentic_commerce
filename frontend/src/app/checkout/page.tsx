"use client"
import dynamic from "next/dynamic"
const CheckoutContent = dynamic(() => import("./checkout-content"), { ssr: false })
export default function CheckoutPage() {
  return <CheckoutContent />
}
