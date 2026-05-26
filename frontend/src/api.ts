import type { ArchiveResponse, DashboardResponse, DossierResponse } from './types'

export async function fetchDashboardTrends(limit = 5): Promise<DashboardResponse> {
  const response = await fetch(`/dashboard/trends?limit=${limit}`)
  if (!response.ok) {
    throw new Error(`dashboard request failed: ${response.status}`)
  }
  return response.json()
}

export async function fetchArchiveTitles(limit = 10): Promise<ArchiveResponse> {
  const response = await fetch(`/archive/titles?limit=${limit}`)
  if (!response.ok) {
    throw new Error(`archive request failed: ${response.status}`)
  }
  return response.json()
}

export async function fetchArchiveDossier(recordId: string, limit = 10): Promise<DossierResponse> {
  const response = await fetch(`/archive/titles/${encodeURIComponent(recordId)}?limit=${limit}`)
  if (!response.ok) {
    throw new Error(`dossier request failed: ${response.status}`)
  }
  return response.json()
}
