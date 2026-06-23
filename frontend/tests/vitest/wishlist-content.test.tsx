import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import WishlistContent from "@/app/wishlist/wishlist-content"

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn(),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
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

beforeEach(() => {
  vi.clearAllMocks()
  mockedAuth.mockReturnValue({ isAuthenticated: true } as any)
  mockedQuery.mockReturnValue({ data: [], isLoading: false } as any)
})

describe("WishlistContent", () => {
  it("shows empty state", () => {
    render(<WishlistContent />)
    expect(screen.getByText("Your wishlist is empty.")).toBeInTheDocument()
  })

  it("shows heading on empty state", () => {
    render(<WishlistContent />)
    expect(screen.getByText("Your Wishlist")).toBeInTheDocument()
  })

  it("shows wishlist items", () => {
    mockedQuery.mockReturnValue({
      data: [
        {
          id: 1,
          product: { id: 1, title: "Wished Product", price: 49.99, discount_percentage: 10, thumbnail: "https://example.com/img.jpg", stock: 5 },
        },
      ],
      isLoading: false,
    } as any)
    render(<WishlistContent />)
    expect(screen.getByText("Wished Product")).toBeInTheDocument()
  })
})
