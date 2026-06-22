"use client"
import dynamic from "next/dynamic"
const WishlistContent = dynamic(() => import("./wishlist-content"), { ssr: false })
export default function WishlistPage() {
  return <WishlistContent />
}
