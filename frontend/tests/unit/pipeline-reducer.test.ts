import { describe, expect, it } from 'vitest'
import { initialPipelineState, pipelineReducer } from '@/lib/pipeline-reducer'
import type { AgentEvent } from '@/lib/ws'

function apply(events: AgentEvent[]) {
  return events.reduce(pipelineReducer, initialPipelineState())
}

describe('pipelineReducer', () => {
  it('starts idle with all stages pending', () => {
    const s = initialPipelineState()
    expect(s.status).toBe('idle')
    expect(Object.values(s.stages).every((st) => st.status === 'pending')).toBe(true)
  })

  it('marks a stage running on agent_start and sets status running', () => {
    const s = apply([{ type: 'agent_start', agent: 'plan', timestamp: 't' }])
    expect(s.status).toBe('running')
    expect(s.stages.plan.status).toBe('running')
  })

  it('records progress messages and completion', () => {
    const s = apply([
      { type: 'agent_start', agent: 'code', timestamp: 't' },
      { type: 'agent_progress', agent: 'code', message: 'Generating', timestamp: 't' },
      { type: 'agent_complete', agent: 'code', timestamp: 't' },
    ])
    expect(s.stages.code.status).toBe('complete')
    expect(s.stages.code.message).toBe('Generating')
  })

  it('dedupes created files', () => {
    const s = apply([
      { type: 'file_created', path: 'app/page.tsx', timestamp: 't' },
      { type: 'file_created', path: 'app/page.tsx', timestamp: 't' },
    ])
    expect(s.files).toEqual(['app/page.tsx'])
  })

  it('captures completion with deployment url and credits', () => {
    const s = apply([
      { type: 'pipeline_complete', deployment_url: 'https://x.staqk.app', credits_used: 5 },
    ])
    expect(s.status).toBe('complete')
    expect(s.deploymentUrl).toBe('https://x.staqk.app')
    expect(s.creditsUsed).toBe(5)
  })

  it('captures pipeline errors with refund', () => {
    const s = apply([{ type: 'pipeline_error', error: 'boom', credits_refunded: 5 }])
    expect(s.status).toBe('error')
    expect(s.errorMessage).toBe('boom')
    expect(s.creditsRefunded).toBe(5)
  })
})
