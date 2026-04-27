import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from './route'
import { NextRequest } from 'next/server'
import { exec } from 'child_process'

// Mock child_process
vi.mock('child_process', () => {
  const m = {
    exec: vi.fn()
  }
  return {
    ...m,
    default: m
  }
})

describe('CORS Proxy API Route', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 400 if url parameter is missing', async () => {
    const request = new NextRequest('http://localhost:3000/api/proxy')
    const response = await GET(request)
    expect(response.status).toBe(400)
    const data = await response.json()
    expect(data.error).toBe('URL parameter is required')
  })

  it('returns 400 for invalid URLs', async () => {
    const request = new NextRequest('http://localhost:3000/api/proxy?url=invalid-url')
    const response = await GET(request)
    expect(response.status).toBe(400)
    const data = await response.json()
    expect(data.error).toBe('Invalid URL')
  })

  it('rewrites relative links and sources in the response body', async () => {
    const mockHtml = `
      <html>
        <body>
          <link rel="stylesheet" href="/style.css">
          <img src="logo.png">
          <a href="/about">About</a>
        </body>
      </html>
    `
    
    // Mock exec success
    vi.mocked(exec).mockImplementation((cmd, options, callback) => {
      const cb = typeof options === 'function' ? options : callback
      if (cb) {
        cb(null, { stdout: mockHtml, stderr: '' } as any)
      }
      return {} as any
    })

    const request = new NextRequest('http://localhost:3000/api/proxy?url=https://example.com/page')
    const response = await GET(request)
    const body = await response.text()

    expect(body).toContain('https://example.com/style.css')
    expect(body).toContain('https://example.com/logo.png')
    expect(body).toContain('https://example.com/about')
  })
})
