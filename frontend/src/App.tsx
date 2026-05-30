import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { fetchArchiveDossier, fetchArchiveTitles, fetchCompanies, fetchCompanyDossier } from './api'
import jobMarketImage from './assets/archive-images/job-market-1.png'
import landingImage from './assets/archive-images/landing-page.png'
import type {
  AdoptionPoint,
  ArchiveRecord,
  ArchiveResponse,
  CompanyDossierResponse,
  CompanyListResponse,
  CompanySignal,
  DossierResponse,
  EraDensity,
  SectorDensity,
  SerpSignal,
  WeeklyHire,
} from './types'

const EDITION = 'Vol. 1 · Issue 47'
const PAGE_SIZE = 3
const BROAD_CATEGORIES = ['TECH', 'FINANCE', 'HEALTHCARE', 'MANUFACTURING', 'PUBLIC SECTOR', 'OTHER'] as const
const TODAY = new Intl.DateTimeFormat('en', { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date())

type View =
  | { name: 'landing' }
  | { name: 'archive' }
  | { name: 'dossier'; recordId: string }
  | { name: 'companies' }
  | { name: 'company'; key: string }

function viewFromHash(): View {
  const hash = window.location.hash
  const dossierMatch = hash.match(/^#\/titles\/(.+)$/)
  if (dossierMatch) return { name: 'dossier', recordId: decodeURIComponent(dossierMatch[1]) }
  const companyMatch = hash.match(/^#\/companies\/(.+)$/)
  if (companyMatch) return { name: 'company', key: decodeURIComponent(companyMatch[1]) }
  if (hash === '#/companies' || hash.startsWith('#/companies?')) return { name: 'companies' }
  if (hash === '#/archive' || hash.startsWith('#/archive?')) return { name: 'archive' }
  return { name: 'landing' }
}

function archivePageFromHash() {
  const match = window.location.hash.match(/^#\/archive\?page=(\d+)$/)
  return match ? Math.max(Number(match[1]) - 1, 0) : 0
}

function pushArchivePage(page: number) {
  window.location.hash = page === 0 ? '#/archive' : `#/archive?page=${page + 1}`
}

function pushView(view: View) {
  if (view.name === 'dossier') {
    window.location.hash = `#/titles/${encodeURIComponent(view.recordId)}`
    return
  }
  if (view.name === 'company') {
    window.location.hash = `#/companies/${encodeURIComponent(view.key)}`
    return
  }
  if (view.name === 'companies') {
    window.location.hash = '#/companies'
    return
  }
  if (view.name === 'archive') {
    window.location.hash = '#/archive'
    return
  }
  window.location.hash = '#/'
}

function Masthead({
  active,
  onHome,
  onArchive,
  onCompanies,
}: {
  active: 'landing' | 'archive' | 'companies'
  onHome: () => void
  onArchive: () => void
  onCompanies: () => void
}) {
  return (
    <header className="masthead">
      <div className="masthead-top">
        <span>{TODAY}</span>
        <button type="button" onClick={onHome}>JOB TITLE ARCHAEOLOGY</button>
        <span>{EDITION}</span>
      </div>
      <nav className="masthead-nav" aria-label="Primary sections">
        <button type="button" className={active === 'archive' ? 'active' : ''} onClick={onArchive}>The Archive</button>
        <button type="button" className={active === 'companies' ? 'active' : ''} onClick={onCompanies}>Field Reports</button>
      </nav>
    </header>
  )
}

function Footer() {
  return (
    <footer className="archive-footer">
      <div>
        <h2>JOB TITLE ARCHAEOLOGY</h2>
        <p>Archival data subject to historical revision. Built from demo labor-market signals.</p>
      </div>
      <div className="footer-links">
        <span>The Archive</span>
        <span>Methodology</span>
        <span>Permissions</span>
        <span>Contact</span>
      </div>
    </footer>
  )
}

function StatePanel({ children }: { children: React.ReactNode }) {
  return <section className="state-panel">{children}</section>
}

const CSV_COLUMNS = [
  'record_id',
  'title',
  'category',
  'category_detail',
  'categories',
  'first_seen_label',
  'velocity_label',
  'score',
  'recent_count',
  'prior_count',
  'early_mover_companies',
  'excerpt',
  'image_path',
] as const

function csvEscape(value: string | number | null | undefined) {
  const text = String(value ?? '')
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

function archiveRecordToCsvRow(record: ArchiveRecord) {
  return [
    record.record_id,
    record.title,
    record.category,
    record.category_detail,
    record.categories.join('; '),
    record.first_seen_label,
    record.velocity_label,
    record.score,
    record.recent_count,
    record.prior_count,
    record.early_mover_companies.join('; '),
    record.excerpt,
    record.image_path ?? '',
  ].map(csvEscape).join(',')
}

function archiveRecordsToCsv(records: ArchiveRecord[]) {
  return [CSV_COLUMNS.join(','), ...records.map(archiveRecordToCsvRow)].join('\n')
}

function downloadArchiveCsv(records: ArchiveRecord[]) {
  const blob = new Blob([archiveRecordsToCsv(records)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'archive-search-data.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function LandingPage({ onArchive, onCompanies }: { onArchive: () => void; onCompanies: () => void }) {
  const tickerItems = ['AI Workflow Architect', 'LLM Reliability Engineer', 'Climate Risk Modeler', 'Clinical AI Safety Officer', 'Robotics Fleet Coordinator']
  return (
    <>
      <section className="landing-hero" aria-labelledby="landing-title">
        <article className="landing-hero-copy">
          <h1 id="landing-title">The Job Titles Nobody’s Talking About Yet Are the Ones That Matter Most.</h1>
          <p>
            Job Title Archaeology turns Bright Data hiring snapshots into searchable signals: emerging titles,
            early adopter companies, velocity scores, dossiers, and field reports.
          </p>
          <div className="landing-actions" aria-label="Landing actions">
            <button type="button" onClick={onArchive}>Enter the Archive <span aria-hidden="true">→</span></button>
            <button type="button" onClick={onCompanies}>Read Field Reports</button>
          </div>
        </article>
        <aside className="landing-plate" aria-label="Method specimen">
          <span className="landing-fig">FIG. 1</span>
          <img src={landingImage} alt="Dashboard preview showing early signal job title detection" />
          <div>
            <span>Source: archive DB</span>
          </div>
        </aside>
      </section>

      <section className="landing-signal-strip" id="signals" aria-label="Emerging title signals">
        <div className="landing-ticker">
          {[...tickerItems, ...tickerItems].map((item, index) => (
            <span key={`${item}-${index}`}><b>▲</b> {item}</span>
          ))}
        </div>
      </section>

      <section className="landing-method" id="how-it-works">
        <div className="landing-section-heading">
          <span>Methodology</span>
          <h2>Excavating Intent Through Syntax</h2>
        </div>
        <div className="landing-method-grid">
          <article>
            <span>01.</span>
            <h3>Ingestion</h3>
            <p>Bright Data Web Scraper snapshots capture Indeed and LinkedIn job postings into the raw archive.</p>
          </article>
          <article>
            <span>02.</span>
            <h3>Semantic Extraction</h3>
            <p>Rule-based normalization strips location noise, IDs, shift markers, and duplicate title variants.</p>
          </article>
          <article>
            <span>03.</span>
            <h3>Dossier Compilation</h3>
            <p>Trend scoring, company velocity, SERP signals, and optional Gemini metadata become readable dossiers.</p>
          </article>
        </div>
      </section>

      <section className="landing-strategy" id="pipeline">
        <article className="landing-strategy-copy">
          <div className="landing-section-heading">
            <span>Strategic Application</span>
            <h2>Mapping Strategy via Taxonomy</h2>
          </div>
          <p>
            A job title is a hiring commitment. When companies name new operating roles, they reveal where budgets,
            controls, automation, and talent strategy are moving before standard reports catch up.
          </p>
          <blockquote>
            “The archive turns messy postings into evidence you can inspect, export, and challenge.”
          </blockquote>
        </article>
        <div className="landing-signal-table">
          <div className="landing-table-head"><span>Detected Signal (Syntax)</span><span>Enterprise Translation</span></div>
          <div><strong>“AI Workflow Architect”</strong><span>AI tools become operating infrastructure, not side experiments.</span></div>
          <div><strong>“Climate Risk Modeler”</strong><span>Portfolio and insurance teams operationalize climate exposure work.</span></div>
          <div><strong>“Clinical AI Safety Officer”</strong><span>Healthcare AI adoption needs accountable safety governance.</span></div>
          <div><strong>“Robotics Fleet Coordinator”</strong><span>Warehouses and factories manage automation as fleets.</span></div>
        </div>
      </section>
    </>
  )
}

function ArchiveResult({ record, onOpen }: { record: ArchiveRecord; onOpen: (recordId: string) => void }) {
  return (
    <article className="archive-result">
      <div className="result-meta">
        <span>Cat. {record.category_detail || record.category}</span>
        <span>REC_ID: {record.record_id}</span>
      </div>
      <button type="button" onClick={() => onOpen(record.record_id)}>
        {record.title}
      </button>
      <p>{record.excerpt}</p>
      <div className="result-facts">
        <div>
          <span>First Seen</span>
          {record.first_seen_label}
        </div>
        <div>
          <span>Velocity</span>
          {record.velocity_label}
        </div>
      </div>
    </article>
  )
}

function ArchiveSidebar({ densities, exportRecords }: { densities: EraDensity[]; exportRecords: ArchiveRecord[] }) {
  return (
    <aside className="archive-sidebar">
      <h3>Archival Context</h3>
      <div className="archive-plate">
        <img src={jobMarketImage} alt="Black-and-white job market newspaper clipping" />
      </div>
      <blockquote>
        “The labor market is a palimpsest; new titles are written over the fading ink of old operating models.”
      </blockquote>
      <p className="sidebar-attribution">— Dr. Aris Thorne, Chief Historian</p>
      <section className="sidebar-ledger" aria-label="Archive evidence summary">
        <div>
          <span>Source Class</span>
          <strong>Hiring Pages</strong>
        </div>
        <div>
          <span>Signal Cadence</span>
          <strong>Weekly</strong>
        </div>
        <div>
          <span>Archive Mode</span>
          <strong>Demo Corpus</strong>
        </div>
      </section>
      <section className="density-panel">
        <h4>Historical Frequency</h4>
        <ul>
          {densities.map((item) => (
            <li key={item.label}>
              <span>{item.label}</span>
              <i />
              <strong>{item.percentage}% Density</strong>
            </li>
          ))}
        </ul>
      </section>
      <button
        className="export-button"
        type="button"
        onClick={() => downloadArchiveCsv(exportRecords)}
        disabled={exportRecords.length === 0}
        title={exportRecords.length === 0 ? 'No records to export' : undefined}
      >
        Export Search Data (.CSV)
      </button>
    </aside>
  )
}

function ArchivePage({ data, onOpen }: { data: ArchiveResponse; onOpen: (recordId: string) => void }) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('ALL')
  const [page, setPage] = useState(() => archivePageFromHash())
  const presentCategories = BROAD_CATEGORIES.filter((name) =>
    data.records.some((record) => (record.categories ?? [record.category]).includes(name)),
  )
  const categories = ['ALL', ...presentCategories]
  const filtered = data.records.filter((record) => {
    const recordCategories = record.categories ?? [record.category]
    const text = `${record.title} ${record.category_detail ?? ''} ${recordCategories.join(' ')} ${record.early_mover_companies.join(' ')}`.toLowerCase()
    const matchesQuery = text.includes(query.toLowerCase())
    const matchesCategory = category === 'ALL' || recordCategories.includes(category)
    return matchesQuery && matchesCategory
  })
  const pageCount = Math.max(Math.ceil(filtered.length / PAGE_SIZE), 1)
  const currentPage = Math.min(page, pageCount - 1)
  const visibleRecords = filtered.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE)
  const emptySlots = Array.from({ length: PAGE_SIZE - visibleRecords.length }, (_, index) => index)

  useEffect(() => {
    const syncPage = () => setPage(archivePageFromHash())
    window.addEventListener('hashchange', syncPage)
    return () => window.removeEventListener('hashchange', syncPage)
  }, [])

  return (
    <>
      <section className="search-hero">
        <span>Archival Query</span>
        <label>
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              pushArchivePage(0)
            }}
            placeholder="Search the Archive"
          />
          <b aria-hidden="true">→</b>
        </label>
      </section>

      <section className="filter-strip" aria-label="Archive filters">
        <div>
          {categories.map((item) => (
            <button
              className={item === category ? 'active' : ''}
              key={item}
              type="button"
              onClick={() => {
                setCategory(item)
                pushArchivePage(0)
              }}
            >
              {item}
            </button>
          ))}
        </div>
        <p>Showing {filtered.length} Historical Records</p>
      </section>

      <section className="archive-layout">
        <div className="results-column">
          {filtered.length === 0 ? (
            <StatePanel>No records found in this edition.</StatePanel>
          ) : (
            <>
              {visibleRecords.map((record) => <ArchiveResult key={record.record_id} record={record} onOpen={onOpen} />)}
              {emptySlots.map((slot) => <div className="archive-result archive-result-placeholder" key={`empty-${slot}`} aria-hidden="true" />)}
              <nav className="archive-pagination" aria-label="Archive pagination">
                <button type="button" onClick={() => pushArchivePage(Math.max(currentPage - 1, 0))} disabled={currentPage === 0}>
                  ‹ Newer Records
                </button>
                <span>Archive Page {String(currentPage + 1).padStart(2, '0')} / {String(pageCount).padStart(2, '0')}</span>
                <button type="button" onClick={() => pushArchivePage(Math.min(currentPage + 1, pageCount - 1))} disabled={currentPage === pageCount - 1}>
                  Older Records ›
                </button>
              </nav>
            </>
          )}
        </div>
        <ArchiveSidebar densities={data.summary.era_density} exportRecords={filtered} />
      </section>
    </>
  )
}

function AdoptionChart({ points }: { points: AdoptionPoint[] }) {
  const maxValue = Math.max(...points.map((point) => point.value), 1)
  const coordinates = points.map((point, index) => {
    const x = points.length === 1 ? 100 : (index / (points.length - 1)) * 100
    const y = 100 - (point.value / maxValue) * 88
    return { ...point, x, y }
  })
  const path = coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')

  return (
    <section className="chart-panel">
      <h3>Fig 1.0: Adoption Velocity Index</h3>
      <div className="line-chart">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Adoption velocity line chart">
          <path d={path} />
          {coordinates.map((point) => (
            <circle key={point.label} cx={point.x} cy={point.y} r="1.6" />
          ))}
        </svg>
        {coordinates.map((point) =>
          point.annotation ? (
            <span className="chart-note" key={point.label} style={{ left: `${point.x}%`, top: `${point.y}%` }}>
              {point.annotation}
            </span>
          ) : null,
        )}
        <div className="axis start">{points[0]?.label}</div>
        <div className="axis end">{points[points.length - 1]?.label}</div>
      </div>
    </section>
  )
}

function SectorDensity({ sectors }: { sectors: SectorDensity[] }) {
  return (
    <section className="sector-panel">
      <h3>Fig 1.1: Sector Density Analysis</h3>
      {sectors.map((sector) => (
        <div className="sector-row" key={sector.sector}>
          <div>
            <span>{sector.sector}</span>
            <strong>{sector.percentage}%</strong>
          </div>
          <i><b style={{ width: `${sector.percentage}%` }} /></i>
        </div>
      ))}
      <div className="verified-stamp">Verified Archival Entry</div>
    </section>
  )
}

function DossierPage({ dossier, onArchive }: { dossier: DossierResponse; onArchive: () => void }) {
  return (
    <>
      <button className="back-link" type="button" onClick={onArchive}>← Back to archive</button>
      <section className="dossier-hero">
        <article>
          <span>Editorial Feature</span>
          <h2>{dossier.title}</h2>
          <p className="subheadline">{dossier.subheadline}</p>
          <div className="feature-grid">
            <p>{dossier.lead_paragraph}</p>
            <blockquote>“{dossier.pull_quote}”</blockquote>
          </div>
        </article>
        <aside>
          <div className="dossier-plate">
            <img src={dossier.image_path ?? jobMarketImage} alt={`${dossier.title} archival illustration`} />
          </div>
          <h3>Early Adopters Timeline</h3>
          <ul>
            {dossier.early_adopters.map((adopter) => (
              <li key={`${adopter.company}-${adopter.date_label}`}>
                <span>{adopter.date_label}</span>
                <strong>{adopter.company}</strong>
                <em>{adopter.location_label}</em>
              </li>
            ))}
          </ul>
        </aside>
      </section>

      <section className="dossier-data">
        <AdoptionChart points={dossier.adoption_points} />
        <SectorDensity sectors={dossier.sector_density} />
      </section>

      {dossier.serp_signals && dossier.serp_signals.length > 0 ? <SerpPanel signals={dossier.serp_signals} /> : null}

      <section className="detail-grid">
        <article>
          <h3>Preceding Titles</h3>
          <p>{dossier.preceding_titles.join(', ')}</p>
          <span>Data integrity verified by methodology group 7.</span>
        </article>
        <article>
          <h3>Required Competencies</h3>
          <ul>
            {dossier.competencies.map((competency) => <li key={competency}>{competency}</li>)}
          </ul>
        </article>
        <article>
          <h3>The 12-Month Outlook</h3>
          <p>{dossier.outlook}</p>
        </article>
      </section>
    </>
  )
}

function SerpPanel({ signals }: { signals: SerpSignal[] }) {
  return (
    <section className="serp-panel" aria-label="Press wire">
      <h3>Press Wire</h3>
      <p className="serp-byline">Open-web signals via Bright Data SERP API</p>
      <ul>
        {signals.map((signal) => (
          <li key={signal.url}>
            <a href={signal.url} target="_blank" rel="noreferrer noopener">{signal.title || signal.url}</a>
            <em>{signal.source}</em>
            <p>{signal.snippet}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

function VelocitySparkline({ buckets }: { buckets: WeeklyHire[] }) {
  if (buckets.length === 0) return <span className="sparkline-empty">No weekly history</span>
  const maxValue = Math.max(...buckets.map((b) => b.count), 1)
  const points = buckets.map((bucket, index) => {
    const x = buckets.length === 1 ? 100 : (index / (buckets.length - 1)) * 100
    const y = 100 - (bucket.count / maxValue) * 80
    return { x, y, label: bucket.week_start, value: bucket.count }
  })
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  return (
    <svg className="velocity-sparkline" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Weekly hires sparkline">
      <path d={path} />
      {points.map((p) => (
        <circle key={p.label} cx={p.x} cy={p.y} r="1.6" />
      ))}
    </svg>
  )
}

function CompanyTile({ signal, onOpen }: { signal: CompanySignal; onOpen: (key: string) => void }) {
  const buckets = signal.top_titles[0]?.weekly_buckets?.map((b) => ({ week_start: b.week_start, count: b.count })) ?? []
  return (
    <article className="company-tile" onClick={() => onOpen(signal.ticker ?? signal.company_key)}>
      <header>
        <span className="ticker">{signal.ticker ?? '—'}</span>
        <h3>{signal.display_name}</h3>
      </header>
      <div className="company-stats">
        <div>
          <span>Recent 30d</span>
          <strong>{signal.recent_hires_30d}</strong>
        </div>
        <div>
          <span>Prior 30d</span>
          <strong>{signal.prior_hires_30d}</strong>
        </div>
        <div>
          <span>Velocity</span>
          <strong>{signal.velocity_score.toFixed(2)}×</strong>
        </div>
      </div>
      <VelocitySparkline buckets={buckets} />
      <ul className="company-titles">
        {signal.top_titles.slice(0, 3).map((title) => (
          <li key={title.normalized_title_id}>
            <span>{title.display_title}</span>
            <strong>{title.count}</strong>
          </li>
        ))}
      </ul>
    </article>
  )
}

function CompanyWatchPage({ data, onOpen }: { data: CompanyListResponse; onOpen: (key: string) => void }) {
  return (
    <>
      <section className="search-hero">
        <span>Field Reports</span>
        <h2>Pre-earnings hiring signals</h2>
        <p className="subheadline">
          Tracking {data.summary.tracked_count} companies · {data.summary.total_recent_hires} fresh hires in last 30 days
        </p>
      </section>

      <section className="company-grid" aria-label="Company watch list">
        {data.companies.length === 0 ? (
          <StatePanel>No company signals computed yet. Run `python -m backend.companies.cli recompute`.</StatePanel>
        ) : (
          data.companies.map((signal) => (
            <CompanyTile key={signal.company_key} signal={signal} onOpen={onOpen} />
          ))
        )}
      </section>
    </>
  )
}

function CompanyDossierPage({ data, onCompanies }: { data: CompanyDossierResponse; onCompanies: () => void }) {
  const weeklyPoints: AdoptionPoint[] = data.weekly.map((bucket, index) => ({
    label: bucket.week_start,
    value: bucket.count,
    annotation: index === data.weekly.length - 1 ? 'Latest week' : null,
  }))
  return (
    <>
      <button className="back-link" type="button" onClick={onCompanies}>← Back to field reports</button>
      <section className="company-hero">
        <article>
          <span>Field Report</span>
          <h2>{data.company.display_name}</h2>
          <p className="subheadline">
            {data.company.ticker ? `${data.company.ticker} · ` : ''}
            {data.company.recent_hires_30d} hires in last 30 days · velocity {data.company.velocity_score.toFixed(2)}×
          </p>
        </article>
      </section>

      <section className="dossier-data">
        <section className="chart-panel">
          <h3>Fig 1.0: Weekly Hiring Curve</h3>
          {weeklyPoints.length > 0 ? (
            <AdoptionChart points={weeklyPoints} />
          ) : (
            <p className="state-panel">No weekly history available for this company.</p>
          )}
        </section>
        <section className="sector-panel">
          <h3>Fig 1.1: Top Roles</h3>
          {data.titles.map((title) => (
            <div className="sector-row" key={title.normalized_title_id}>
              <div>
                <span>{title.display_title}</span>
                <strong>{title.count}</strong>
              </div>
              <i><b style={{ width: `${Math.min(100, (title.count / Math.max(data.titles[0]?.count ?? 1, 1)) * 100)}%` }} /></i>
            </div>
          ))}
          <div className="verified-stamp">Bright Data Hiring Corpus</div>
        </section>
      </section>
    </>
  )
}

export default function App() {
  const [archive, setArchive] = useState<ArchiveResponse | null>(null)
  const [dossier, setDossier] = useState<DossierResponse | null>(null)
  const [companies, setCompanies] = useState<CompanyListResponse | null>(null)
  const [companyDossier, setCompanyDossier] = useState<CompanyDossierResponse | null>(null)
  const [view, setView] = useState<View>(() => viewFromHash())
  const [error, setError] = useState<string | null>(null)
  const [archiveReturnHash, setArchiveReturnHash] = useState('#/archive')

  useEffect(() => {
    const syncView = () => setView(viewFromHash())
    window.addEventListener('hashchange', syncView)
    return () => window.removeEventListener('hashchange', syncView)
  }, [])

  useEffect(() => {
    fetchArchiveTitles(50)
      .then(setArchive)
      .catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (view.name !== 'dossier') return
    setDossier(null)
    fetchArchiveDossier(view.recordId, 50)
      .then(setDossier)
      .catch((err: Error) => setError(err.message))
  }, [view])

  useEffect(() => {
    if (view.name !== 'companies' && view.name !== 'company') return
    if (companies) return
    fetchCompanies(20)
      .then(setCompanies)
      .catch((err: Error) => setError(err.message))
  }, [view, companies])

  useEffect(() => {
    if (view.name !== 'company') return
    setCompanyDossier(null)
    fetchCompanyDossier(view.key)
      .then(setCompanyDossier)
      .catch((err: Error) => setError(err.message))
  }, [view])

  const currentView = useMemo(() => {
    if (view.name === 'landing') {
      return <LandingPage onArchive={() => pushView({ name: 'archive' })} onCompanies={() => pushView({ name: 'companies' })} />
    }
    if (error) return <StatePanel>Archive feed interrupted · {error}</StatePanel>
    if (view.name === 'dossier') {
      if (!archive) return <StatePanel>Opening archive...</StatePanel>
      if (!dossier) return <StatePanel>Retrieving dossier...</StatePanel>
      return <DossierPage dossier={dossier} onArchive={() => { window.location.hash = archiveReturnHash }} />
    }
    if (view.name === 'companies') {
      if (!companies) return <StatePanel>Loading field reports...</StatePanel>
      return <CompanyWatchPage data={companies} onOpen={(key) => pushView({ name: 'company', key })} />
    }
    if (view.name === 'company') {
      if (!companyDossier) return <StatePanel>Loading company report...</StatePanel>
      return <CompanyDossierPage data={companyDossier} onCompanies={() => pushView({ name: 'companies' })} />
    }
    if (!archive) return <StatePanel>Opening archive...</StatePanel>
    return <ArchivePage data={archive} onOpen={(recordId) => {
      setArchiveReturnHash(window.location.hash || '#/archive')
      pushView({ name: 'dossier', recordId })
    }} />
  }, [archive, archiveReturnHash, dossier, companies, companyDossier, error, view])

  const activeSection: 'landing' | 'archive' | 'companies' =
    view.name === 'companies' || view.name === 'company'
      ? 'companies'
      : view.name === 'archive' || view.name === 'dossier'
        ? 'archive'
        : 'landing'

  return (
    <main className="archive-shell">
      <Masthead
        active={activeSection}
        onHome={() => pushView({ name: 'landing' })}
        onArchive={() => pushView({ name: 'archive' })}
        onCompanies={() => pushView({ name: 'companies' })}
      />
      {currentView}
      <Footer />
    </main>
  )
}
