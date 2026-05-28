import '@testing-library/jest-dom/vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const imagePath = '/archive-generated/10-ai-workflow-architect.png'

const archiveRecord = {
  record_id: 'ai-workflow-architect',
  title: 'AI Workflow Architect',
  category: 'TECH',
  category_detail: 'Tech / AI',
  categories: ['TECH'],
  first_seen_label: '2025 Q4',
  velocity_label: 'Rapid ascent',
  score: 0.92,
  recent_count: 12,
  prior_count: 1,
  early_mover_companies: ['Acme', 'Globex'],
  excerpt: 'AI workflow roles are emerging.',
  image_path: imagePath,
}

const archivePayload = {
  records: [archiveRecord],
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
  it('renders loading state without decorative masthead categories', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})))

    render(<App />)

    expect(screen.getByText(/opening archive/i)).toBeInTheDocument()
    expect(screen.queryByLabelText('Archive sections')).not.toBeInTheDocument()
  })

  it('does not render archive record image on the list page', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => archivePayload }))

    render(<App />)

    await screen.findByRole('button', { name: 'AI Workflow Architect' })
    expect(document.querySelector('.record-illustration')).not.toBeInTheDocument()
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

  it('filters by broad categories and supports multi-category records', async () => {
    const records = [
      { ...archiveRecord, record_id: 'tech-record', title: 'Tech Record', category: 'TECH', category_detail: 'Tech / AI', categories: ['TECH'] },
      { ...archiveRecord, record_id: 'finance-health-record', title: 'Finance Health Record', category: 'FINANCE', category_detail: 'Healthcare / Finance', categories: ['FINANCE', 'HEALTHCARE'] },
      { ...archiveRecord, record_id: 'other-record', title: 'Other Record', category: 'OTHER', category_detail: 'Education', categories: ['OTHER'] },
    ]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...archivePayload,
        records,
        summary: {
          ...archivePayload.summary,
          category_counts: { TECH: 1, FINANCE: 1, HEALTHCARE: 1, MANUFACTURING: 0, 'PUBLIC SECTOR': 0, OTHER: 1 },
        },
      }),
    }))

    render(<App />)

    await screen.findByRole('button', { name: 'TECH' })
    expect(screen.getByRole('button', { name: 'FINANCE' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'HEALTHCARE' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'TECH / AI' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'HEALTHCARE' }))

    await screen.findByRole('button', { name: 'Finance Health Record' })
    expect(screen.queryByRole('button', { name: 'Tech Record' })).not.toBeInTheDocument()
  })

  it('returns to the same archive page after opening a dossier', async () => {
    const records = Array.from({ length: 4 }, (_, index) => ({
      ...archiveRecord,
      record_id: `record-${index + 1}`,
      title: `Record ${index + 1}`,
    }))
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...archivePayload, records }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ...dossierPayload, ...records[3] }) })
    vi.stubGlobal('fetch', fetchMock)
    window.location.hash = '#/?page=2'

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Record 4' }))
    await screen.findByText('A new operational layer enters the archive.')
    fireEvent.click(screen.getByRole('button', { name: /back to archive/i }))

    await screen.findByRole('button', { name: 'Record 4' })
    expect(screen.getByText('Archive Page 02 / 02')).toBeInTheDocument()
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
