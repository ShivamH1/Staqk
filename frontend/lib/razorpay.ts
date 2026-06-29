/** Razorpay Checkout integration.
 *
 * The script is loaded on-demand (first purchase) rather than bundled, so the
 * billing page stays light. Credits are granted by the backend webhook — the
 * client handler only triggers a refetch so the balance reflects the payment.
 */

export type RazorpayPaymentResponse = {
  razorpay_payment_id: string
  razorpay_order_id: string
  razorpay_signature: string
}

export type RazorpayCheckoutOptions = {
  key: string
  order_id: string
  amount: number
  currency: string
  name: string
  description?: string
  prefill?: { name?: string; email?: string }
  theme?: { color?: string }
  handler?: (response: RazorpayPaymentResponse) => void
  modal?: { ondismiss?: () => void }
}

type RazorpayInstance = { open: () => void }
type RazorpayConstructor = new (options: RazorpayCheckoutOptions) => RazorpayInstance

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor
  }
}

const SCRIPT_SRC = 'https://checkout.razorpay.com/v1/checkout.js'

let scriptPromise: Promise<void> | null = null

function loadRazorpay(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Razorpay can only load in the browser'))
  }
  if (window.Razorpay) return Promise.resolve()
  if (scriptPromise) return scriptPromise

  scriptPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = SCRIPT_SRC
    script.onload = () => resolve()
    script.onerror = () => {
      scriptPromise = null // allow a retry on the next attempt
      reject(new Error('Failed to load Razorpay Checkout'))
    }
    document.body.appendChild(script)
  })
  return scriptPromise
}

/** Load the SDK if needed, then open the Checkout modal. */
export async function openCheckout(options: RazorpayCheckoutOptions): Promise<void> {
  await loadRazorpay()
  if (!window.Razorpay) throw new Error('Razorpay Checkout is unavailable')
  const checkout = new window.Razorpay(options)
  checkout.open()
}
