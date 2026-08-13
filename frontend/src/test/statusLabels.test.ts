import { describe, expect, it } from 'vitest'
import {
  invoiceStatusLabel,
  fiscalStateLabel,
  paymentStatusLabel,
  tenantStatusLabel,
  wooStatusLabel,
} from '../utils/statusLabels'

describe('statusLabels', () => {
  it('traduce estados de factura', () => {
    expect(invoiceStatusLabel('draft')).toBe('Borrador')
    expect(invoiceStatusLabel('paid')).toBe('Pagada')
    expect(invoiceStatusLabel('cancelled')).toBe('Anulada')
  })

  it('traduce estados fiscales DGI', () => {
    expect(fiscalStateLabel('accepted')).toBe('Aceptada por DGI')
    expect(fiscalStateLabel('pending_send')).toBe('Pendiente de envío')
  })

  it('traduce pagos, tenants y Woo', () => {
    expect(paymentStatusLabel('completed')).toBe('Completado')
    expect(tenantStatusLabel('active')).toBe('Activo')
    expect(wooStatusLabel('processing')).toBe('En proceso')
  })

  it('no inventa etiquetas para códigos desconocidos', () => {
    expect(invoiceStatusLabel('otro')).toBe('otro')
    expect(invoiceStatusLabel('')).toBe('—')
  })
})
