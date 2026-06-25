"use client"

import { useState, useRef, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { api, ApiError } from "@/lib/api-client"
import { useAuthStore } from "@/stores/auth-store"
import { Send, Bot, User, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ProductCard } from "@/components/ui/product-card"
import type { Product, ChatResponse } from "@/types/api"

interface Message {
  role: "user" | "assistant"
  content: string
  products?: Product[]
}

const WELCOME: Message = {
  role: "assistant",
  content:
    "Hi! I'm your AI shopping assistant. I can help you find products, browse categories, check your cart, and more. What are you looking for today?",
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = sessionStorage.getItem("agent-chat-messages")
        if (saved) return JSON.parse(saved) as Message[]
      } catch { /* ignore */ }
    }
    return [WELCOME]
  })
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    sessionStorage.setItem("agent-chat-messages", JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    inputRef.current?.focus()
  }, [loading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    const history = messages.slice(1).map((m) => ({ role: m.role, content: m.content }))

    setMessages((prev) => [...prev, { role: "user", content: text }])
    setInput("")
    setLoading(true)
    setError(null)

    try {
      const data = await api.post<ChatResponse>("/chat", {
        message: text,
        history,
      })
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response || "I'm not sure how to respond to that.", products: data.products },
      ])
    } catch (err) {
      const detail =
        err instanceof ApiError ? err.message : "Something went wrong. Please try again."
      setError(detail)
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ ${detail}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="mb-2 text-xl font-semibold">Sign in required</h2>
          <p className="text-muted-foreground">Please sign in to use the AI shopping assistant.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex flex-1 flex-col overflow-hidden rounded-lg border bg-card">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                {msg.role === "assistant" ? (
                  <>
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                    {msg.products && msg.products.length > 0 && (
                      <div className="mt-3 space-y-3">
                        {msg.products.map((p) => (
                          <ProductCard key={p.id} product={p} newTab />
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-sm">{msg.content}</div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20">
                  <User className="h-4 w-4 text-primary" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="rounded-lg bg-muted px-4 py-2.5">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me about products..."
              disabled={loading}
              className="flex-1 rounded-md border bg-background px-3 py-2 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
            />
            <Button type="submit" size="icon" disabled={loading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
          {error && !loading && (
            <p className="mt-2 text-xs text-destructive">{error}</p>
          )}
        </div>
      </div>
    </div>
  )
}
