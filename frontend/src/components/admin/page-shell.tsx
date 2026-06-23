import type { ReactNode } from "react"

export function AdminPageShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{title}</h1>
      {children}
    </div>
  )
}
