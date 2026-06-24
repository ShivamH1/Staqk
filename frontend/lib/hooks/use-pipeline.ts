'use client'

import { useAuth } from '@clerk/nextjs'
import { useCallback, useReducer, useRef, useState } from 'react'
import { initialPipelineState, pipelineReducer } from '@/lib/pipeline-reducer'
import type { AgentEvent } from '@/lib/ws'

interface StartArgs {
  userMessage: string
  techStack?: Record<string, unknown>
}

export function usePipeline(projectId: string) {
  const { getToken } = useAuth()
  const [state, dispatch] = useReducer(pipelineReducer, undefined, initialPipelineState)
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)

  const start = useCallback(
    async ({ userMessage, techStack = {} }: StartArgs) => {
      const token = await getToken()
      if (!token) return

      const base = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, 'ws') ?? 'ws://localhost:8000'
      const ws = new WebSocket(`${base}/ai/stream/${projectId}?token=${token}`)
      socketRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        ws.send(JSON.stringify({ user_message: userMessage, tech_stack: techStack }))
      }

      ws.onmessage = (msg) => {
        try {
          const event = JSON.parse(msg.data as string) as AgentEvent
          dispatch(event)
        } catch {
          // ignore malformed frames
        }
      }

      ws.onclose = () => {
        setConnected(false)
        socketRef.current = null
      }
    },
    [getToken, projectId],
  )

  return { state, connected, start }
}
