"use client"

import dynamic from "next/dynamic"

const ProductsContent = dynamic(() => import("./products-content"), { ssr: false })

export default function ProductsPage() {
  return <ProductsContent />
}
