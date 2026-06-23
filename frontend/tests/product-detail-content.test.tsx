import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ReviewSection } from "@/app/products/[id]/product-detail-content"

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(),
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

import { useQuery, useMutation } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"

const mockedAuth = vi.mocked(useAuthStore)
const mockedQuery = vi.mocked(useQuery)
const mockedMutation = vi.mocked(useMutation)

const mockReviews = [
  {
    id: 1,
    user_id: 1,
    product_id: 1,
    rating: 4,
    comment: "Great product!",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    user: { id: 1, email: "alice@test.com", first_name: "Alice" },
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  mockedQuery.mockReturnValue({ data: mockReviews, refetch: vi.fn() } as any)
  mockedMutation.mockReturnValue({ mutate: vi.fn(), isPending: false } as any)
})

describe("ReviewSection", () => {
  it("renders review cards when reviews exist", () => {
    mockedAuth.mockReturnValue({ isAuthenticated: false, user: null } as any)
    render(<ReviewSection productId={1} />)
    expect(screen.getByText("Great product!")).toBeInTheDocument()
    expect(screen.getByText("Alice")).toBeInTheDocument()
  })

  it("renders empty state when no reviews", () => {
    mockedAuth.mockReturnValue({ isAuthenticated: false, user: null } as any)
    mockedQuery.mockReturnValue({ data: [], refetch: vi.fn() } as any)
    render(<ReviewSection productId={1} />)
    expect(screen.getByText("No reviews yet. Be the first to review this product!")).toBeInTheDocument()
  })

  it("shows Write a Review button when authenticated and not already reviewed", () => {
    mockedAuth.mockReturnValue({ isAuthenticated: true, user: { id: 3, email: "new@test.com" } } as any)
    render(<ReviewSection productId={1} />)
    expect(screen.getByText("Write a Review")).toBeInTheDocument()
  })

  it("hides Write button when user already reviewed", () => {
    mockedAuth.mockReturnValue({ isAuthenticated: true, user: { id: 1, email: "alice@test.com" } } as any)
    render(<ReviewSection productId={1} />)
    expect(screen.queryByText("Write a Review")).not.toBeInTheDocument()
    expect(screen.getByText("You have already reviewed this product.")).toBeInTheDocument()
  })

  it("shows review form when Write button is clicked", () => {
    mockedAuth.mockReturnValue({ isAuthenticated: true, user: { id: 3, email: "new@test.com" } } as any)
    render(<ReviewSection productId={1} />)
    fireEvent.click(screen.getByText("Write a Review"))
    expect(screen.getByText("Your Rating")).toBeInTheDocument()
    expect(screen.getByText("Your Review")).toBeInTheDocument()
    expect(screen.getByText("Submit Review")).toBeInTheDocument()
    expect(screen.getByText("Cancel")).toBeInTheDocument()
  })

  it("submits review form successfully", () => {
    const mutate = vi.fn()
    mockedMutation.mockReturnValue({ mutate, isPending: false } as any)
    mockedAuth.mockReturnValue({ isAuthenticated: true, user: { id: 3, email: "new@test.com" } } as any)

    render(<ReviewSection productId={1} />)
    fireEvent.click(screen.getByText("Write a Review"))
    fireEvent.click(screen.getByRole("button", { name: "1 star" })) // click first star
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Great product!" } })
    fireEvent.click(screen.getByText("Submit Review"))

    expect(mutate).toHaveBeenCalledWith({ rating: 1, comment: "Great product!" })
  })
})
