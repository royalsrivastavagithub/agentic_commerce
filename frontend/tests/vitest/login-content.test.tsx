import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
vi.mock("@react-oauth/google", () => ({
  GoogleLogin: ({ onSuccess, onError, ...props }: any) => (
    <div data-testid="google-login" data-props={JSON.stringify(props)}>Google</div>
  ),
}))

import LoginContent from "@/app/auth/login/login-content"

const mockPush = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: mockPush })),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: vi.fn(),
}))

vi.mock("@/lib/api-client", () => ({
  api: { post: vi.fn() },
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { api } from "@/lib/api-client"
import { useAuthStore } from "@/stores/auth-store"
import { toast } from "sonner"

const mockedApiPost = vi.mocked(api.post)
const mockedAuthStore = vi.mocked(useAuthStore)

beforeEach(() => {
  vi.clearAllMocks()
  mockPush.mockReset()
  mockedAuthStore.mockReturnValue({ login: vi.fn() } as any)
})

describe("LoginContent", () => {
  it("renders login form with email and password", () => {
    render(<LoginContent />)
    expect(screen.getByText("Login")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument()
    expect(screen.getByText("Sign in")).toBeInTheDocument()
  })

  it("renders Google sign-in button", async () => {
    render(<LoginContent />)
    expect(await screen.findByTestId("google-login")).toBeInTheDocument()
  })

  it("renders sign up link", () => {
    render(<LoginContent />)
    expect(screen.getByText("Sign up")).toBeInTheDocument()
  })

  it("submits form and navigates on success", async () => {
    const login = vi.fn()
    mockedAuthStore.mockReturnValue({ login } as any)
    mockedApiPost.mockResolvedValue({
      access_token: "tok",
      token_type: "bearer",
      user: { id: 1, email: "a@b.com", role: "user" },
    })

    render(<LoginContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "a@b.com" } })
    fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "secret" } })
    fireEvent.click(screen.getByText("Sign in"))

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/auth/login", {
        email: "a@b.com",
        password: "secret",
      })
    })
    expect(login).toHaveBeenCalledWith("tok", { id: 1, email: "a@b.com", role: "user" })
    expect(toast.success).toHaveBeenCalledWith("Logged in successfully")
    expect(mockPush).toHaveBeenCalledWith("/")
  })

  it("shows error toast on login failure", async () => {
    mockedApiPost.mockRejectedValue(new Error("Invalid credentials"))

    render(<LoginContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "bad@test.com" } })
    fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "wrong" } })
    fireEvent.click(screen.getByText("Sign in"))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Invalid credentials")
    })
  })

  it("disables button while loading", async () => {
    mockedApiPost.mockImplementation(() => new Promise(() => {})) // never resolves

    render(<LoginContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "a@b.com" } })
    fireEvent.change(screen.getByPlaceholderText("••••••••"), { target: { value: "pw" } })
    fireEvent.click(screen.getByText("Sign in"))

    await waitFor(() => {
      expect(screen.getByText("Signing in...")).toBeInTheDocument()
    })
  })
})
