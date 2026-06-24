import { test, expect } from "@playwright/test"

test.describe("Login flow", () => {
  test("login form loads", async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto("/auth/login")
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible()
    await context.close()
  })

  test("login with valid credentials", async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto("/auth/login")
    await page.fill('input[type="email"]', "alice@test.com")
    await page.fill('input[type="password"]', "test123")
    await page.getByRole("button", { name: "Sign in", exact: true }).click()
    await expect(page).toHaveURL("http://localhost:3000/", { timeout: 10000 })
    await expect(page.getByRole("heading", { name: /Welcome to Agentic Commerce/i })).toBeVisible()
    await context.close()
  })

  test("login with invalid credentials shows error", async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto("/auth/login")
    await page.fill('input[type="email"]', "alice@test.com")
    await page.fill('input[type="password"]', "wrongpass")
    await page.getByRole("button", { name: "Sign in", exact: true }).click()
    await expect(page.getByText("Invalid credentials")).toBeVisible({ timeout: 10000 })
    await context.close()
  })
})

test.describe("Signup", () => {
  test("signup form loads", async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto("/auth/signup")
    await expect(page.getByText("Create Account", { exact: true })).toBeVisible({ timeout: 10000 })
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.getByRole("button", { name: "Create account" })).toBeVisible()
    await context.close()
  })
})

test.describe("Logout", () => {
  test("sign out clears authentication", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByText(/Hello,/)).toBeVisible()
    await page.getByText(/Account & Lists/).click()
    await page.getByRole("menuitem", { name: "Sign Out" }).click()
    await expect(page.getByRole("link", { name: /Sign in/i })).toBeVisible({ timeout: 10000 })
  })
})

test.describe("Protected routes", () => {
  test("redirects to login when not authenticated", async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    await page.goto("/orders")
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 10000 })
    await context.close()
  })
})
