/** API response shapes — mirror the backend Pydantic schemas. */

export type ProjectStatus = 'draft' | 'building' | 'ready' | 'deployed' | 'error'

/** List view (`GET /projects`) — no `file_tree`. */
export type ProjectSummary = {
  id: string
  name: string
  description: string
  status: ProjectStatus
  created_at: string
  updated_at: string
}

/** Detail view (`GET /projects/{id}`, `POST /projects`). */
export type Project = ProjectSummary & {
  user_id: string
  tech_stack: Record<string, unknown>
  file_tree: Record<string, string>
}

export type CreateProjectInput = {
  name: string
  description?: string
  tech_stack?: Record<string, unknown>
}

/** Current user (`GET /auth/me`). */
export type CurrentUser = {
  id: string
  clerk_id: string
  email: string
  credits: number
  plan: string
  created_at: string
}
