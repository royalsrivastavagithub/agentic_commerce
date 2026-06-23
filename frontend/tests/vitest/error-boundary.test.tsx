import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ErrorBoundary } from "@/components/features/error-boundary"

const originalHref = window.location.href

beforeEach(() => {
  vi.clearAllMocks()
  Object.defineProperty(window, "location", {
    value: { ...window.location, href: "/current" },
    writable: true,
  })
})

const GoodChild = () => <div>All good</div>

const BadChild = () => {
  throw new Error("Kaboom!")
}

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>,
    )
    expect(screen.getByText("All good")).toBeInTheDocument()
  })

  it("renders fallback UI when child throws", () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <BadChild />
      </ErrorBoundary>,
    )
    expect(screen.getByText("Something went wrong")).toBeInTheDocument()
    expect(screen.getByText("Kaboom!")).toBeInTheDocument()
    expect(screen.getByText("Go home")).toBeInTheDocument()
    vi.mocked(console.error).mockRestore()
  })

  it("shows generic message when error has no message", () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    const ReallyBad = () => {
      throw new Error()
    }
    render(
      <ErrorBoundary>
        <ReallyBad />
      </ErrorBoundary>,
    )
    expect(screen.getByText("An unexpected error occurred")).toBeInTheDocument()
    vi.mocked(console.error).mockRestore()
  })

  it("shows custom fallback when provided", () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    render(
      <ErrorBoundary fallback={<div>Custom error</div>}>
        <BadChild />
      </ErrorBoundary>,
    )
    expect(screen.getByText("Custom error")).toBeInTheDocument()
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument()
    vi.mocked(console.error).mockRestore()
  })

  it("navigates home on Go home click", () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <BadChild />
      </ErrorBoundary>,
    )
    fireEvent.click(screen.getByText("Go home"))
    expect(window.location.href).toBe("/")
    vi.mocked(console.error).mockRestore()
  })
})
