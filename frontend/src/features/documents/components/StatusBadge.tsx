const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  uploaded: {
    label: 'Uploaded',
    className: 'bg-secondary-container text-on-secondary-container',
  },
  queued: {
    label: 'Processing',
    className: 'bg-[#fff3cd] text-[#7a5b00]',
  },
  pending: {
    label: 'Processing',
    className: 'bg-[#fff3cd] text-[#7a5b00]',
  },
  processing: {
    label: 'Processing',
    className: 'bg-[#fff3cd] text-[#7a5b00]',
  },
  partially_processed: {
    label: 'Processing',
    className: 'bg-[#fff3cd] text-[#7a5b00]',
  },
  processed: {
    label: 'Processed',
    className: 'bg-primary-container text-on-primary-container',
  },
  completed: {
    label: 'Processed',
    className: 'bg-primary-container text-on-primary-container',
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
      className={`inline-block rounded-full px-3 py-1 text-label-sm font-semibold ${badge.className}`}
    >
      {badge.label}
    </span>
  )
}
