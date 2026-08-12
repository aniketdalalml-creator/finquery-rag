import { FileText } from 'lucide-react'
import type { SourceDocument } from '../types'

type SourceChipProps = {
  source: SourceDocument
}

export function SourceChip({ source }: SourceChipProps) {
  const name = source.filename.split(/[/\\]/).pop() ?? source.filename
  const score = Math.round(source.relevance_score * 100)

  return (
    <span
      title={source.snippet}
      className="inline-flex cursor-default items-center gap-1.5 rounded-lg border border-outline-variant/30 bg-surface-container px-3 py-1.5 text-label-sm font-semibold text-on-surface-variant transition-colors hover:bg-surface-container-high"
    >
      <FileText size={14} />
      {name}
      {Number.isFinite(score) && score > 0 && (
        <span className="text-outline">· {score}%</span>
      )}
    </span>
  )
}
