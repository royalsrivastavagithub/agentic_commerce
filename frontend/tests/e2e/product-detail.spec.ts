import { test, expect } from "@playwright/test"

test.describe("Product detail", () => {
  test("product page shows basic info", async ({ page }) => {
    await page.goto("/products/1")
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 10000 })
    const stockText = page.getByText("In Stock").or(page.getByText("Currently Unavailable"))
    await expect(stockText).toBeVisible()
  })

  test("customer reviews section is present", async ({ page }) => {
    await page.goto("/products/2")
    await expect(page.getByText("Customer Reviews")).toBeVisible({ timeout: 10000 })
  })

  test("write review form is accessible", async ({ page }) => {
    await page.goto("/products/150")
    const writeBtn = page.getByRole("button", { name: "Write a Review" })
    await expect(writeBtn).toBeVisible({ timeout: 10000 })
    await writeBtn.click()
    await expect(page.getByText("Your Rating")).toBeVisible()
    await expect(page.getByPlaceholder("Share your thoughts about this product...")).toBeVisible()
  })
})

test.describe("Add to cart", () => {
  test("add to cart from product page", async ({ page }) => {
    await page.goto("/products/1")
    const addBtn = page.getByRole("button", { name: "Add to Cart" })
    await expect(addBtn).toBeVisible({ timeout: 10000 })
    await addBtn.click()
  })
})

test.describe("Wishlist", () => {
  test("add to wishlist button is present", async ({ page }) => {
    await page.goto("/products/3")
    await expect(page.getByText(/Hello,/)).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole("button", { name: /Wishlist/ })).toBeVisible({ timeout: 10000 })
  })
})
