/**
 * Bridge between the OpenPlan3D iframe and the parent「我的所有」app.
 * Message types:
 *   parent → iframe: { type: 'wodesuoyou:openplan-load', project }
 *   iframe → parent: { type: 'wodesuoyou:openplan-ready' }
 *   iframe → parent: { type: 'wodesuoyou:openplan-save', project }
 */

import type { Project } from '$lib/models/types'

export const OPENPLAN_MSG = {
  ready: 'wodesuoyou:openplan-ready',
  load: 'wodesuoyou:openplan-load',
  save: 'wodesuoyou:openplan-save',
} as const

export function isEmbedMode(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return new URL(window.location.href).searchParams.get('embed') === '1'
  } catch {
    return false
  }
}

export function postToParent(type: string, extra: Record<string, unknown> = {}) {
  if (typeof window === 'undefined' || window.parent === window) return
  window.parent.postMessage({ type, ...extra }, '*')
}

export function normalizeProject(raw: unknown): Project | null {
  if (!raw || typeof raw !== 'object') return null
  const p = raw as Project
  if (!p.id || !Array.isArray(p.floors)) return null
  p.createdAt = new Date(p.createdAt)
  p.updatedAt = new Date(p.updatedAt)
  for (const floor of p.floors) {
    if (!floor.rooms) floor.rooms = []
    if (!floor.doors) floor.doors = []
    if (!floor.windows) floor.windows = []
    if (!floor.furniture) floor.furniture = []
    if (!floor.stairs) floor.stairs = []
    if (!floor.columns) floor.columns = []
    if (!floor.guides) floor.guides = []
    if (!floor.measurements) floor.measurements = []
    if (!floor.annotations) floor.annotations = []
    if (!floor.textAnnotations) floor.textAnnotations = []
    if (!floor.groups) floor.groups = []
    // Localize legacy English floor labels from earlier builds
    if (floor.name === 'Ground Floor') floor.name = '一层'
    else if (/^Floor (\d+)$/.test(floor.name)) {
      const n = Number(RegExp.$1)
      floor.name = n <= 0 ? '一层' : `${n + 1}层`
    } else if (floor.name === 'Basement') floor.name = '地下室'
  }
  return p
}

export function serializeProject(project: Project) {
  return JSON.parse(
    JSON.stringify({
      ...project,
      createdAt: project.createdAt instanceof Date ? project.createdAt.toISOString() : project.createdAt,
      updatedAt: project.updatedAt instanceof Date ? project.updatedAt.toISOString() : project.updatedAt,
    }),
  )
}
