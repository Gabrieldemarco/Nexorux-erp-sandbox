/** Small POS helpers (sound, local prefs, held cart). */

const PREFS_KEY = 'nexorux.pos.prefs'
const HELD_KEY = 'nexorux.pos.held'
const RECENT_KEY = 'nexorux.pos.recent'

export type PosPrefs = {
  autoPrint: boolean
  sound: boolean
}

export type HeldCartPayload = {
  cart: unknown[]
  paymentMethod: string
  amountReceived: string
  series: string
  warehouseId: string
  branchId: string
  savedAt: string
}

export const defaultPosPrefs = (): PosPrefs => ({
  autoPrint: false,
  sound: true,
})

export const loadPosPrefs = (): PosPrefs => {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (!raw) return defaultPosPrefs()
    return { ...defaultPosPrefs(), ...JSON.parse(raw) }
  } catch {
    return defaultPosPrefs()
  }
}

export const savePosPrefs = (prefs: PosPrefs) => {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs))
}

export const loadHeldCart = (): HeldCartPayload | null => {
  try {
    const raw = localStorage.getItem(HELD_KEY)
    if (!raw) return null
    return JSON.parse(raw) as HeldCartPayload
  } catch {
    return null
  }
}

export const saveHeldCart = (payload: HeldCartPayload) => {
  localStorage.setItem(HELD_KEY, JSON.stringify(payload))
}

export const clearHeldCart = () => {
  localStorage.removeItem(HELD_KEY)
}

export const loadRecentProductIds = (): string[] => {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === 'string') : []
  } catch {
    return []
  }
}

export const pushRecentProductId = (productId: string, limit = 24) => {
  const prev = loadRecentProductIds().filter((id) => id !== productId)
  const next = [productId, ...prev].slice(0, limit)
  localStorage.setItem(RECENT_KEY, JSON.stringify(next))
  return next
}

/** Soft UI beep via Web Audio (no asset files). */
export const playPosTone = (kind: 'ok' | 'err' | 'cash' = 'ok') => {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!Ctx) return
    const ctx = new Ctx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    const now = ctx.currentTime
    if (kind === 'ok') {
      osc.frequency.value = 880
      gain.gain.setValueAtTime(0.0001, now)
      gain.gain.exponentialRampToValueAtTime(0.08, now + 0.01)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09)
      osc.start(now)
      osc.stop(now + 0.1)
    } else if (kind === 'cash') {
      osc.frequency.value = 660
      gain.gain.setValueAtTime(0.0001, now)
      gain.gain.exponentialRampToValueAtTime(0.1, now + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18)
      osc.start(now)
      osc.stop(now + 0.2)
    } else {
      osc.type = 'square'
      osc.frequency.value = 220
      gain.gain.setValueAtTime(0.0001, now)
      gain.gain.exponentialRampToValueAtTime(0.07, now + 0.01)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22)
      osc.start(now)
      osc.stop(now + 0.25)
    }
    window.setTimeout(() => void ctx.close(), 400)
  } catch {
    // ignore autoplay / unsupported
  }
}
