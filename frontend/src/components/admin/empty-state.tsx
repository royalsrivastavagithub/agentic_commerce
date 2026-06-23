export function AdminEmptyState({ label = "items" }: { label?: string }) {
  return <p className="text-sm text-muted-foreground">No {label} found.</p>
}
