export const DOCUMENT_TYPE_OPTIONS = [
  { value: '101', label: 'e-Ticket — consumidor final (101)' },
  { value: '111', label: 'e-Factura — empresa con RUT (111)' },
  { value: '102', label: 'Nota de crédito e-Ticket (102)' },
  { value: '112', label: 'Nota de crédito e-Factura (112)' },
  { value: '103', label: 'Nota de débito e-Ticket (103)' },
  { value: '113', label: 'Nota de débito e-Factura (113)' },
  { value: '201', label: 'e-Ticket contingencia (201)' },
  { value: '211', label: 'e-Factura contingencia (211)' },
] as const

const shortLabels: Record<string, string> = {
  '101': 'e-Ticket (101)',
  '111': 'e-Factura (111)',
  '102': 'NC e-Ticket (102)',
  '112': 'NC e-Factura (112)',
  '103': 'ND e-Ticket (103)',
  '113': 'ND e-Factura (113)',
  '201': 'e-Ticket cont. (201)',
  '211': 'e-Factura cont. (211)',
}

export function documentTypeLabel(code: string, short = true): string {
  if (short) return shortLabels[code] || code
  return DOCUMENT_TYPE_OPTIONS.find((o) => o.value === code)?.label || code
}

export const isTicketType = (docType: string) =>
  ['101', '102', '103', '201', '202', '203'].includes(docType)
