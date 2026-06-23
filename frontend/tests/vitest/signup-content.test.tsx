import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import SignupContent from "@/app/auth/signup/signup-content"

vi.mock("@/lib/api-client", () => ({
  api: { post: vi.fn() },
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

import { api } from "@/lib/api-client"

const mockedApiPost = vi.mocked(api.post)
import { toast } from "sonner"

beforeEach(() => {
  vi.clearAllMocks()
})

describe("SignupContent", () => {
  it("renders the form with all fields", () => {
    render(<SignupContent />)
    expect(screen.getByText("Create Account")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument()
    expect(screen.getByText("Create account")).toBeInTheDocument()
    expect(screen.getByText("Sign in")).toBeInTheDocument()
  })

  it("submits form and shows success state", async () => {
    mockedApiPost.mockResolvedValue({
      id: 1,
      email: "new@test.com",
      role: "user",
      is_active: true,
      is_verified: false,
    })

    const { container } = render(<SignupContent />)

    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "new@test.com" } })
    const passwordInputs = screen.getAllByPlaceholderText("••••••••")
    fireEvent.change(passwordInputs[0], { target: { value: "StrongP@ss1" } })
    fireEvent.change(container.querySelector("#first_name")!, { target: { value: "New" } })
    fireEvent.change(container.querySelector("#last_name")!, { target: { value: "User" } })
    fireEvent.change(container.querySelector("#phone")!, { target: { value: "9876543210" } })
    fireEvent.change(container.querySelector("#gender")!, { target: { value: "male" } })
    const dayInput = screen.getByPlaceholderText("DD")
    fireEvent.change(dayInput, { target: { value: "15" } })
    const monthInput = screen.getByPlaceholderText("MM")
    fireEvent.change(monthInput, { target: { value: "06" } })
    const yearInput = screen.getByPlaceholderText("YYYY")
    fireEvent.change(yearInput, { target: { value: "2000" } })

    fireEvent.click(screen.getByText("Create account"))

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalled()
    })
    expect(toast.success).toHaveBeenCalled()
  })

  it("shows error toast on signup failure", async () => {
    mockedApiPost.mockRejectedValue(new Error("Email already registered"))

    const { container } = render(<SignupContent />)

    fireEvent.change(screen.getByPlaceholderText("you@example.com"), { target: { value: "exists@test.com" } })
    const passwordInputs = screen.getAllByPlaceholderText("••••••••")
    fireEvent.change(passwordInputs[0], { target: { value: "StrongP@ss1" } })
    fireEvent.change(container.querySelector("#first_name")!, { target: { value: "A" } })
    fireEvent.change(container.querySelector("#last_name")!, { target: { value: "B" } })
    fireEvent.change(container.querySelector("#phone")!, { target: { value: "9876543210" } })
    fireEvent.change(container.querySelector("#gender")!, { target: { value: "male" } })
    fireEvent.change(screen.getByPlaceholderText("DD"), { target: { value: "15" } })
    fireEvent.change(screen.getByPlaceholderText("MM"), { target: { value: "06" } })
    fireEvent.change(screen.getByPlaceholderText("YYYY"), { target: { value: "2000" } })
    fireEvent.click(screen.getByText("Create account"))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Email already registered")
    })
  })
})
