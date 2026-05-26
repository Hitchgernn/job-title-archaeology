import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

const successPayload = {
  trends: [
    {
      rank: 1,
      title: 'AI Workflow Architect',
      score: 0.92,
      recent_count: 12,
      prior_count: 1,
      newness: 1,
      velocity: 0.86,
      concentration: 0.6,
      early_mover_companies: ['Acme', 'Globex'],
      narrative: 'summary:\nAI workflow roles are emerging.\nevidence:\nRecent postings jumped.',
    },
  ],
  summary: { trend_count: 1, average_score: 0.92, early_mover_count: 2 },
}

describe('App', () => {
  it('renders loading state', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})))

    render(<App />)

    expect(screen.getByText(/acquiring signals/i)).toBeInTheDocument()
  })

  it('renders trend cards', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => successPayload }))

    render(<App />)

    await waitFor(() => expect(screen.getByText('AI Workflow Architect')).toBeInTheDocument())
    expect(screen.getByText('SIGNAL DESK')).toBeInTheDocument()
    expect(screen.getAllByText('0.92').length).toBeGreaterThan(0)
    expect(screen.getByText(/Acme, Globex/)).toBeInTheDocument()
  })

  it('renders empty state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ trends: [], summary: { trend_count: 0, average_score: 0, early_mover_count: 0 } }) }))

    render(<App />)

    await waitFor(() => expect(screen.getByText(/no signals found/i)).toBeInTheDocument())
  })

  it('renders error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))

    render(<App />)

    await waitFor(() => expect(screen.getByText(/signal feed interrupted/i)).toBeInTheDocument())
  })
})
