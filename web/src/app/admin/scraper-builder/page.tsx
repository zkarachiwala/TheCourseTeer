'use client'

import React, { useState, useEffect } from 'react'
import { saveScraperConfig } from './actions'

export default function ScraperBuilderPage() {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null)
  
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedSelector, setSelectedSelector] = useState<string | null>(null)
  const [selectedText, setSelectedText] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState<string>('/')
  const [selectedField, setSelectedField] = useState<string>('')
  const [aiParsedValue, setAiParsedValue] = useState<string | null>(null)
  const [isAiLoading, setIsAiLoading] = useState(false)
  
  const [isTaggingMode, setIsTaggingMode] = useState(true)
  const [history, setHistory] = useState<string[]>([])

  useEffect(() => {
    async function getAiPreview() {
      if (selectedField && selectedText) {
        setIsAiLoading(true)
        setAiParsedValue(null)
        const { parseWithAI } = await import('./actions')
        const result = await parseWithAI(selectedField, selectedText)
        if (result.result) {
          setAiParsedValue(result.result)
        } else {
          setAiParsedValue('Error parsing value')
        }
        setIsAiLoading(false)
      } else {
        setAiParsedValue(null)
      }
    }
    getAiPreview()
  }, [selectedField, selectedText])

  useEffect(() => {
    if (saveStatus) {
      const timer = setTimeout(() => setSaveStatus(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [saveStatus])

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'ELEMENT_SELECTED') {
        if (isTaggingMode) {
          setSelectedSelector(event.data.selector)
          setSelectedText(event.data.text)
          setSaveStatus(null)
        }
      } else if (event.data.type === 'NAVIGATE') {
        const newUrl = event.data.url
        if (previewUrl) {
          const base = new URL(previewUrl).origin
          if (newUrl.startsWith(base)) {
            const path = newUrl.substring(base.length) || '/'
            if (path !== currentPath) {
              setHistory(prev => [...prev, currentPath])
              setCurrentPath(path)
            }
          }
        }
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [previewUrl, currentPath, isTaggingMode])

  // Inform iframe of tagging mode changes
  useEffect(() => {
    const iframe = document.querySelector('iframe')
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage({
        type: 'SET_TAGGING_MODE',
        enabled: isTaggingMode
      }, '*')
    }
  }, [isTaggingMode])

  const handleBack = () => {
    if (history.length > 0) {
      const prevPath = history[history.length - 1]
      setHistory(prev => prev.slice(0, -1))
      setCurrentPath(prevPath)
    }
  }

  const handlePreview = async () => {
    setError(null)
    setPreviewUrl(null)
    setSelectedSelector(null)
    setHistory([])
    
    if (!url) {
      setError('Please enter a URL')
      return
    }

    try {
      const parsedUrl = new URL(url)
      setIsLoading(true)
      setPreviewUrl(parsedUrl.origin)
      setCurrentPath(parsedUrl.pathname + parsedUrl.search + parsedUrl.hash)
    } catch (e) {
      setError('Please enter a valid URL')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!previewUrl || !selectedSelector || !selectedField) return;

    setIsSaving(true)
    setSaveStatus(null)

    const result = await saveScraperConfig({
      universityOrigin: previewUrl,
      fieldName: selectedField,
      selector: selectedSelector,
      urlPath: currentPath
    })

    if (result.success) {
      setSaveStatus({ type: 'success', message: 'Configuration saved successfully!' })
      // Keep selector visible so user knows what was saved, but clear field
      setSelectedField('')
    } else {
      setSaveStatus({ type: 'error', message: result.error || 'Failed to save' })
    }
    
    setIsSaving(false)
  }

  const iframeSrc = previewUrl 
    ? `/api/proxy?url=${encodeURIComponent(new URL(currentPath, previewUrl).toString())}`
    : ''

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-gray-100">Visual Scraper Builder</h1>
      
      <div className="max-w-2xl">
        <div className="flex flex-col gap-2 mb-8">
          <div className="flex gap-4">
            <input 
              type="url" 
              placeholder="Enter course URL" 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className={`flex-1 p-2 border rounded ${
                error ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
              } bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100`}
            />
            <button 
              disabled={isLoading}
              onClick={handlePreview}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
            >
              {isLoading ? 'Loading...' : 'Preview'}
            </button>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          {isLoading && <p className="text-blue-500 text-sm italic">Loading site... (may take up to 10 seconds)</p>}
        </div>
      </div>

      {previewUrl && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 flex flex-col gap-2">
            <div className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 border rounded text-xs font-mono">
              <div className="flex items-center gap-4 text-gray-900 dark:text-gray-100">
                <button 
                  onClick={handleBack}
                  disabled={history.length === 0}
                  className="flex items-center gap-1 px-2 py-1 bg-white dark:bg-gray-700 border rounded hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                >
                  ← Back
                </button>
                <div className="truncate max-w-md">
                  Mapping: <span className="text-blue-600 dark:text-blue-400">{currentPath}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-gray-900 dark:text-gray-100">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={isTaggingMode}
                    onChange={(e) => setIsTaggingMode(e.target.checked)}
                    className="w-4 h-4 accent-blue-600"
                  />
                  <span>Tagging Mode</span>
                </label>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  isTaggingMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-700'
                }`}>
                  {isTaggingMode ? 'ON' : 'OFF'}
                </span>
              </div>
            </div>
            <div className="border rounded overflow-hidden h-[700px] bg-white">
              <iframe 
                src={iframeSrc}
                className="w-full h-full border-none"
                title="Course Page Preview"
                sandbox="allow-scripts allow-same-origin allow-forms"
              />
            </div>
          </div>
          
          <div className="border rounded p-4 bg-gray-50 dark:bg-gray-900 h-fit">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Selector Details</h2>
            
            {selectedSelector ? (
              <div className="flex flex-col gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500 uppercase">Selected Text</p>
                  <div className="p-2 bg-white dark:bg-gray-800 border rounded text-sm italic text-gray-700 dark:text-gray-300">
                    "{selectedText}"
                  </div>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-500 uppercase">Generated Selector</p>
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 border rounded font-mono text-xs break-all text-gray-800 dark:text-gray-200">
                    {selectedSelector}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-500 uppercase">Target Page Path</p>
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 border rounded font-mono text-xs break-all text-gray-800 dark:text-gray-200">
                    {currentPath}
                  </div>
                </div>

                <div className="mt-4">
                  <p className="text-sm font-medium mb-2 uppercase text-gray-500">Assign to Field</p>
                  <select 
                    value={selectedField}
                    onChange={(e) => setSelectedField(e.target.value)}
                    className="w-full p-2 border rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select a field...</option>
                    <optgroup label="Course Details">
                      <option value="name">Course Name</option>
                      <option value="faculty">Faculty</option>
                      <option value="degree_type">Degree Type (UG/PG)</option>
                      <option value="duration_years">Duration (Years)</option>
                      <option value="prerequisites">Prerequisites</option>
                    </optgroup>
                    <optgroup label="Admissions (Per Campus)">
                      <option value="atar_guaranteed">ATAR (Guaranteed)</option>
                      <option value="atar_lowest_selection_rank">ATAR (Lowest Selection Rank)</option>
                      <option value="campus_name">Campus Name</option>
                    </optgroup>
                    <optgroup label="Fees">
                      <option value="price_annual_csp_aud">Annual CSP Fee (AUD)</option>
                      <option value="price_annual_dfee_aud">Annual Domestic Full Fee (AUD)</option>
                      <option value="csp_available">CSP Available? (Yes/No)</option>
                    </optgroup>
                  </select>
                </div>

                {selectedField && (
                  <div className="p-3 bg-white dark:bg-gray-800 border rounded border-blue-100 dark:border-blue-900 shadow-sm">
                    <p className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase mb-1 flex items-center gap-2">
                      <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                      AI Parsing Preview
                    </p>
                    <div className="text-sm font-mono break-all">
                      {isAiLoading ? (
                        <span className="text-gray-400 italic">Processing with AI...</span>
                      ) : (
                        <span className="text-gray-900 dark:text-gray-100">
                          {aiParsedValue || 'No data'}
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-gray-500 mt-2 italic">
                      This is how the scraper will store the value in the database.
                    </p>
                  </div>
                )}
                
                <button 
                  disabled={!selectedField || isSaving}
                  onClick={handleSave}
                  className="w-full py-2 bg-green-600 text-white rounded hover:bg-green-700 mt-2 disabled:bg-green-400"
                >
                  {isSaving ? 'Saving...' : 'Save Configuration'}
                </button>

                {saveStatus && (
                  <p className={`mt-2 text-sm text-center ${
                    saveStatus.type === 'success' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {saveStatus.message}
                  </p>
                )}
              </div>
            ) : (
              <div className="text-gray-500 italic flex flex-col gap-4">
                <p>Click an element in the preview to select it.</p>
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-100 dark:border-blue-800 text-sm not-italic">
                  <p className="font-semibold text-blue-700 dark:text-blue-300 mb-1">Pro Tip:</p>
                  <p>Disable <strong>Tagging Mode</strong> to interact with popups or accept cookies, then enable it when you're ready to select data.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
