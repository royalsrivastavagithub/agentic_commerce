import { describe, it, expect } from "vitest"
import { decodeToken, isTokenExpired } from "@/lib/auth"

describe("decodeToken", () => {
  it("returns payload for a valid token", () => {
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6InVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.abc"
    const payload = decodeToken(token)
    expect(payload).not.toBeNull()
    expect(payload!.sub).toBe("1")
    expect(payload!.role).toBe("user")
  })

  it("returns null for malformed token", () => {
    expect(decodeToken("not-a-token")).toBeNull()
  })

  it("returns null for empty string", () => {
    expect(decodeToken("")).toBeNull()
  })
})

describe("isTokenExpired", () => {
  it("returns false for token with future expiry", () => {
    const future = Math.floor(Date.now() / 1000) + 3600
    const payload = btoa(JSON.stringify({ sub: "1", role: "user", exp: future }))
    const token = `header.${payload}.sig`
    expect(isTokenExpired(token)).toBe(false)
  })

  it("returns true for token with past expiry", () => {
    const past = Math.floor(Date.now() / 1000) - 3600
    const payload = btoa(JSON.stringify({ sub: "1", role: "user", exp: past }))
    const token = `header.${payload}.sig`
    expect(isTokenExpired(token)).toBe(true)
  })

  it("returns true for token with no exp", () => {
    const payload = btoa(JSON.stringify({ sub: "1", role: "user" }))
    const token = `header.${payload}.sig`
    expect(isTokenExpired(token)).toBe(true)
  })

  it("returns true for malformed token", () => {
    expect(isTokenExpired("bad")).toBe(true)
  })
})
