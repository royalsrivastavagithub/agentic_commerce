"use client"

import dynamic from "next/dynamic"

const ReviewsContent = dynamic(() => import("./reviews-content"), { ssr: false })

export default function ReviewsPage() {
  return <ReviewsContent />
}
