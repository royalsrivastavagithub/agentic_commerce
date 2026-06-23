import { describe, it, expect } from "vitest"
import { cn } from "@/lib/utils"

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("px-4", "py-2")).toBe("px-4 py-2")
  })

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "extra")).toBe("base extra")
  })

  it("resolves tailwind conflicts (later wins)", () => {
    expect(cn("px-4", "px-6")).toBe("px-6")
  })

  it("returns empty string for no args", () => {
    expect(cn()).toBe("")
  })
})
