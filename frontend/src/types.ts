export type DashboardTrendCard = {
  rank: number
  title: string
  score: number
  recent_count: number
  prior_count: number
  newness: number
  velocity: number
  concentration: number
  early_mover_companies: string[]
  narrative: string
}

export type DashboardSummary = {
  trend_count: number
  average_score: number
  early_mover_count: number
}

export type DashboardResponse = {
  trends: DashboardTrendCard[]
  summary: DashboardSummary
}

export type ArchiveRecord = {
  record_id: string
  title: string
  category: string
  first_seen_label: string
  velocity_label: string
  score: number
  recent_count: number
  prior_count: number
  early_mover_companies: string[]
  excerpt: string
  image_path?: string | null
}

export type EraDensity = {
  label: string
  percentage: number
}

export type ArchiveSummary = {
  total_records: number
  category_counts: Record<string, number>
  era_density: EraDensity[]
}

export type ArchiveResponse = {
  records: ArchiveRecord[]
  summary: ArchiveSummary
}

export type AdoptionPoint = {
  label: string
  value: number
  annotation?: string | null
}

export type SectorDensity = {
  sector: string
  percentage: number
}

export type EarlyAdopter = {
  company: string
  date_label: string
  location_label: string
}

export type DossierResponse = ArchiveRecord & {
  subheadline: string
  lead_paragraph: string
  pull_quote: string
  adoption_points: AdoptionPoint[]
  sector_density: SectorDensity[]
  early_adopters: EarlyAdopter[]
  preceding_titles: string[]
  competencies: string[]
  outlook: string
}
