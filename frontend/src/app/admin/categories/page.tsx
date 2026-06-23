"use client"

import dynamic from "next/dynamic"

const CategoriesContent = dynamic(() => import("./categories-content"), { ssr: false })

export default function CategoriesPage() {
  return <CategoriesContent />
}
