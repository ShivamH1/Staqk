'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { CreateProjectInput, Project, ProjectSummary } from '@/lib/types'
import { useApi } from './use-api'

export function useProjects() {
  const api = useApi()
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => api<ProjectSummary[]>('/projects'),
  })
}

export function useProject(id: string) {
  const api = useApi()
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => api<Project>(`/projects/${id}`),
    enabled: Boolean(id),
  })
}

export function useCreateProject() {
  const api = useApi()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateProjectInput) =>
      api<Project>('/projects', { method: 'POST', body: JSON.stringify(input) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })
}
