import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ShortlistProvider } from '@/contexts/shortlist-context'
import { CourseListClient } from '@/components/course-list-client'
import type { FetchCoursePageParams } from '@/lib/queries/courses'

// Use vi.hoisted so mockReplace is available when vi.mock factory runs
const mockReplace = vi.hoisted(() => vi.fn())

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace, push: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => '/courses',
}))

beforeEach(() => mockReplace.mockClear())

const baseParams: FetchCoursePageParams = { page: 1, pageSize: 48, filters: {} }

const baseProps = {
  courses: [],
  total: 0,
  availableDurations: [3, 4],
  universities: [{ slug: 'rmit', name: 'RMIT University' }],
  currentParams: baseParams,
}

function renderWithProviders(ui: React.ReactElement) {
  return render(<ShortlistProvider>{ui}</ShortlistProvider>)
}

describe('CourseListClient', () => {
  it('displays the correct course count', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={128} />)
    expect(screen.getByText('128 courses')).toBeInTheDocument()
  })

  it('displays singular "course" for count of 1', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={1} />)
    expect(screen.getByText('1 course')).toBeInTheDocument()
  })

  it('does not show pagination when total equals pageSize', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={48} />)
    expect(screen.queryByText('← Prev')).not.toBeInTheDocument()
  })

  it('does not show pagination when total is less than pageSize', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={20} />)
    expect(screen.queryByText('← Prev')).not.toBeInTheDocument()
  })

  it('shows pagination controls when total exceeds pageSize', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={100} />)
    expect(screen.getByText('← Prev')).toBeInTheDocument()
    expect(screen.getByText('Next →')).toBeInTheDocument()
  })

  it('prev button is disabled on page 1', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={100} />)
    expect(screen.getByText('← Prev')).toBeDisabled()
  })

  it('next button is disabled on last page', () => {
    // total=144, pageSize=48 → 3 pages, page 3 is last
    const params: FetchCoursePageParams = { page: 3, pageSize: 48, filters: {} }
    renderWithProviders(
      <CourseListClient {...baseProps} total={144} currentParams={params} />
    )
    expect(screen.getByText('Next →')).toBeDisabled()
  })

  it('next button calls router.replace with page=2', () => {
    renderWithProviders(<CourseListClient {...baseProps} total={100} />)
    fireEvent.click(screen.getByText('Next →'))
    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining('page=2'),
      expect.anything()
    )
  })

  it('prev button calls router.replace with previous page number', () => {
    const params: FetchCoursePageParams = { page: 3, pageSize: 48, filters: {} }
    renderWithProviders(
      <CourseListClient {...baseProps} total={200} currentParams={params} />
    )
    fireEvent.click(screen.getByText('← Prev'))
    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining('page=2'),
      expect.anything()
    )
  })

  it('page size change calls router.replace with new pageSize and resets to page 1', () => {
    const params: FetchCoursePageParams = { page: 3, pageSize: 48, filters: {} }
    renderWithProviders(
      <CourseListClient {...baseProps} total={200} currentParams={params} />
    )
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '24' } })
    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining('pageSize=24'),
      expect.anything()
    )
    // page resets to 1, which is omitted from the URL (default)
    expect(mockReplace).toHaveBeenCalledWith(
      expect.not.stringContaining('page='),
      expect.anything()
    )
  })

  it('clear filters calls router.replace with an empty query string', () => {
    const params: FetchCoursePageParams = {
      page: 2,
      pageSize: 48,
      filters: { search: 'law', areas: ['law'] },
    }
    renderWithProviders(
      <CourseListClient {...baseProps} total={100} currentParams={params} />
    )
    fireEvent.click(screen.getByText('Clear all'))
    expect(mockReplace).toHaveBeenCalledWith('/courses', expect.objectContaining({ scroll: false }))
  })
})
