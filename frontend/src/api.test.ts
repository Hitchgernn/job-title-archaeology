import { describe, expect, it, vi } from 'vitest'
import { fetchDashboardTrends } from './api'

describe('fetchDashboardTrends', () => {
  it('fetches dashboard trends with limit', async () => {
    const payload = { trends: [], summary: { trend_count: 0, average_score: 0, early_mover_count: 0 } }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => payload }))

    const result = await fetchDashboardTrends(7)

    expect(fetch).toHaveBeenCalledWith('/dashboard/trends?limit=7')
    expect(result).toEqual(payload)
  })

  it('throws when request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))

    await expect(fetchDashboardTrends()).rejects.toThrow('dashboard request failed: 500')
  })
})
