/**
 * Runtime configuration for the frontend.
 *
 * When served by Modal (same origin), leave VITE_API_URL blank — all
 * requests use relative paths.  When deployed separately (e.g. Aedify),
 * set VITE_API_URL to the Modal web endpoint like:
 *   https://zubairzafar480--estateagent-ai-web.modal.run
 */

const raw = import.meta.env.VITE_API_URL as string | undefined

/** HTTP base – no trailing slash */
export const API_BASE: string = raw ? raw.replace(/\/+$/, '') : ''

/** WebSocket base (wss:// or ws://) – no trailing slash */
export function wsBase(): string {
  if (raw) {
    const url = new URL(raw)
    const proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${url.host}`
  }
  // Same-origin fallback
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}`
}
