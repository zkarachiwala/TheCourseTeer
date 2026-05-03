import { describe, it, expect, beforeEach, vi } from 'vitest'

// vi.mock is hoisted — must appear before imports of the module under test
vi.mock('../../../db', () => ({
  db: { execute: vi.fn() },
}))

// db/schema is pure table definitions — no IO, no mock needed

import { parseSearchParams, fetchCoursePage } from '@/lib/queries/courses'
import { db } from '../../../db'

const mockExecute = vi.mocked(db.execute)

// ─── parseSearchParams ────────────────────────────────────────────────────────

describe('parseSearchParams', () => {
  it('returns defaults for empty input', () => {
    const r = parseSearchParams({})
    expect(r.page).toBe(1)
    expect(r.pageSize).toBe(48)
    expect(r.filters).toEqual({})
    expect(r.slug).toBeUndefined()
  })

  it('parses page and pageSize', () => {
    const r = parseSearchParams({ page: '3', pageSize: '24' })
    expect(r.page).toBe(3)
    expect(r.pageSize).toBe(24)
  })

  it('falls back to pageSize 48 for out-of-range value', () => {
    expect(parseSearchParams({ pageSize: '100' }).pageSize).toBe(48)
  })

  it('falls back to pageSize 48 for non-numeric value', () => {
    expect(parseSearchParams({ pageSize: 'abc' }).pageSize).toBe(48)
  })

  it('parses areas from comma-delimited string', () => {
    expect(parseSearchParams({ areas: 'law,science' }).filters.areas).toEqual(['law', 'science'])
  })

  it('parses areas from string array', () => {
    expect(parseSearchParams({ areas: ['law', 'science'] }).filters.areas).toEqual(['law', 'science'])
  })

  it('returns undefined areas for empty string', () => {
    expect(parseSearchParams({ areas: '' }).filters.areas).toBeUndefined()
  })

  it('parses minAtar as number', () => {
    expect(parseSearchParams({ minAtar: '75' }).filters.minAtar).toBe(75)
  })

  it('returns undefined minAtar for non-numeric input', () => {
    expect(parseSearchParams({ minAtar: 'abc' }).filters.minAtar).toBeUndefined()
  })

  it('passes slug from opts', () => {
    expect(parseSearchParams({}, { slug: 'rmit' }).slug).toBe('rmit')
  })

  it('clamps page to minimum 1 for zero', () => {
    expect(parseSearchParams({ page: '0' }).page).toBe(1)
  })

  it('clamps page to minimum 1 for negative values', () => {
    expect(parseSearchParams({ page: '-5' }).page).toBe(1)
  })
})

// ─── fetchCoursePage ──────────────────────────────────────────────────────────

const mockDataRow = {
  id: 'abc-def',
  name: 'Bachelor of Science',
  faculty: 'Science',
  degreeType: 'UG',
  durationYears: '3',
  sourceUrl: 'https://example.com',
  universityName: 'RMIT University',
  universitySlug: 'rmit',
  atarGuaranteed: '70',
  atarSelectionRank: null,
  campusName: 'City',
}

describe('fetchCoursePage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns rows, total, and availableDurations', async () => {
    mockExecute
      .mockResolvedValueOnce([mockDataRow] as any)
      .mockResolvedValueOnce([{ count: '1' }] as any)
      .mockResolvedValueOnce([{ durationYears: '3' }] as any)

    const result = await fetchCoursePage({ page: 1, pageSize: 48, filters: {} })

    expect(result.rows).toHaveLength(1)
    expect(result.total).toBe(1)
    expect(result.availableDurations).toEqual([3])
  })

  it('coerces numeric string columns from postgres to JS numbers', async () => {
    mockExecute
      .mockResolvedValueOnce([mockDataRow] as any)
      .mockResolvedValueOnce([{ count: '1' }] as any)
      .mockResolvedValueOnce([{ durationYears: '3' }] as any)

    const result = await fetchCoursePage({ page: 1, pageSize: 48, filters: {} })

    expect(result.rows[0].durationYears).toBe(3)
    expect(result.rows[0].atarGuaranteed).toBe(70)
    expect(result.rows[0].atarSelectionRank).toBeNull()
  })

  it('runs 3 parallel queries (data, count, durations)', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: {} })

    expect(mockExecute).toHaveBeenCalledTimes(3)
  })

  it('applies OFFSET for page 2 with pageSize 24', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 2, pageSize: 24, filters: {} })

    const dataQuery = mockExecute.mock.calls[0][0]
    const queryStr = JSON.stringify(dataQuery)
    // OFFSET 24 = (page-1) * pageSize = 1 * 24
    expect(queryStr).toContain('24')
  })

  it('includes ILIKE clause when search filter is set', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: { search: 'law' } })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('ILIKE')
  })

  it('includes regex clause (~*) when areas filter is set', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: { areas: ['law'] } })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('~*')
  })

  it('includes ANY clause when unis filter is set', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: { unis: ['rmit', 'monash'] } })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('ANY')
  })

  it('includes durations ANY clause when durations filter is set', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: { durations: ['3', '4'] } })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('ANY')
  })

  it('includes COALESCE clause when minAtar filter is set', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ page: 1, pageSize: 48, filters: { minAtar: 70 } })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('COALESCE')
  })

  it('scopes data and count queries to university slug', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ slug: 'rmit', page: 1, pageSize: 48, filters: {} })

    const dataQuery = JSON.stringify(mockExecute.mock.calls[0][0])
    expect(dataQuery).toContain('rmit')
    const countQuery = JSON.stringify(mockExecute.mock.calls[1][0])
    expect(countQuery).toContain('rmit')
  })

  it('scopes durations query to slug but not other filters', async () => {
    mockExecute
      .mockResolvedValueOnce([] as any)
      .mockResolvedValueOnce([{ count: '0' }] as any)
      .mockResolvedValueOnce([] as any)

    await fetchCoursePage({ slug: 'federation', page: 1, pageSize: 48, filters: { search: 'nursing' } })

    // durations query (3rd call) should contain the slug but NOT the search term
    const durQuery = JSON.stringify(mockExecute.mock.calls[2][0])
    expect(durQuery).toContain('federation')
    expect(durQuery).not.toContain('ILIKE')
  })
})
