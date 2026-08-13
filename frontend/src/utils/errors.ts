export function getErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => (typeof item === 'object' && item && 'msg' in item ? String(item.msg) : JSON.stringify(item))).join(', ')
  }
  return fallback
}
