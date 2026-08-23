interface StatusRowProps {
  label: string
  value: string
}

export function StatusRow({ label, value }: StatusRowProps) {
  return (
    <p className="text-lg text-neutral-700">
      {label}:{' '}
      <span className="font-medium text-neutral-900">{value}</span>
    </p>
  )
}
