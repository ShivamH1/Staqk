'use client'

import { useQuery } from '@tanstack/react-query'
import type { CurrentUser } from '@/lib/types'
import { useApi } from './use-api'

export function useCurrentUser() {
  const api = useApi()
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api<CurrentUser>('/auth/me'),
  })
}
