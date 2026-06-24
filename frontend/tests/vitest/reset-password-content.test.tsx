import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"

const mockSearchParamsGet = vi.fn()
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockSearchParamsGet }),
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}))

vi.mock("@/lib/api-client", () => ({
  api: { post: vi.fn() },
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import ResetPasswordContent from "@/app/auth/reset-password/reset-password-content"
import { api } from "@/lib/api-client"

const mockedApiPost = vi.mocked(api.post)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("ResetPasswordContent", () => {
  it("shows invalid link view when no token", () => {
    mockSearchParamsGet.mockReturnValue(null)
    render(<ResetPasswordContent />)
    expect(screen.getByText("Invalid Link")).toBeInTheDocument()
    expect(screen.getByText("Request Reset")).toBeInTheDocument()
  })

  it("renders form when token is present", () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    render(<ResetPasswordContent />)
    expect(screen.getByText("Enter your new password.")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Reset Password" })).toBeInTheDocument()
  })

  it("shows validation error for short password", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    render(<ResetPasswordContent />)
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "short" } })
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "short" } })
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }))
    await waitFor(() => {
      expect(screen.getByText("Password must be at least 8 characters")).toBeInTheDocument()
    })
  })

  it("shows validation error for mismatched passwords", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    render(<ResetPasswordContent />)
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "LongEnough1!" } })
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "Different1!" } })
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }))
    await waitFor(() => {
      expect(screen.getByText("Passwords do not match")).toBeInTheDocument()
    })
  })

  it("shows invalid link view for empty token string", () => {
    mockSearchParamsGet.mockReturnValue("")
    render(<ResetPasswordContent />)
    expect(screen.getByText("Invalid Link")).toBeInTheDocument()
    expect(screen.getByText("Request Reset")).toBeInTheDocument()
  })

  it("calls api and shows success on valid submission", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedApiPost.mockResolvedValue({ message: "Password reset successfully" })
    render(<ResetPasswordContent />)
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }))
    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/auth/reset-password", {
        token: "valid-token",
        new_password: "N3wP@ss!x",
      })
    })
    expect(screen.getByText("Password Reset")).toBeInTheDocument()
    expect(screen.getByText("Your password has been reset successfully.")).toBeInTheDocument()
    expect(screen.getByText("Go to Login")).toBeInTheDocument()
  })

  it("shows error on api failure", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedApiPost.mockRejectedValue(new Error("Invalid or expired reset token"))
    render(<ResetPasswordContent />)
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }))
    await waitFor(() => {
      expect(screen.getByText("Invalid or expired reset token")).toBeInTheDocument()
    })
  })

  it("disables button while loading", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedApiPost.mockImplementation(() => new Promise(() => {}))
    render(<ResetPasswordContent />)
    fireEvent.change(screen.getByLabelText("New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.change(screen.getByLabelText("Confirm New Password"), { target: { value: "N3wP@ss!x" } })
    fireEvent.click(screen.getByRole("button", { name: "Reset Password" }))
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Resetting..." })).toBeInTheDocument()
    })
  })
})
