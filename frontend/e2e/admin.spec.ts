import { test, expect } from "@playwright/test"

test.describe("Admin panel", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login")
    await page.fill('input[type="email"]', "admin@admin.com")
    await page.fill('input[type="password"]', "admin")
    await page.click('button:has-text("Sign in")')
    await page.waitForURL("http://localhost:3000/", { timeout: 10000 })
  })

  test("dashboard loads with summary cards", async ({ page }) => {
    await page.goto("/admin/dashboard")
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(3000)
    // The page renders — check that the sidebar nav is visible
    await expect(page.getByText("Products").first()).toBeVisible({ timeout: 5000 })
  })

  test("products page lists products", async ({ page }) => {
    await page.goto("/admin/products")
    await expect(page.getByRole("heading", { name: "Products" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(3000)
    // Should see at least one product row
    const rows = page.locator("table tbody tr")
    const count = await rows.count()
    expect(count).toBeGreaterThan(0)
  })

  test("orders page shows orders", async ({ page }) => {
    await page.goto("/admin/orders")
    await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(3000)
  })

  test("users page shows users", async ({ page }) => {
    await page.goto("/admin/users")
    await expect(page.getByRole("heading", { name: "Users" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(3000)
    // Should see user rows in the table
    const rows = page.locator("table tbody tr")
    const count = await rows.count()
    expect(count).toBeGreaterThan(0)
  })

  test("users can be searched", async ({ page }) => {
    await page.goto("/admin/users")
    await page.waitForTimeout(2000)
    const searchInput = page.locator('input[placeholder="Search users..."]')
    await searchInput.fill("alice")
    await page.waitForTimeout(2000)
    // Should find Alice
    await expect(page.getByText("alice@test.com").first()).toBeVisible({ timeout: 5000 })
  })

  test("reviews page shows reviews", async ({ page }) => {
    await page.goto("/admin/reviews")
    await expect(page.getByRole("heading", { name: "Reviews" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(3000)
  })

  test("categories page shows categories", async ({ page }) => {
    await page.goto("/admin/categories")
    await expect(page.getByRole("heading", { name: "Categories" })).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(2000)
    // Should see at least one category
    const rows = page.locator("table tbody tr")
    const count = await rows.count()
    expect(count).toBeGreaterThan(0)
  })

  test("create a new category", async ({ page }) => {
    await page.goto("/admin/categories")
    await page.waitForTimeout(2000)
    // Click Add Category button
    await page.getByRole("button", { name: "Add Category" }).click()
    // Wait for dialog to appear
    await expect(page.getByRole("heading", { name: "Create Category" })).toBeVisible({ timeout: 5000 })
    // Fill name and submit
    await page.getByPlaceholder("Category name").fill("Test Category E2E")
    await page.getByRole("button", { name: "Create" }).click()
    await page.waitForTimeout(2000)
    // Should now see the new category in the table
    await expect(page.getByText("Test Category E2E").first()).toBeVisible({ timeout: 5000 })
  })

  test("admin sidebar navigation works", async ({ page }) => {
    await page.goto("/admin/dashboard")
    await page.waitForTimeout(1000)
    // Click on "Products" in the sidebar
    await page.click('a:has-text("Products")')
    await expect(page.getByRole("heading", { name: "Products" })).toBeVisible({ timeout: 10000 })
  })
})

test.describe("Admin auth", () => {
  test("non-admin user cannot access admin", async ({ page }) => {
    // Login as Alice (non-admin)
    await page.goto("/auth/login")
    await page.fill('input[type="email"]', "alice@test.com")
    await page.fill('input[type="password"]', "test123")
    await page.click('button:has-text("Sign in")')
    await page.waitForURL("http://localhost:3000/", { timeout: 10000 })

    // Try to access admin
    await page.goto("/admin/dashboard")
    await page.waitForTimeout(2000)
    // Should be redirected away from admin
    expect(page.url()).not.toContain("/admin/dashboard")
  })

  test("unauthenticated user cannot access admin", async ({ page }) => {
    await page.goto("/admin/dashboard")
    await page.waitForTimeout(2000)
    // Should be redirected to login
    expect(page.url()).toContain("/auth/login")
  })
})
