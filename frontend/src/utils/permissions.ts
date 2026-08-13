export const PERMISSION_ALL = '*'

export function hasPermission(
  user: { permission_codes?: string[] } | null | undefined,
  code: string
): boolean {
  const codes = user?.permission_codes
  if (!codes || codes.length === 0) return true // permissive until loaded / legacy
  if (codes.includes(PERMISSION_ALL)) return true
  return codes.includes(code)
}

export function hasAnyPermission(
  user: { permission_codes?: string[] } | null | undefined,
  ...codes: string[]
): boolean {
  return codes.some((c) => hasPermission(user, c))
}
