'use client'

import { useAuth } from '@clerk/nextjs'
import { useCallback } from 'react'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API error ${status}`)
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

/**
 * Returns a fetch helper that attaches the Clerk JWT (mirrors lib/ws.ts auth).
 * Use inside React Query hooks; throws `ApiError` on non-2xx.
 */
export function useApi() {
  const { getToken } = useAuth()

  return useCallback(
    async <T>(path: string, options?: RequestInit): Promise<T> => {
      const token = await getToken()
      const res = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options?.headers,
        },
      })

      if (!res.ok) {
        throw new ApiError(res.status, await res.json().catch(() => null))
      }
      if (res.status === 204) {
        return undefined as T
      }
      return res.json() as Promise<T>
    },
    [getToken],
  )
}
