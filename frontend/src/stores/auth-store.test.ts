import { describe, it, expect, beforeEach } from "vitest"
import { useAuthStore } from "./auth-store"

const mockUser = { id: 1, email: "test@test.com", role: "user", is_active: true, is_verified: false }

beforeEach(() => {
  useAuthStore.getState().logout()
  localStorage.clear()
})

describe("auth-store", () => {
  it("starts with null token and user", () => {
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it("login sets token, user, and isAuthenticated", () => {
    useAuthStore.getState().login("tok123", mockUser)
    const state = useAuthStore.getState()
    expect(state.token).toBe("tok123")
    expect(state.user).toEqual(mockUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it("logout clears everything", () => {
    useAuthStore.getState().login("tok123", mockUser)
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it("setUser updates user without changing token", () => {
    useAuthStore.getState().login("tok123", mockUser)
    const updated = { ...mockUser, first_name: "Test" }
    useAuthStore.getState().setUser(updated)
    const state = useAuthStore.getState()
    expect(state.token).toBe("tok123")
    expect(state.user?.first_name).toBe("Test")
  })
})
