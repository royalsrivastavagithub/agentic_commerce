import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

vi.mock("@/lib/api-client", () => ({
  api: { post: vi.fn() },
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ push: vi.fn() })),
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import ForgotPasswordContent from "@/app/auth/forgot-password/forgot-password-content"
import { api } from "@/lib/api-client"

const mockedApiPost = vi.mocked(api.post)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("ForgotPasswordContent", () => {
  it("renders the form with email field", () => {
    render(<ForgotPasswordContent />)
    expect(screen.getByText("Forgot Password")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument()
    expect(screen.getByText("Send Reset Link")).toBeInTheDocument()
  })

  it("calls api and shows sent message on success", async () => {
    mockedApiPost.mockResolvedValue({ message: "If an account with that email exists..." })
    render(<ForgotPasswordContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "user@test.com" } })
    fireEvent.click(screen.getByText("Send Reset Link"))
    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/auth/forgot-password", { email: "user@test.com" })
    })
    expect(screen.getByText("Check your email for a password reset link.")).toBeInTheDocument()
  })

  it("shows sent message even on api failure", async () => {
    mockedApiPost.mockRejectedValue(new Error("Network error"))
    render(<ForgotPasswordContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "fail@test.com" } })
    fireEvent.click(screen.getByText("Send Reset Link"))
    await waitFor(() => {
      expect(screen.getByText("Check your email for a password reset link.")).toBeInTheDocument()
    })
  })

  it("disables button while loading", async () => {
    mockedApiPost.mockImplementation(() => new Promise(() => {}))
    render(<ForgotPasswordContent />)
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "a@b.com" } })
    fireEvent.click(screen.getByText("Send Reset Link"))
    await waitFor(() => {
      expect(screen.getByText("Sending...")).toBeInTheDocument()
    })
  })

  it("shows back to login link", () => {
    render(<ForgotPasswordContent />)
    expect(screen.getByText("Back to Login")).toBeInTheDocument()
  })
})
