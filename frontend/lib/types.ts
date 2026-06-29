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

/** A purchasable credit pack (`GET /billing/packs`). `amount` is the price in
 * the smallest currency unit (paise for INR). */
export type CreditPack = {
  id: string
  credits: number
  amount: number
  currency: string
}

/** Razorpay order to hand to Checkout (`POST /billing/order`). */
export type CreateOrderResponse = {
  order_id: string
  amount: number
  currency: string
  key_id: string
  credits: number
  pack_id: string
}

export type TransactionType = 'purchase' | 'spend' | 'refund'

/** A credit-ledger entry (`GET /billing/transactions`). `amount` is signed:
 * positive for purchase/refund, negative for spend. */
export type Transaction = {
  id: string
  amount: number
  type: TransactionType
  description: string
  created_at: string
}
