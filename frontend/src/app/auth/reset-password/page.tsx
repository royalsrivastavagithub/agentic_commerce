import { Suspense } from "react"
import ResetPasswordContent from "./reset-password-content"

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  )
}
