import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import CartContent from "@/app/cart/cart-content"

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn(),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"

const mockedQuery = vi.mocked(useQuery)
const mockedAuth = vi.mocked(useAuthStore)

function makeItem(overrides = {}) {
  return {
    id: 1,
    product_id: 1,
    product: { id: 1, title: "Test Product", price: 29.99, thumbnail: "https://example.com/img.jpg", stock: 10 },
    quantity: 2,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedAuth.mockReturnValue({ isAuthenticated: true } as any)
  mockedQuery.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false } as any)
})

describe("CartContent", () => {
  it("shows empty cart message when no items", () => {
    render(<CartContent />)
    expect(screen.getByText("Your cart is empty")).toBeInTheDocument()
  })

  it("shows items when present", () => {
    mockedQuery.mockReturnValue({
      data: { items: [makeItem()], total: 59.98 },
      isLoading: false,
    } as any)
    render(<CartContent />)
    expect(screen.getByAltText("Test Product")).toBeInTheDocument()
  })

  it("shows proceed to checkout with items", () => {
    mockedQuery.mockReturnValue({
      data: { items: [makeItem()], total: 59.98 },
      isLoading: false,
    } as any)
    render(<CartContent />)
    expect(screen.getByText("Proceed to Checkout")).toBeInTheDocument()
  })
})
