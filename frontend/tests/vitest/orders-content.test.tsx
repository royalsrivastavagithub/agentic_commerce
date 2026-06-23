import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import OrdersContent from "@/app/orders/orders-content"

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn(),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn() },
}))

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  useSearchParams: vi.fn(() => ({ get: vi.fn() })),
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"

const mockedQuery = vi.mocked(useQuery)
const mockedAuth = vi.mocked(useAuthStore)

beforeEach(() => {
  vi.clearAllMocks()
  mockedAuth.mockReturnValue({ isAuthenticated: true } as any)
  mockedQuery.mockReturnValue({ data: [], isLoading: false } as any)
})

describe("OrdersContent", () => {
  it("shows empty state when no orders", () => {
    render(<OrdersContent />)
    expect(screen.getByText("You haven't placed any orders yet.")).toBeInTheDocument()
  })

  it("shows heading on empty state", () => {
    render(<OrdersContent />)
    expect(screen.getByText("Your Orders")).toBeInTheDocument()
  })

  it("shows order list", () => {
    mockedQuery.mockReturnValue({
      data: [
        {
          id: 1,
          created_at: "2026-01-15T10:00:00Z",
          status: "DELIVERED",
          total: 59.98,
          items: [
            {
              id: 1,
              product_name: "Ordered Item",
              quantity: 2,
              product_price: 29.99,
              subtotal: 59.98,
              thumbnail: "https://example.com/img.jpg",
            },
          ],
        },
      ],
      isLoading: false,
    } as any)
    render(<OrdersContent />)
    expect(screen.getByText(/ORDER PLACED/)).toBeInTheDocument()
  })
})
