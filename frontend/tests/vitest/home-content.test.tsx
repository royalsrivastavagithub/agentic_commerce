import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import HomeContent from "@/app/home-content"

let callCount = 0

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => {
    callCount++
    if (callCount === 1) {
      return { data: { products: [] }, isLoading: false, isError: false } as any
    }
    return { data: { products: [{ id: 1, title: "Deal Item", price: 19.99, rating: 4, thumbnail: "", stock: 5 }] }, isLoading: false, isError: false } as any
  }),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn() },
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

beforeEach(() => {
  callCount = 0
  vi.clearAllMocks()
})

describe("HomeContent", () => {
  it("shows featured products section heading", () => {
    render(<HomeContent />)
    expect(screen.getByText("Featured Products")).toBeInTheDocument()
  })

  it("shows deals section heading", () => {
    render(<HomeContent />)
    expect(screen.getByText("Today's Deals")).toBeInTheDocument()
  })
})
