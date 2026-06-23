import { describe, it, expect } from "vitest"
import { buildSortParams, buildFilterParams } from "@/lib/filter-utils"

describe("buildSortParams", () => {
  it("returns empty string for default sort", () => {
    expect(buildSortParams("default")).toBe("")
  })

  it("returns price asc params", () => {
    expect(buildSortParams("price-asc")).toBe("&sort_by=price&sort_order=asc")
  })

  it("returns price desc params", () => {
    expect(buildSortParams("price-desc")).toBe("&sort_by=price&sort_order=desc")
  })

  it("returns rating desc params", () => {
    expect(buildSortParams("rating")).toBe("&sort_by=rating&sort_order=desc")
  })

  it("returns title asc params", () => {
    expect(buildSortParams("title-asc")).toBe("&sort_by=title&sort_order=asc")
  })

  it("returns title desc params", () => {
    expect(buildSortParams("title-desc")).toBe("&sort_by=title&sort_order=desc")
  })

  it("returns discount desc params", () => {
    expect(buildSortParams("discount")).toBe("&sort_by=discount&sort_order=desc")
  })

  it("returns empty for unknown sort", () => {
    expect(buildSortParams("unknown")).toBe("")
  })
})

describe("buildFilterParams", () => {
  const priceMin = 0.79
  const priceMax = 36999.99

  it("returns empty string when no filters set", () => {
    expect(buildFilterParams("", "", 0, 0, priceMin, priceMax)).toBe("")
  })

  it("includes min_price when above global minimum", () => {
    const result = buildFilterParams("100", "", 0, 0, priceMin, priceMax)
    expect(result).toContain("&min_price=100")
  })

  it("omits min_price when equal to global minimum", () => {
    const result = buildFilterParams("0.79", "", 0, 0, priceMin, priceMax)
    expect(result).not.toContain("min_price")
  })

  it("includes max_price when below global maximum", () => {
    const result = buildFilterParams("", "500", 0, 0, priceMin, priceMax)
    expect(result).toContain("&max_price=500")
  })

  it("omits max_price when equal to global maximum", () => {
    const result = buildFilterParams("", "36999.99", 0, 0, priceMin, priceMax)
    expect(result).not.toContain("max_price")
  })

  it("includes min_rating when greater than 0", () => {
    const result = buildFilterParams("", "", 4, 0, priceMin, priceMax)
    expect(result).toContain("&min_rating=4")
  })

  it("omits min_rating when 0", () => {
    const result = buildFilterParams("", "", 0, 0, priceMin, priceMax)
    expect(result).not.toContain("min_rating")
  })

  it("includes min_discount when greater than 0", () => {
    const result = buildFilterParams("", "", 0, 10, priceMin, priceMax)
    expect(result).toContain("&min_discount=10")
  })

  it("omits min_discount when 0", () => {
    const result = buildFilterParams("", "", 0, 0, priceMin, priceMax)
    expect(result).not.toContain("min_discount")
  })

  it("combines all filters", () => {
    const result = buildFilterParams("100", "500", 4, 10, priceMin, priceMax)
    expect(result).toContain("&min_price=100")
    expect(result).toContain("&max_price=500")
    expect(result).toContain("&min_rating=4")
    expect(result).toContain("&min_discount=10")
  })
})
