import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import appCss from './App.css?raw'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const imagePath = '/archive-generated/10-ai-workflow-architect.png'

const archivePayload = {
  records: [
    {
      record_id: 'ai-workflow-architect',
      title: 'AI Workflow Architect',
      category: 'TECH',
      first_seen_label: '2025 Q4',
      velocity_label: 'Rapid ascent',
      score: 0.92,
      recent_count: 12,
      prior_count: 1,
      early_mover_companies: ['Acme', 'Globex'],
      excerpt: 'AI workflow roles are emerging.',
      image_path: imagePath,
    },
  ],
  summary: {
    total_records: 1,
    category_counts: { TECH: 1 },
    era_density: [{ label: '2025', percentage: 72 }],
  },
}

const dossierPayload = {
  ...archivePayload.records[0],
  subheadline: 'A new operational layer enters the archive.',
  lead_paragraph: 'Recent postings jumped.',
  pull_quote: 'Workflow orchestration became a job title.',
  adoption_points: [{ label: '2025 Q4', value: 12, annotation: 'Breakout' }],
  sector_density: [{ sector: 'Technology', percentage: 88 }],
  early_adopters: [{ company: 'Acme', date_label: '2025 Q4', location_label: 'Remote' }],
  preceding_titles: ['Automation Specialist'],
  competencies: ['Process mapping'],
  outlook: 'Continued growth likely.',
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  window.location.hash = ''
})

describe('App', () => {
  it('renders loading state', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})))

    render(<App />)

    expect(screen.getByText(/opening archive/i)).toBeInTheDocument()
  })

  it('does not render archive record image on the list page', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => archivePayload }))

    render(<App />)

    await screen.findByRole('button', { name: 'AI Workflow Architect' })
    expect(document.querySelector('.record-illustration')).not.toBeInTheDocument()
  })

  it('uses full-width archive result layout without the removed image column', () => {
    expect(appCss).not.toContain('grid-template-columns: 132px minmax(0, 1fr)')
  })

  it('renders dossier image from image_path', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => archivePayload })
      .mockResolvedValueOnce({ ok: true, json: async () => dossierPayload })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'AI Workflow Architect' }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith('/archive/titles/ai-workflow-architect?limit=10'))
    const image = await screen.findByAltText('AI Workflow Architect archival illustration')
    expect(image).toHaveAttribute('src', imagePath)
  })

  it('renders empty state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ records: [], summary: { total_records: 0, category_counts: {}, era_density: [] } }),
    }))

    render(<App />)

    await waitFor(() => expect(screen.getByText(/no records found/i)).toBeInTheDocument())
  })

  it('renders error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))

    render(<App />)

    await waitFor(() => expect(screen.getByText(/archive feed interrupted/i)).toBeInTheDocument())
  })
})
