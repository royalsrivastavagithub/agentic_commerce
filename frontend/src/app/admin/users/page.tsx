"use client"

import dynamic from "next/dynamic"

const UsersContent = dynamic(() => import("./users-content"), { ssr: false })

export default function UsersPage() {
  return <UsersContent />
}
