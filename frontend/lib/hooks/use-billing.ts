'use client'

import { useMutation, useQuery } from '@tanstack/react-query'
import type { CreateOrderResponse, CreditPack, Transaction } from '@/lib/types'
import { useApi } from './use-api'

export function usePacks() {
  const api = useApi()
  return useQuery({
    queryKey: ['billing', 'packs'],
    queryFn: () => api<CreditPack[]>('/billing/packs'),
  })
}

export function useTransactions() {
  const api = useApi()
  return useQuery({
    queryKey: ['transactions'],
    queryFn: () => api<Transaction[]>('/billing/transactions'),
  })
}

export function useCreateOrder() {
  const api = useApi()
  return useMutation({
    mutationFn: (packId: string) =>
      api<CreateOrderResponse>('/billing/order', {
        method: 'POST',
        body: JSON.stringify({ pack_id: packId }),
      }),
  })
}
