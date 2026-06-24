import type { AgentEvent, AgentName } from './ws'

export const AGENTS: AgentName[] = ['plan', 'code', 'test', 'security', 'deploy']

export type StageStatus = 'pending' | 'running' | 'complete' | 'error'

export interface StageState {
  status: StageStatus
  message?: string
  error?: string
}

export interface PipelineState {
  status: 'idle' | 'running' | 'complete' | 'error'
  stages: Record<AgentName, StageState>
  files: string[]
  testResults: { file: string; passed: number; failed: number }[]
  securityFindings: { severity: string; rule: string; file: string }[]
  deploymentUrl?: string
  creditsUsed?: number
  creditsRefunded?: number
  errorMessage?: string
}

export function initialPipelineState(): PipelineState {
  return {
    status: 'idle',
    stages: {
      plan: { status: 'pending' },
      code: { status: 'pending' },
      test: { status: 'pending' },
      security: { status: 'pending' },
      deploy: { status: 'pending' },
    },
    files: [],
    testResults: [],
    securityFindings: [],
  }
}

function setStage(
  state: PipelineState,
  agent: AgentName,
  patch: Partial<StageState>,
): PipelineState {
  return {
    ...state,
    stages: { ...state.stages, [agent]: { ...state.stages[agent], ...patch } },
  }
}

export function pipelineReducer(state: PipelineState, event: AgentEvent): PipelineState {
  switch (event.type) {
    case 'agent_start':
      return setStage({ ...state, status: 'running' }, event.agent, {
        status: 'running',
        message: undefined,
        error: undefined,
      })
    case 'agent_progress':
      return setStage(state, event.agent, { message: event.message })
    case 'agent_complete':
      return setStage(state, event.agent, { status: 'complete' })
    case 'agent_error':
      return setStage({ ...state, status: 'error' }, event.agent, {
        status: 'error',
        error: event.error,
      })
    case 'file_created':
      return state.files.includes(event.path)
        ? state
        : { ...state, files: [...state.files, event.path] }
    case 'test_result':
      return {
        ...state,
        testResults: [
          ...state.testResults,
          { file: event.file, passed: event.passed, failed: event.failed },
        ],
      }
    case 'security_finding':
      return {
        ...state,
        securityFindings: [
          ...state.securityFindings,
          { severity: event.severity, rule: event.rule, file: event.file },
        ],
      }
    case 'pipeline_complete':
      return {
        ...state,
        status: 'complete',
        deploymentUrl: event.deployment_url,
        creditsUsed: event.credits_used,
      }
    case 'pipeline_error':
      return {
        ...state,
        status: 'error',
        errorMessage: event.error,
        creditsRefunded: event.credits_refunded,
      }
    default:
      return state
  }
}
