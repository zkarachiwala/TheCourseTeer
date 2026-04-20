import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from './route'
import { NextRequest } from 'next/server'

describe('CORS Proxy API Route', () => {
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
    // This requires mocking fetch
    const mockHtml = `
      <html>
        <head>
          <link rel="stylesheet" href="/style.css">
        </head>
        <body>
          <img src="logo.png">
          <a href="/about">About</a>
        </body>
      </html>
    `
    
    const mockResponse = {
      status: 200,
      text: () => Promise.resolve(mockHtml),
      headers: {
        get: (name: string) => name === 'content-type' ? 'text/html' : null
      }
    }

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockResponse))

    const request = new NextRequest('http://localhost:3000/api/proxy?url=https://example.com/page')
    const response = await GET(request)
    const body = await response.text()

    expect(body).toContain('https://example.com/style.css')
    expect(body).toContain('https://example.com/logo.png')
    expect(body).toContain('https://example.com/about')

    vi.unstubAllGlobals()
  })
})
