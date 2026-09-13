const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  uploaded: {
    label: 'Uploaded',
    className: 'bg-warning-container text-warning',
  },
  queued: {
    label: 'Processing',
    className: 'bg-warning-container text-warning',
  },
  pending: {
    label: 'Processing',
    className: 'bg-warning-container text-warning',
  },
  processing: {
    label: 'Processing',
    className: 'bg-warning-container text-warning',
  },
  partially_processed: {
    label: 'Processing',
    className: 'bg-warning-container text-warning',
  },
  processed: {
    label: 'Ready',
    className: 'bg-success-container text-success',
  },
  completed: {
    label: 'Ready',
    className: 'bg-success-container text-success',
  },
  failed: {
    label: 'Failed',
    className: 'bg-error-container text-on-error-container',
  },
}

export function StatusBadge({ status }: { status: string }) {
  const badge = STATUS_BADGES[status] ?? {
    label: status,
    className: 'bg-surface-variant text-on-surface',
  }
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-label-sm font-semibold ${badge.className}`}
    >
      {badge.label}
    </span>
  )
}
