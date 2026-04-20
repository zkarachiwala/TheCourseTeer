import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Page from './page'

describe('Scraper Builder Admin Page', () => {
  it('renders the scraper builder heading', () => {
    render(<Page />)
    expect(screen.getByRole('heading', { name: /Visual Scraper Builder/i })).toBeDefined()
  })

  it('contains a URL input for the preview', () => {
    render(<Page />)
    expect(screen.getByPlaceholderText(/Enter course URL/i)).toBeDefined()
  })

  it('shows an error message for an invalid URL on submit', () => {
    render(<Page />)
    const input = screen.getByPlaceholderText(/Enter course URL/i)
    const button = screen.getByRole('button', { name: /Preview/i })
    
    // Test invalid URL
    fireEvent.change(input, { target: { value: 'not-a-url' } })
    fireEvent.click(button)
    expect(screen.getByText(/Please enter a valid URL/i)).toBeDefined()
  })

  it('shows an error message for empty input on submit', () => {
    render(<Page />)
    const button = screen.getByRole('button', { name: /Preview/i })
    
    fireEvent.click(button)
    expect(screen.getByText(/Please enter a URL/i)).toBeDefined()
  })

  it('renders an iframe when a valid URL is provided', () => {
    render(<Page />)
    const input = screen.getByPlaceholderText(/Enter course URL/i)
    const button = screen.getByRole('button', { name: /Preview/i })
    
    fireEvent.change(input, { target: { value: 'https://example.com' } })
    fireEvent.click(button)
    
    const iframe = screen.getByTitle(/Course Page Preview/i) as HTMLIFrameElement
    expect(iframe).toBeDefined()
    expect(iframe.src).toContain(encodeURIComponent('https://example.com'))
  })
})
