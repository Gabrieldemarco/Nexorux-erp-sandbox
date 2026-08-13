import { describe, it, expect } from 'vitest'
import {
  DOCUMENT_TYPE_OPTIONS,
  documentTypeLabel,
  isTicketType,
} from '../utils/documentTypes'

describe('documentTypes', () => {
  it('exposes readable CFE options used by invoice forms', () => {
    const values = DOCUMENT_TYPE_OPTIONS.map((o) => o.value)
    expect(values).toEqual(expect.arrayContaining(['101', '111', '102', '112']))
    expect(DOCUMENT_TYPE_OPTIONS.find((o) => o.value === '111')?.label).toMatch(/e-Factura/i)
    expect(DOCUMENT_TYPE_OPTIONS.find((o) => o.value === '101')?.label).toMatch(/e-Ticket/i)
  })

  it('returns short labels by default', () => {
    expect(documentTypeLabel('111')).toBe('e-Factura (111)')
    expect(documentTypeLabel('101')).toBe('e-Ticket (101)')
    expect(documentTypeLabel('102')).toBe('NC e-Ticket (102)')
    expect(documentTypeLabel('112')).toBe('NC e-Factura (112)')
  })

  it('returns long labels when short=false', () => {
    expect(documentTypeLabel('111', false)).toBe('e-Factura — empresa con RUT (111)')
    expect(documentTypeLabel('101', false)).toBe('e-Ticket — consumidor final (101)')
  })

  it('falls back to raw code for unknown types', () => {
    expect(documentTypeLabel('999')).toBe('999')
    expect(documentTypeLabel('999', false)).toBe('999')
  })

  it('detects ticket document types', () => {
    expect(isTicketType('101')).toBe(true)
    expect(isTicketType('102')).toBe(true)
    expect(isTicketType('201')).toBe(true)
    expect(isTicketType('111')).toBe(false)
    expect(isTicketType('112')).toBe(false)
  })
})
