import { api } from './api'

export interface CatalogOption {
  value: string
  label: string
}

export interface InvoiceStatusOption extends CatalogOption {
  affects_stock?: boolean
  affects_receivable?: boolean
  allows_credit_note?: boolean
}

export interface PaymentStatusOption extends CatalogOption {
  counts_as_paid?: boolean
}

export interface DocumentTypeOption extends CatalogOption {
  name: string
  description?: string
  requires_receptor_rut: boolean
  is_ticket: boolean
  is_credit_note: boolean
  credit_note_type?: string | null
  pos_default?: boolean
  invoice_form?: boolean
}

export interface AppCatalog {
  currency: string
  country: string
  defaults: {
    invoice_status: string
    payment_status: string
    pos_invoice_status: string
    invoice_paid_status?: string
    invoice_open_status?: string
    pos_document_type: string
    invoice_document_type: string
  }
  invoice_statuses: InvoiceStatusOption[]
  fiscal_states: CatalogOption[]
  payment_statuses: PaymentStatusOption[]
  payment_methods: CatalogOption[]
  tenant_statuses: CatalogOption[]
  receipt_statuses: CatalogOption[]
  woocommerce_statuses: CatalogOption[]
  document_types: DocumentTypeOption[]
  invoice_form_document_types: DocumentTypeOption[]
}

let cached: AppCatalog | null = null
let inflight: Promise<AppCatalog> | null = null

export async function fetchCatalog(force = false): Promise<AppCatalog> {
  if (cached && !force) return cached
  if (!inflight) {
    inflight = api.get('/catalog/').then((res) => {
      cached = res.data as AppCatalog
      inflight = null
      return cached
    })
  }
  return inflight
}

export function lookupLabel(options: CatalogOption[] | undefined, code?: string | null): string {
  if (!code) return '—'
  return options?.find((o) => o.value === code)?.label || code
}

export function invoiceStatusLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.invoice_statuses, code)
}

export function fiscalStateLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.fiscal_states, code)
}

export function paymentStatusLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.payment_statuses, code)
}

export function tenantStatusLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.tenant_statuses, code)
}

export function receiptStatusLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.receipt_statuses, code)
}

export function wooStatusLabel(catalog: AppCatalog | null, code?: string | null): string {
  return lookupLabel(catalog?.woocommerce_statuses, code)
}

export function documentTypeFromCatalog(catalog: AppCatalog | null, code: string): DocumentTypeOption | undefined {
  return catalog?.document_types.find((d) => d.value === code)
}

export function creditNoteTypeFromCatalog(catalog: AppCatalog | null, documentType: string): string | null {
  return documentTypeFromCatalog(catalog, documentType)?.credit_note_type || null
}

export function documentTypeLabelFromCatalog(catalog: AppCatalog | null, code: string): string {
  return lookupLabel(catalog?.document_types, code)
}
