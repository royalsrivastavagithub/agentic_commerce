import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"

const mockSearchParamsGet = vi.fn()
vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockSearchParamsGet }),
}))

vi.mock("@/lib/api-client", () => ({
  api: { get: vi.fn() },
}))

vi.mock("@/components/features/dynamic-shell", () => ({
  DynamicShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import VerifyEmailContent from "@/app/auth/verify-email/verify-email-content"
import { api } from "@/lib/api-client"

const mockedGet = vi.mocked(api.get)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("VerifyEmailContent", () => {
  it("shows loading state initially", () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedGet.mockImplementation(() => new Promise(() => {}))
    render(<VerifyEmailContent />)
    expect(screen.getByText("Verifying...")).toBeInTheDocument()
    expect(screen.getByText("Please wait while we verify your email...")).toBeInTheDocument()
  })

  it("shows success state on valid token", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedGet.mockResolvedValue({ message: "Email verified successfully", email: "a@b.com", is_verified: true })
    render(<VerifyEmailContent />)
    await waitFor(() => {
      expect(screen.getByText("Email Verified")).toBeInTheDocument()
    })
    expect(screen.getByText("Go to Login")).toBeInTheDocument()
  })

  it("shows success state even for invalid token (quirk)", async () => {
    mockSearchParamsGet.mockReturnValue("used-token")
    mockedGet.mockRejectedValue(new Error("Invalid or expired verification token"))
    render(<VerifyEmailContent />)
    await waitFor(() => {
      expect(screen.getByText("Email Verified")).toBeInTheDocument()
      expect(screen.getByText("Go to Login")).toBeInTheDocument()
    })
  })

  it("shows error state on api failure", async () => {
    mockSearchParamsGet.mockReturnValue("valid-token")
    mockedGet.mockRejectedValue(new Error("Server error"))
    render(<VerifyEmailContent />)
    await waitFor(() => {
      expect(screen.getByText("Verification Failed")).toBeInTheDocument()
    })
    expect(screen.getByText("Back to Login")).toBeInTheDocument()
  })

  it("shows error state when no token", async () => {
    mockSearchParamsGet.mockReturnValue(null)
    render(<VerifyEmailContent />)
    await waitFor(() => {
      expect(screen.getByText("Verification Failed")).toBeInTheDocument()
    })
    expect(screen.getByText("No verification token provided.")).toBeInTheDocument()
  })
})
