import { getArea, getMonogram, atarColor, AREAS } from '@/lib/area-map'

test('maps engineering faculty', () => expect(getArea('Faculty of Engineering')).toBe('engineering'))
test('maps medicine faculty', () => expect(getArea('Melbourne Medical School')).toBe('medicine'))
test('maps business faculty', () => expect(getArea('Faculty of Business and Economics')).toBe('business'))
test('returns null for unknown faculty', () => expect(getArea('Misc Department')).toBeNull())
test('returns null for null input', () => expect(getArea(null)).toBeNull())
test('AREAS has 11 entries', () => expect(Object.keys(AREAS)).toHaveLength(11))

test('monogram skips prepositions', () => expect(getMonogram('University of Melbourne')).toBe('UM'))
test('monogram takes first 2 significant initials', () => expect(getMonogram('RMIT University')).toBe('RU'))
test('monogram for Monash University', () => expect(getMonogram('Monash University')).toBe('MU'))

test('atarColor red for 95+', () => expect(atarColor(95)).toBe('#ef4444'))
test('atarColor orange for 85-94', () => expect(atarColor(85)).toBe('#f97316'))
test('atarColor yellow for 75-84', () => expect(atarColor(80)).toBe('#eab308'))
test('atarColor green for under 75', () => expect(atarColor(70)).toBe('#22c55e'))
