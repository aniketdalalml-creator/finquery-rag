import { useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { useApiHealth } from './hooks/useApiHealth'
import { ingestDocuments } from './api/client'
import { Sidebar } from './components/Sidebar'
import { EmptyState } from './components/EmptyState'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { SettingsPanel } from './components/SettingsPanel'
import { Header } from '../../shared/components/Header'

export function ChatPage() {
  const {
    sessions,
    activeId,
    messages,
    loading,
    error,
    newChat,
    selectChat,
    sendMessage,
  } = useChat()

  const { health, status, refresh } = useApiHealth()

  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [ingestMessage, setIngestMessage] = useState<string | null>(null)

  const scrollRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const isEmpty = messages.length === 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading, activeId])

  const handleSubmit = () => {
    const q = input.trim()
    if (!q) return
    setSettingsOpen(false)
    setInput('')
    void sendMessage(q)
  }

  const handleSuggestion = (text: string) => {
    setSettingsOpen(false)
    setInput('')
    void sendMessage(text)
  }

  const handleIngest = async () => {
    setIngesting(true)
    setIngestMessage(null)
    try {
      const res = await ingestDocuments()
      setIngestMessage(res.message || `Added ${res.chunks_added} chunks.`)
      await refresh()
    } catch (err) {
      setIngestMessage(err instanceof Error ? err.message : 'Ingest failed')
    } finally {
      setIngesting(false)
    }
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-surface text-on-surface">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onNewChat={() => {
          setSettingsOpen(false)
          newChat()
        }}
        onSelect={(id) => {
          setSettingsOpen(false)
          selectChat(id)
        }}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        settingsOpen={settingsOpen}
        onToggleSettings={() => setSettingsOpen((v) => !v)}
      />

      <div className="flex min-w-0 flex-1 flex-col lg:pl-72">
        <Header onMenuClick={() => setSidebarOpen(true)} />

        {settingsOpen ? (
          <div className="flex-1 overflow-y-auto pt-16">
            <SettingsPanel
              health={health}
              status={status}
              onRefresh={() => void refresh()}
              onIngest={handleIngest}
              ingesting={ingesting}
              ingestMessage={ingestMessage}
            />
          </div>
        ) : (
          <>
            {/* Scrollable transcript */}
            <div
              ref={scrollRef}
              className="min-h-0 flex-1 overflow-y-auto overscroll-contain pt-16"
            >
              {isEmpty ? (
                <EmptyState />
              ) : (
                <>
                  <MessageList messages={messages} loading={loading} />
                  {error && (
                    <p className="mx-auto max-w-[800px] px-8 pb-2 text-center text-label-sm text-error">
                      {error}
                    </p>
                  )}
                </>
              )}
              <div ref={bottomRef} className="h-px w-full" aria-hidden />
            </div>

            {/* Sticky composer (ChatGPT-style) */}
            <div className="shrink-0 border-t border-outline-variant/30 bg-surface px-4 pb-4 pt-3 sm:px-6">
              <div className="mx-auto w-full max-w-[800px]">
                {isEmpty && (
                  <div className="mb-3 flex flex-wrap items-center justify-center gap-2">
                    {[
                      "Analyze NVIDIA's financial performance",
                      'Compare Apple and Microsoft',
                    ].map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => handleSuggestion(s)}
                        className="rounded-full bg-surface-container-low px-4 py-2 text-sm text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
                <ChatInput
                  value={input}
                  onChange={setInput}
                  onSubmit={handleSubmit}
                  loading={loading}
                  variant={isEmpty ? 'hero' : 'followup'}
                  placeholder={
                    isEmpty
                      ? 'Ask FinQuery anything about finance...'
                      : 'Ask a follow up question...'
                  }
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
