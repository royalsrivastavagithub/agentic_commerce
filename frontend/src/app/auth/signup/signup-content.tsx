"use client"

import { useState } from "react"
import Link from "next/link"
import { api } from "@/lib/api-client"
import type { User } from "@/types/api"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"
import { DynamicShell as Shell } from "@/components/features/dynamic-shell"

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9\s])[\S]{8,16}$/
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface FieldErrors {
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  date_of_birth?: string
  gender?: string
  password?: string
}

export default function SignupContent() {
  const [form, setForm] = useState({
    email: "", password: "", first_name: "", last_name: "",
    phone: "", date_of_birth: "", gender: "",
  })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [touched, setTouched] = useState<Set<string>>(new Set())

  const markTouched = (field: string) => {
    setTouched((prev) => new Set(prev).add(field))
  }

  const validate = (): FieldErrors => {
    const errs: FieldErrors = {}
    if (!form.first_name?.trim()) errs.first_name = "First name is required"
    if (!form.last_name?.trim()) errs.last_name = "Last name is required"
    if (!form.email?.trim()) errs.email = "Email is required"
    else if (!EMAIL_REGEX.test(form.email)) errs.email = "Enter a valid email address"
    if (!form.password) errs.password = "Password is required"
    else if (form.password.length < 8 || form.password.length > 16) errs.password = "Password must be 8–16 characters"
    else if (!PASSWORD_REGEX.test(form.password)) errs.password = "Must include uppercase, lowercase, digit, and symbol"
    if (!form.phone?.trim()) errs.phone = "Phone is required"
    if (!form.date_of_birth || !/^\d{4}-\d{2}-\d{2}$/.test(form.date_of_birth)) errs.date_of_birth = "Date of birth is required"
    if (!form.gender) errs.gender = "Please select a gender"

    return errs
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs = validate()
    setErrors(errs)
    Object.keys(errs).forEach(markTouched)
    if (Object.keys(errs).length > 0) return

    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.phone) payload.phone = ""
      if (!payload.gender) payload.gender = ""

      await api.post<User>("/auth/signup", payload)
      setDone(true)
      toast.success("Account created! You can now log in.")
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Signup failed")
    } finally {
      setLoading(false)
    }
  }

  const showError = (field: string) => touched.has(field) && errors[field as keyof FieldErrors]

  if (done) {
    return (
      <Shell>
        <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl font-bold">Account Created</CardTitle>
              <CardDescription>You can now sign in with your credentials</CardDescription>
            </CardHeader>
            <CardFooter>
              <Link href="/auth/login" className={buttonVariants({ className: "w-full" })}>
                Go to Login
              </Link>
            </CardFooter>
          </Card>
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
            <CardDescription>Sign up for a new account</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit} noValidate>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FieldWrap label="First Name *" error={showError("first_name") ? errors.first_name : undefined}>
                  <Input
                    id="first_name"
                    value={form.first_name}
                    onChange={(e) => { setForm((f) => ({ ...f, first_name: e.target.value })); setErrors((prev) => ({ ...prev, first_name: undefined })) }}
                    onBlur={() => markTouched("first_name")}
                  />
                </FieldWrap>
                <FieldWrap label="Last Name *" error={showError("last_name") ? errors.last_name : undefined}>
                  <Input
                    id="last_name"
                    value={form.last_name}
                    onChange={(e) => { setForm((f) => ({ ...f, last_name: e.target.value })); setErrors((prev) => ({ ...prev, last_name: undefined })) }}
                    onBlur={() => markTouched("last_name")}
                  />
                </FieldWrap>
              </div>
              <FieldWrap label="Email *" error={showError("email") ? errors.email : undefined}>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={(e) => { setForm((f) => ({ ...f, email: e.target.value })); setErrors((prev) => ({ ...prev, email: undefined })) }}
                  onBlur={() => markTouched("email")}
                />
              </FieldWrap>
              <FieldWrap label="Phone *" error={showError("phone") ? errors.phone : undefined}>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+91 9876543210"
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                />
              </FieldWrap>
              <div className="grid grid-cols-2 gap-4">
                <FieldWrap label="Date of Birth *" error={showError("date_of_birth") ? errors.date_of_birth : undefined}>
                  <div className="flex items-center gap-1">
                    <input
                      type="text" inputMode="numeric" maxLength={2} placeholder="DD"
                      value={form.date_of_birth ? (() => { const [y,m,d] = form.date_of_birth.split("-"); return ["",undefined].includes(d)?"":d })() : ""}
                      onChange={(e) => {
                        const d = e.target.value.replace(/\D/g, "").slice(0,2)
                        const [y,m] = form.date_of_birth ? form.date_of_birth.split("-") : ["",""]
                        setForm((f) => ({ ...f, date_of_birth: `${y||""}-${m||""}-${d}` }))
                        setErrors((prev) => ({ ...prev, date_of_birth: undefined }))
                        if (d.length === 2) (e.target.nextElementSibling as HTMLElement)?.focus()
                      }}
                      onBlur={() => {
                        markTouched("date_of_birth")
                        const d = form.date_of_birth?.split("-")[2]
                        if (d && d.length === 1) {
                          const [y,m] = form.date_of_birth ? form.date_of_birth.split("-") : ["",""]
                          setForm((f) => ({ ...f, date_of_birth: `${y||""}-${m||""}-0${d}` }))
                        }
                      }}
                      className="w-12 rounded border border-input bg-background px-2 py-2 text-sm text-center outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                    />
                    <span className="text-muted-foreground">/</span>
                    <input
                      type="text" inputMode="numeric" maxLength={2} placeholder="MM"
                      value={form.date_of_birth ? (() => { const [y,m] = form.date_of_birth.split("-"); return ["",undefined].includes(m)?"":m })() : ""}
                      onChange={(e) => {
                        const m = e.target.value.replace(/\D/g, "").slice(0,2)
                        const [y,,d] = form.date_of_birth ? form.date_of_birth.split("-") : ["","",""]
                        setForm((f) => ({ ...f, date_of_birth: `${y||""}-${m}-${d||""}` }))
                        setErrors((prev) => ({ ...prev, date_of_birth: undefined }))
                        if (m.length === 2) setTimeout(() => (e.target.nextElementSibling?.nextElementSibling as HTMLElement)?.focus(), 10)
                      }}
                      onBlur={() => {
                        markTouched("date_of_birth")
                        const m = form.date_of_birth?.split("-")[1]
                        if (m && m.length === 1) {
                          const [y,,d] = form.date_of_birth ? form.date_of_birth.split("-") : ["","",""]
                          setForm((f) => ({ ...f, date_of_birth: `${y||""}-0${m}-${d||""}` }))
                        }
                      }}
                      className="w-12 rounded border border-input bg-background px-2 py-2 text-sm text-center outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                    />
                    <span className="text-muted-foreground">/</span>
                    <input
                      type="text" inputMode="numeric" maxLength={4} placeholder="YYYY"
                      value={form.date_of_birth ? (() => { const [y] = form.date_of_birth.split("-"); return ["",undefined].includes(y)?"":y })() : ""}
                      onChange={(e) => {
                        const y = e.target.value.replace(/\D/g, "").slice(0,4)
                        const [,m,d] = form.date_of_birth ? form.date_of_birth.split("-") : ["","",""]
                        setForm((f) => ({ ...f, date_of_birth: `${y}-${m||""}-${d||""}` }))
                        setErrors((prev) => ({ ...prev, date_of_birth: undefined }))
                      }}
                      onBlur={() => markTouched("date_of_birth")}
                      className="w-14 rounded border border-input bg-background px-2 py-2 text-sm text-center outline-none focus:border-amazon-link dark:border-border dark:bg-card"
                    />
                  </div>
                </FieldWrap>
                <FieldWrap label="Gender *" error={showError("gender") ? errors.gender : undefined}>
                  <select
                    id="gender"
                    value={form.gender}
                    onChange={(e) => { setForm((f) => ({ ...f, gender: e.target.value })); setErrors((prev) => ({ ...prev, gender: undefined })) }}
                    onBlur={() => markTouched("gender")}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-amazon-link"
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="unspecified">Prefer not to say</option>
                  </select>
                </FieldWrap>
              </div>
              <FieldWrap label="Password *" error={showError("password") ? errors.password : undefined}>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => { setForm((f) => ({ ...f, password: e.target.value })); setErrors((prev) => ({ ...prev, password: undefined })) }}
                  onBlur={() => markTouched("password")}
                />
              </FieldWrap>
            </CardContent>
            <CardFooter className="flex flex-col gap-4">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Creating account..." : "Create account"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link href="/auth/login" className="font-medium text-primary hover:underline">
                  Sign in
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </Shell>
  )
}

function FieldWrap({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
