import { Inbox } from "lucide-react"

export function AdminEmptyState({ label = "items" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Inbox className="mb-3 h-10 w-10 text-muted-foreground/50" />
      <p className="text-sm text-muted-foreground">No {label} found.</p>
    </div>
  )
}
