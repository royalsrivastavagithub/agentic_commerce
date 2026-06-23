import dynamic from "next/dynamic"
import { Suspense } from "react"

const ShellInner = dynamic(
  () => import("@/components/features/shell").then((m) => ({ default: m.Shell })),
  { ssr: false },
)

export function DynamicShell({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={null}>
      <ShellInner>{children}</ShellInner>
    </Suspense>
  )
}
