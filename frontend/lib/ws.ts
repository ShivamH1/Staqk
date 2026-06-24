export type AgentName = 'plan' | 'code' | 'test' | 'security' | 'deploy'

export type AgentEvent =
  | { type: 'agent_start'; agent: AgentName; timestamp: string }
  | { type: 'agent_progress'; agent: AgentName; message: string; timestamp: string }
  | { type: 'agent_complete'; agent: AgentName; timestamp: string }
  | { type: 'agent_error'; agent: AgentName; error: string; timestamp: string }
  | { type: 'file_created'; path: string; timestamp: string }
  | { type: 'test_result'; file: string; passed: number; failed: number }
  | { type: 'security_finding'; severity: string; rule: string; file: string }
  | { type: 'pipeline_complete'; deployment_url: string; credits_used: number }
  | { type: 'pipeline_error'; error: string; credits_refunded: number }

export function createAgentSocket(
  projectId: string,
  token: string,
  onEvent: (event: AgentEvent) => void,
  onClose?: () => void,
): WebSocket {
  const url = `${process.env.NEXT_PUBLIC_WS_URL ?? process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws')}/ai/stream/${projectId}?token=${token}`
  const ws = new WebSocket(url)

  ws.onmessage = (msg) => {
    try {
      const event = JSON.parse(msg.data as string) as AgentEvent
      onEvent(event)
    } catch {
      // malformed message — ignore
    }
  }

  ws.onclose = () => onClose?.()

  return ws
}
