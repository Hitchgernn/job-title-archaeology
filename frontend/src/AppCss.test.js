import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const appCss = readFileSync(resolve(import.meta.dirname, 'App.css'), 'utf-8')

describe('App CSS', () => {
  it('keeps pagination spacing balanced above and below the rule', () => {
    expect(appCss).toContain('padding-top: 18px;\n  padding-bottom: 18px;')
  })

  it('uses full-width archive result layout without the removed image column', () => {
    expect(appCss).not.toContain('grid-template-columns: 132px minmax(0, 1fr)')
  })

  it('keeps the landing signal strip moving like the reference', () => {
    expect(appCss).toContain('@keyframes landing-ticker')
    expect(appCss).toContain('animation: landing-ticker 30s linear infinite;')
  })
})
