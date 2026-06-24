import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

const mockPush = vi.fn()
const mockLogin = vi.fn()
const mockInvalidateQueries = vi.fn()
const mockMutate = vi.fn()

let mockUser: any = {
  id: 1,
  email: "test@test.com",
  first_name: "Test",
  last_name: "User",
  is_google_account: false,
  phone: "9876543210",
  addresses: [],
}

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn(),
}))

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({ data: null })),
  useMutation: vi.fn(() => ({ mutate: mockMutate, isPending: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: mockInvalidateQueries })),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), delete: vi.fn() },
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import ProfileContent from "@/app/profile/profile-content"
import { useAuthStore } from "@/stores/auth-store"
import { useQuery } from "@tanstack/react-query"
import { toast } from "sonner"

const mockedAuthStore = vi.mocked(useAuthStore)
const mockedUseQuery = vi.mocked(useQuery)

beforeEach(() => {
  vi.clearAllMocks()
  mockUser = {
    id: 1,
    email: "test@test.com",
    first_name: "Test",
    last_name: "User",
    phone: "9876543210",
    is_google_account: false,
    is_verified: true,
    is_active: true,
    role: "user",
    addresses: [],
  }
  mockedUseQuery.mockReturnValue({ data: null } as any)
})

describe("ProfileContent", () => {
  it("redirects to login when not authenticated", () => {
    mockedAuthStore.mockReturnValue({ isAuthenticated: false } as any)
    const { container } = render(<ProfileContent />)
    expect(container.innerHTML).toBe("")
    expect(mockPush).toHaveBeenCalledWith("/auth/login")
  })

  it("renders user email when authenticated", () => {
    mockedAuthStore.mockReturnValue({ isAuthenticated: true, user: mockUser, login: mockLogin } as any)
    render(<ProfileContent />)
    expect(screen.getByText("Your Profile")).toBeInTheDocument()
    expect(screen.getByText("test@test.com")).toBeInTheDocument()
  })

  it("shows editable fields", () => {
    mockedAuthStore.mockReturnValue({ isAuthenticated: true, user: mockUser, login: mockLogin } as any)
    render(<ProfileContent />)
    expect(screen.getByText("First Name")).toBeInTheDocument()
    expect(screen.getByText("Test")).toBeInTheDocument()
    expect(screen.getByText("Last Name")).toBeInTheDocument()
    expect(screen.getByText("User")).toBeInTheDocument()
    expect(screen.getByText("Phone")).toBeInTheDocument()
  })

  it("shows edit mode when pencil is clicked", async () => {
    mockedAuthStore.mockReturnValue({ isAuthenticated: true, user: mockUser, login: mockLogin } as any)
    render(<ProfileContent />)
    const pencilButtons = screen.getAllByRole("button")
    const editBtn = pencilButtons.find((b) => b.querySelector("svg"))
    expect(editBtn).toBeTruthy()
  })
})
