'use server'

import { db } from '@/../db'
import { scraperConfigs, universities } from '@/../db/schema'
import { eq, and } from 'drizzle-orm'
import { v4 as uuidv4 } from 'uuid'
import { revalidatePath } from 'next/cache'
import { exec } from 'child_process'
import { promisify } from 'util'

const execPromise = promisify(exec)

export async function saveScraperConfig(data: {
  universityOrigin: string;
  fieldName: string;
  selector: string;
  urlPath: string;
}) {
  try {
    // 1. Find the university by origin/homepage_url
    // In a real app, we'd probably have a dropdown to select the university first,
    // but for this POC we'll try to match the origin.
    const university = await db.query.universities.findFirst({
      where: (u, { like }) => like(u.homepageUrl, `${data.universityOrigin}%`)
    })

    if (!university) {
      return { error: `Could not find university with origin ${data.universityOrigin}. Please ensure the university is seeded in the database.` }
    }

    // 2. Check if a config for this field already exists
    const existing = await db.query.scraperConfigs.findFirst({
      where: and(
        eq(scraperConfigs.universityId, university.id),
        eq(scraperConfigs.fieldName, data.fieldName)
      )
    })

    if (existing) {
      // Update
      await db.update(scraperConfigs)
        .set({
          selector: data.selector,
          urlPath: data.urlPath,
          lastVerifiedAt: new Date(),
          aiGenerated: false
        })
        .where(eq(scraperConfigs.id, existing.id))
    } else {
      // Insert
      await db.insert(scraperConfigs).values({
        id: uuidv4(),
        universityId: university.id,
        fieldName: data.fieldName,
        selector: data.selector,
        urlPath: data.urlPath,
        lastVerifiedAt: new Date(),
        aiGenerated: false
      })
    }

    revalidatePath('/admin/scraper-builder')
    return { success: true }
  } catch (error) {
    console.error('Failed to save scraper config:', error)
    return { error: 'Internal server error' }
  }
}

export async function parseWithAI(fieldName: string, text: string) {
  try {
    const pythonCommand = `cd ../scraper && uv run python ai_parse.py "${fieldName}" "${text.replace(/"/g, '\\"')}"`
    const { stdout, stderr } = await execPromise(pythonCommand)
    
    if (!stdout && stderr) {
      return { error: stderr }
    }

    return { result: stdout.trim() }
  } catch (error) {
    console.error('AI parse error:', error)
    return { error: 'Failed to parse with AI' }
  }
}

export async function getUniversities() {
  return await db.query.universities.findMany()
}
