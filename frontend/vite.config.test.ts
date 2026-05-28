import { describe, expect, it } from 'vitest'
import config from './vite.config'

describe('vite proxy config', () => {
  it('does not proxy generated archive image assets to the backend', () => {
    const proxy = config.server?.proxy ?? {}

    expect(Object.keys(proxy)).not.toContain('/archive')
    expect(Object.keys(proxy)).toContain('^/archive(/|$)')
  })
})
