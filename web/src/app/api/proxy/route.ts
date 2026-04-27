import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execPromise = promisify(exec)

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const targetUrl = searchParams.get('url')

  if (!targetUrl) {
    return NextResponse.json({ error: 'URL parameter is required' }, { status: 400 })
  }

  let urlObj: URL
  try {
    urlObj = new URL(targetUrl)
  } catch (e) {
    return NextResponse.json({ error: 'Invalid URL' }, { status: 400 })
  }

  try {
    let body: string
    let contentType = 'text/html'
    let status = 200

    // Check if the request is for a known static resource extension
    const isResource = /\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|otf|ico)$/i.test(urlObj.pathname)

    if (isResource) {
      // For static resources, use standard fetch
      const response = await fetch(urlObj.toString(), {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
      })
      
      const buffer = await response.arrayBuffer()
      contentType = response.headers.get('content-type') || 'application/octet-stream'
      
      return new NextResponse(buffer, {
        status: response.status,
        headers: {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600',
        },
      })
    } else {
      // Use Python with Playwright for HTML pages to render fully and bypass bot detection
      const pythonCommand = `cd ../scraper && uv run python fetch_page.py "${targetUrl}"`
      
      const { stdout, stderr } = await execPromise(pythonCommand, { maxBuffer: 1024 * 1024 * 10 })
      
      if (!stdout && stderr) {
        throw new Error(`Python script error: ${stderr}`)
      }
      body = stdout
    }

    const responseHeaders = new Headers()
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Content-Type', 'text/html; charset=utf-8')

    // Rewrite relative URLs and strip scripts if it's an HTML page
    if (body) {
      const baseUrl = urlObj.origin
      const pageBase = targetUrl.substring(0, targetUrl.lastIndexOf('/') + 1)
      
      // 1. Strip all original script tags to prevent redirects/interruption
      // We keep our own overlay script which will be injected later
      body = body.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      
      // 2. Rewrite relative URLs
      body = body.replace(/(href|src)=["']([^"']+)["']/g, (match, attr, val) => {
        if (val.startsWith('http') || val.startsWith('//') || val.startsWith('data:')) {
          return match
        }
        
        // Handle absolute-path relative URLs (/path)
        if (val.startsWith('/')) {
          return `${attr}="${baseUrl}${val}"`
        }
        
        // Handle relative-path relative URLs (path)
        return `${attr}="${pageBase}${val}"`
      })

      // 3. Inject our overlay script at the end of the body
      body = body.replace('</body>', '<script src="/scraper-builder-overlay.js"></script></body>')
      
      // If no </body> tag found, just append it
      if (!body.includes('/scraper-builder-overlay.js')) {
        body += '<script src="/scraper-builder-overlay.js"></script>'
      }
    }

    return new NextResponse(body, {
      status,
      headers: responseHeaders,
    })
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json({ error: 'Failed to fetch the URL' }, { status: 500 })
  }
}
