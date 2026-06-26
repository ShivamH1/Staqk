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

  const run = useCallback(
    async (endpoint: 'stream' | 'iterate', payload: Record<string, unknown>) => {
      const token = await getToken()
      if (!token) return

      dispatch({ type: 'reset' })
      const base = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, 'ws') ?? 'ws://localhost:8000'
      const ws = new WebSocket(`${base}/ai/${endpoint}/${projectId}?token=${token}`)
      socketRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        ws.send(JSON.stringify(payload))
      }

      ws.onmessage = (msg) => {
        try {
          dispatch(JSON.parse(msg.data as string) as AgentEvent)
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

  const start = useCallback(
    ({ userMessage, techStack = {} }: StartArgs) =>
      run('stream', { user_message: userMessage, tech_stack: techStack }),
    [run],
  )

  /** Chat iteration over the project's existing file tree (cheaper than a full run). */
  const iterate = useCallback(
    (userMessage: string) => run('iterate', { user_message: userMessage }),
    [run],
  )

  return { state, connected, start, iterate }
}
