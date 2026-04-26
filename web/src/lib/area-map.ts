export const AREAS = {
  science:     { label: 'Science',     color: '#6366f1' },
  business:    { label: 'Business',    color: '#0ea5e9' },
  engineering: { label: 'Engineering', color: '#f97316' },
  technology:  { label: 'Technology',  color: '#8b5cf6' },
  design:      { label: 'Design',      color: '#ec4899' },
  arts:        { label: 'Arts',        color: '#14b8a6' },
  medicine:    { label: 'Medicine',    color: '#ef4444' },
  law:         { label: 'Law',         color: '#a16207' },
  health:      { label: 'Health',      color: '#22c55e' },
  education:   { label: 'Education',   color: '#06b6d4' },
  sport:       { label: 'Sport',       color: '#84cc16' },
} as const

export type AreaKey = keyof typeof AREAS

const FACULTY_MAP: Array<[RegExp, AreaKey]> = [
  [/engineering|electrical|civil|mechanical|chemical/i, 'engineering'],
  [/information technology|computer science|software|cybersecurity|data science/i, 'technology'],
  [/business|commerce|economics|management|accounting|finance|marketing/i, 'business'],
  [/medicine|medical|nursing|pharmacy|dentist|dental/i, 'medicine'],
  [/law|legal/i, 'law'],
  [/science|chemistry|physics|biology|mathematics|environmental/i, 'science'],
  [/health|physiotherapy|nutrition|rehabilitation|allied health/i, 'health'],
  [/education|teaching/i, 'education'],
  [/design|architecture|fashion|visual|media arts/i, 'design'],
  [/arts|humanities|history|philosophy|languages|literature|music|creative/i, 'arts'],
  [/sport|kinesiology|exercise/i, 'sport'],
]

export function getArea(faculty: string | null | undefined): AreaKey | null {
  if (!faculty) return null
  for (const [pattern, area] of FACULTY_MAP) {
    if (pattern.test(faculty)) return area
  }
  return null
}

export function getAreasFromName(name: string): AreaKey[] {
  if (!name.includes('/')) return []
  const areas: AreaKey[] = []
  for (const part of name.split('/')) {
    for (const [pattern, area] of FACULTY_MAP) {
      if (pattern.test(part) && !areas.includes(area)) { areas.push(area); break }
    }
  }
  return areas
}

export function degreeLabel(type: string | null | undefined): string {
  if (type === 'UG') return 'Undergraduate'
  if (type === 'PG') return 'Postgraduate'
  return type ?? ''
}

const SKIP = new Set(['of', 'and', 'the', 'for', 'in', 'at', 'a', 'an'])

export function getMonogram(name: string): string {
  return name
    .split(' ')
    .filter(w => w.length > 0 && !SKIP.has(w.toLowerCase()))
    .map(w => w[0].toUpperCase())
    .slice(0, 2)
    .join('')
}

export function atarColor(atar: number): string {
  if (atar >= 95) return '#ef4444'
  if (atar >= 85) return '#f97316'
  if (atar >= 75) return '#eab308'
  return '#22c55e'
}
