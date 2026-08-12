import { useCallback, useEffect, useState } from 'react'
import { queryFinQuery } from '../api/client'
import type { ChatMessage, ChatSession } from '../types'

const STORAGE_KEY = 'finquery.sessions.v2'

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function titleFromQuestion(q: string) {
  const t = q.trim()
  return t.length > 40 ? `${t.slice(0, 40)}…` : t
}

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as ChatSession[]
  } catch {
    return []
  }
}

function saveSessions(sessions: ChatSession[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

export function useChat() {
  const [sessions, setSessions] = useState<ChatSession[]>(() => loadSessions())
  const [activeId, setActiveId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    saveSessions(sessions)
  }, [sessions])

  const activeSession = sessions.find((s) => s.id === activeId) ?? null
  const messages = activeSession?.messages ?? []

  const newChat = useCallback(() => {
    setActiveId(null)
    setError(null)
  }, [])

  const selectChat = useCallback((id: string) => {
    setActiveId(id)
    setError(null)
  }, [])

  const sendMessage = useCallback(
    async (text: string) => {
      const question = text.trim()
      if (!question || loading) return

      setError(null)
      setLoading(true)

      const userMsg: ChatMessage = {
        id: uid(),
        role: 'user',
        content: question,
      }

      let sessionId = activeId
      if (!sessionId) {
        sessionId = uid()
        const session: ChatSession = {
          id: sessionId,
          title: titleFromQuestion(question),
          messages: [userMsg],
          updatedAt: Date.now(),
        }
        setSessions((prev) => [session, ...prev])
        setActiveId(sessionId)
      } else {
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: [...s.messages, userMsg],
                  updatedAt: Date.now(),
                  title:
                    s.messages.length === 0 ? titleFromQuestion(question) : s.title,
                }
              : s,
          ),
        )
      }

      try {
        const res = await queryFinQuery(question)
        const assistantMsg: ChatMessage = {
          id: uid(),
          role: 'assistant',
          content: res.answer,
          sources: res.sources,
          processingTimeMs: res.processing_time_ms,
          model: res.model,
        }
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: [...s.messages, assistantMsg],
                  updatedAt: Date.now(),
                }
              : s,
          ),
        )
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Something went wrong'
        setError(msg)
        const failMsg: ChatMessage = {
          id: uid(),
          role: 'assistant',
          content: `Sorry — I couldn't answer that.\n\n${msg}`,
        }
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...s.messages, failMsg], updatedAt: Date.now() }
              : s,
          ),
        )
      } finally {
        setLoading(false)
      }
    },
    [activeId, loading],
  )

  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (activeId === id) setActiveId(null)
    },
    [activeId],
  )

  return {
    sessions,
    activeId,
    messages,
    loading,
    error,
    newChat,
    selectChat,
    sendMessage,
    deleteSession,
  }
}
