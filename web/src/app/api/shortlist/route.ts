import { NextResponse } from 'next/server'
import { db } from '../../../../db'
import { leads } from '../../../../db/schema'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  courseIds: z.array(z.string()).min(1),
})

export async function POST(req: Request) {
  const body = await req.json().catch(() => null)
  const parsed = schema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
  await db.insert(leads).values({
    email: parsed.data.email,
    courseIds: parsed.data.courseIds as `${string}-${string}-${string}-${string}-${string}`[],
  })
  return NextResponse.json({ ok: true })
}
