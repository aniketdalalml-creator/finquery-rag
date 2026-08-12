import { useEffect, useRef, type FormEvent, type KeyboardEvent } from 'react'
import { ArrowUp, Plus } from 'lucide-react'

type ChatInputProps = {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading?: boolean
  variant?: 'hero' | 'followup'
  placeholder?: string
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  loading = false,
  variant = 'followup',
  placeholder,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const canSend = value.trim().length >= 1 && !loading

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [value])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSubmit()
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (canSend) onSubmit()
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div
        className={`flex items-end rounded-3xl border border-outline-variant/50 bg-surface-container-lowest p-2 shadow-sm transition-all focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/15 ${
          variant === 'hero' ? 'shadow-md' : ''
        }`}
      >
        <button
          type="button"
          className="mb-0.5 flex items-center justify-center rounded-xl p-2.5 text-outline transition-colors hover:bg-surface-container hover:text-on-surface"
          aria-label="Attach"
        >
          <Plus size={20} />
        </button>
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder={placeholder ?? 'Message FinQuery…'}
          className="max-h-40 min-h-[44px] flex-1 resize-none border-none bg-transparent px-2 py-3 text-body-md text-on-surface outline-none placeholder:text-outline disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className="mb-0.5 ml-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-send text-white transition-colors hover:bg-send/90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ArrowUp size={18} />
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] font-medium text-outline/80">
        FinQuery can make mistakes. Verify critical figures.
      </p>
    </form>
  )
}
