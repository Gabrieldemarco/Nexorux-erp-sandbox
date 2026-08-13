/** Etiquetas en español uruguayo. Los códigos internos (API) no se cambian. */

export const INVOICE_STATUS_OPTIONS = [
  { value: 'draft', label: 'Borrador' },
  { value: 'issued', label: 'Emitida' },
  { value: 'paid', label: 'Pagada' },
  { value: 'posted', label: 'Contabilizada' },
  { value: 'confirmed', label: 'Confirmada' },
  { value: 'cancelled', label: 'Anulada' },
] as const

export const FISCAL_STATE_OPTIONS = [
  { value: 'draft', label: 'Borrador' },
  { value: 'pending_sign', label: 'Pendiente de firma' },
  { value: 'pending_send', label: 'Pendiente de envío' },
  { value: 'sent', label: 'Enviada a DGI' },
  { value: 'accepted', label: 'Aceptada por DGI' },
  { value: 'rejected', label: 'Rechazada por DGI' },
  { value: 'cancelled', label: 'Anulada' },
] as const

export const PAYMENT_STATUS_OPTIONS = [
  { value: 'completed', label: 'Completado' },
  { value: 'pending', label: 'Pendiente' },
  { value: 'failed', label: 'Fallido' },
  { value: 'cancelled', label: 'Anulado' },
] as const

export const TENANT_STATUS_OPTIONS = [
  { value: 'active', label: 'Activo' },
  { value: 'inactive', label: 'Inactivo' },
  { value: 'suspended', label: 'Suspendido' },
] as const

export const RECEIPT_STATUS_OPTIONS = [
  { value: 'received', label: 'Recibida' },
  { value: 'draft', label: 'Borrador' },
  { value: 'cancelled', label: 'Anulada' },
] as const

const WOO_STATUS: Record<string, string> = {
  pending: 'Pendiente',
  processing: 'En proceso',
  on_hold: 'En espera',
  completed: 'Completado',
  cancelled: 'Anulado',
  canceled: 'Anulado',
  refunded: 'Reembolsado',
  failed: 'Fallido',
  trash: 'Papelera',
}

function lookup(
  options: readonly { value: string; label: string }[],
  code?: string | null
): string {
  if (!code) return '—'
  const found = options.find((o) => o.value === code)
  return found?.label || code
}

export function invoiceStatusLabel(code?: string | null): string {
  return lookup(INVOICE_STATUS_OPTIONS, code)
}

export function fiscalStateLabel(code?: string | null): string {
  return lookup(FISCAL_STATE_OPTIONS, code)
}

export function paymentStatusLabel(code?: string | null): string {
  return lookup(PAYMENT_STATUS_OPTIONS, code)
}

export function tenantStatusLabel(code?: string | null): string {
  return lookup(TENANT_STATUS_OPTIONS, code)
}

export function receiptStatusLabel(code?: string | null): string {
  return lookup(RECEIPT_STATUS_OPTIONS, code)
}

export function wooStatusLabel(code?: string | null): string {
  if (!code) return '—'
  return WOO_STATUS[code] || code
}
