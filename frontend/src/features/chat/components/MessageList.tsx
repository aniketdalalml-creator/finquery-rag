import type { ChatMessage } from '../types'
import { Logo } from '../../../shared/components/Logo'
import { SourceChip } from './SourceChip'
import { RichAnalysisBlock } from './RichAnalysisBlock'
import { FileText, Megaphone } from 'lucide-react'

type MessageListProps = {
  messages: ChatMessage[]
  loading?: boolean
}

function formatAnswer(text: string) {
  const paragraphs = text.split(/\n\n+/).filter(Boolean)
  return paragraphs.map((p, i) => {
    const lines = p.split('\n')
    return (
      <p key={i} className="max-w-[65ch] text-body-md text-on-surface-variant">
        {lines.map((line, j) => (
          <span key={j}>
            {j > 0 && <br />}
            {line}
          </span>
        ))}
      </p>
    )
  })
}

export function MessageList({ messages, loading }: MessageListProps) {
  return (
    <div className="mx-auto flex w-full max-w-[800px] flex-col gap-8 px-4 py-8 sm:px-8">
      {messages.map((m) =>
        m.role === 'user' ? (
          <div key={m.id} className="flex max-w-[85%] items-start gap-4 self-end sm:gap-6">
            <div className="rounded-2xl rounded-tr-sm bg-primary-container px-5 py-3.5 text-body-md text-on-primary-container sm:px-6 sm:py-4 sm:text-body-lg">
              {m.content}
            </div>
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-outline-variant bg-surface-container text-label-sm font-semibold text-on-surface-variant sm:h-10 sm:w-10">
              U
            </div>
          </div>
        ) : (
          <div key={m.id} className="flex max-w-[95%] items-start gap-4 sm:gap-6">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high sm:h-10 sm:w-10">
              <Logo size={22} />
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-5">
              {m.rich ? (
                <RichAnalysisBlock data={m.rich} />
              ) : (
                <div className="flex flex-col gap-3">
                  <div className="flex flex-col gap-3">{formatAnswer(m.content)}</div>
                </div>
              )}

              {m.rich?.sourceLabels && m.rich.sourceLabels.length > 0 ? (
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-label-sm font-semibold text-outline">Sources:</span>
                  <div className="flex flex-wrap gap-2">
                    {m.rich.sourceLabels.map((label, i) => (
                      <span
                        key={`${label}-${i}`}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant/30 bg-surface-container px-3 py-1.5 text-label-sm font-semibold text-on-surface-variant"
                      >
                        {i === 0 ? <FileText size={14} /> : <Megaphone size={14} />}
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                m.sources &&
                m.sources.length > 0 && (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-label-sm font-semibold text-outline">Sources:</span>
                    <div className="flex flex-wrap gap-2">
                      {m.sources.map((s, i) => (
                        <SourceChip key={`${s.filename}-${i}`} source={s} />
                      ))}
                    </div>
                  </div>
                )
              )}

              {(m.processingTimeMs != null || m.model) && (
                <p className="text-label-sm text-outline">
                  {m.model && m.model !== 'dummy' && m.model !== 'demo' && (
                    <span>{m.model}</span>
                  )}
                  {m.model &&
                    m.model !== 'dummy' &&
                    m.model !== 'demo' &&
                    m.processingTimeMs != null && <span> · </span>}
                  {m.processingTimeMs != null && (
                    <span>{Math.round(m.processingTimeMs)} ms</span>
                  )}
                </p>
              )}
            </div>
          </div>
        ),
      )}

      {loading && (
        <div className="flex max-w-[95%] items-start gap-4 sm:gap-6">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high sm:h-10 sm:w-10">
            <Logo size={22} />
          </div>
          <div className="flex flex-col gap-3 pt-2">
            <div className="h-3 w-40 animate-pulse rounded bg-surface-container-high sm:w-48" />
            <div className="h-3 w-56 animate-pulse rounded bg-surface-container sm:w-72" />
            <div className="h-3 w-48 animate-pulse rounded bg-surface-container sm:w-56" />
          </div>
        </div>
      )}
    </div>
  )
}
