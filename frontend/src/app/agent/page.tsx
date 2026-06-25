"use client"
import dynamic from "next/dynamic"

const AgentChat = dynamic(() => import("@/components/features/agent-chat").then((m) => ({ default: m.AgentChat })), {
  ssr: false,
})

export default function AgentPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <AgentChat />
    </div>
  )
}
