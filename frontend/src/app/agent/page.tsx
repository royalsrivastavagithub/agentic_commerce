"use client"
import dynamic from "next/dynamic"

const AgentChat = dynamic(() => import("@/components/features/agent-chat").then((m) => ({ default: m.AgentChat })), {
  ssr: false,
})

export default function AgentPage() {
  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-7xl flex-col px-4 sm:px-6 lg:px-8">
      <AgentChat />
    </div>
  )
}
