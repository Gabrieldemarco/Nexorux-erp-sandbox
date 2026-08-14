import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import { invoicesApi, InvoiceCreate, InvoiceResponse, InvoiceUpdate } from '../services/invoices'
import { invoiceItemsApi } from '../services/invoiceItems'
import { customersApi, CustomerResponse } from '../services/customers'
import { productsApi, ProductResponse } from '../services/products'
import { branchesApi, BranchResponse } from '../services/branches'
import { warehousesApi, WarehouseResponse } from '../services/warehouses'
import { certificatesApi, CertificateResponse } from '../services/certificates'
import { fiscalDocumentsApi } from '../services/fiscalDocuments'
import { getErrorMessage } from '../utils/errors'
import { DOCUMENT_TYPE_OPTIONS, documentTypeLabel, isTicketType } from '../utils/documentTypes'
import { INVOICE_STATUS_OPTIONS, invoiceStatusLabel as fallbackInvoiceStatusLabel } from '../utils/statusLabels'
import { useCatalog } from '../hooks/useCatalog'
import {
  creditNoteTypeFromCatalog,
  documentTypeLabelFromCatalog,
  invoiceStatusLabel as catalogInvoiceStatusLabel,
} from '../services/catalog'

const nextNumberForSeries = (invoices: InvoiceResponse[], series: string): string => {
  const nums = invoices
    .filter((inv) => inv.series === series)
    .map((inv) => parseInt(inv.number, 10))
    .filter((n) => !Number.isNaN(n))
  const next = nums.length ? Math.max(...nums) + 1 : 1
  return String(next).padStart(8, '0')
}

const hasValidRut = (customer?: CustomerResponse | null) => {
  if (!customer?.rut) return false
  const rut = customer.rut.trim()
  return rut.length > 0 && rut !== '00000000' && !/^0+$/.test(rut)
}

const isCompanyLikeCustomer = (customer?: CustomerResponse | null) => {
  if (!customer) return false
  if (customer.customer_type === 'final_consumer') return false
  return hasValidRut(customer) || customer.customer_type === 'company'
}

const normalizeCode = (value: string) => value.trim().toLowerCase()

const productLabel = (p: ProductResponse) => {
  const codes = [p.sku, p.barcode].filter(Boolean).join(' · ')
  return codes ? `${p.name} (${codes}) — $${p.sales_price}` : `${p.name} — $${p.sales_price}`
}

const matchProduct = (products: ProductResponse[], rawQuery: string): ProductResponse | null => {
  const query = normalizeCode(rawQuery)
  if (!query) return null

  const exactBarcode = products.find((p) => p.barcode && normalizeCode(p.barcode) === query)
  if (exactBarcode) return exactBarcode

  const exactSku = products.find((p) => normalizeCode(p.sku) === query)
  if (exactSku) return exactSku

  const nameExact = products.find((p) => normalizeCode(p.name) === query)
  if (nameExact) return nameExact

  const partial = products.filter(
    (p) =>
      normalizeCode(p.name).includes(query) ||
      normalizeCode(p.sku).includes(query) ||
      (p.barcode ? normalizeCode(p.barcode).includes(query) : false) ||
      (p.description ? normalizeCode(p.description).includes(query) : false)
  )
  return partial.length === 1 ? partial[0] : null
}

const suggestProducts = (products: ProductResponse[], rawQuery: string, limit = 8): ProductResponse[] => {
  const query = normalizeCode(rawQuery)
  if (!query || query.length < 1) return []
  return products
    .filter(
      (p) =>
        normalizeCode(p.name).includes(query) ||
        normalizeCode(p.sku).includes(query) ||
        (p.barcode ? normalizeCode(p.barcode).includes(query) : false) ||
        (p.description ? normalizeCode(p.description).includes(query) : false)
    )
    .slice(0, limit)
}

const today = () => new Date().toISOString().slice(0, 10)
const dueIn30 = () => {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
}

const toIsoDate = (date: string) => `${date}T00:00:00`
const money = (n: number) => Number((n || 0).toFixed(2))
const newRowKey = () => `row-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  const d = value.slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return value
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

type InvoiceSortKey = 'number' | 'document_type' | 'issue_date' | 'due_date' | 'total' | 'status'

const compareInvoices = (a: InvoiceResponse, b: InvoiceResponse, key: InvoiceSortKey) => {
  if (key === 'number') {
    const seriesCmp = (a.series || '').localeCompare(b.series || '', undefined, { sensitivity: 'base' })
    if (seriesCmp !== 0) return seriesCmp
    const na = parseInt(a.number, 10)
    const nb = parseInt(b.number, 10)
    if (!Number.isNaN(na) && !Number.isNaN(nb) && na !== nb) return na - nb
    return (a.number || '').localeCompare(b.number || '', undefined, { numeric: true })
  }
  if (key === 'total') return Number(a.total || 0) - Number(b.total || 0)
  if (key === 'issue_date' || key === 'due_date') {
    return (a[key] || '').localeCompare(b[key] || '')
  }
  return String(a[key] || '').localeCompare(String(b[key] || ''), undefined, { sensitivity: 'base' })
}

type LineRow = {
  key: string
  id?: string
  product_id: string
  description: string
  quantity: number
  unit_price: number
  tax_rate: number
  discount: number
}

const emptyRow = (): LineRow => ({
  key: newRowKey(),
  product_id: '',
  description: '',
  quantity: 1,
  unit_price: 0,
  tax_rate: 22,
  discount: 0,
})

const rowAmounts = (row: LineRow) => {
  const qty = Math.max(Number(row.quantity) || 0, 0)
  const price = Math.max(Number(row.unit_price) || 0, 0)
  const discount = Math.max(Number(row.discount) || 0, 0)
  const net = Math.max(qty * price - discount, 0)
  const tax = money((net * (Number(row.tax_rate) || 0)) / 100)
  const total = money(net + tax)
  return { net: money(net), tax, total }
}

const defaultForm = {
  document_type: '',
  series: 'A',
  number: '',
  status: 'draft',
  issue_date: today(),
  due_date: dueIn30(),
  customer_id: '',
  branch_id: '',
  warehouse_id: '',
  currency: '',
  exchange_rate: 1,
  notes: '',
}

const Invoices = () => {
  const { user } = useAuth()
  const { catalog, currency: companyCurrency } = useCatalog()
  const statusOptions = catalog?.invoice_statuses?.length
    ? catalog.invoice_statuses
    : [...INVOICE_STATUS_OPTIONS]
  const documentTypes = catalog?.invoice_form_document_types?.length
    ? catalog.invoice_form_document_types
    : DOCUMENT_TYPE_OPTIONS.filter((opt) => ['101', '111', '102', '112'].includes(opt.value))
  const typeLabel = useCallback((code: string) =>
    catalog ? documentTypeLabelFromCatalog(catalog, code) : documentTypeLabel(code),
    [catalog]
  )
  const statusLabel = useCallback((code?: string | null) =>
    catalog ? catalogInvoiceStatusLabel(catalog, code) : fallbackInvoiceStatusLabel(code),
    [catalog]
  )

  const crud = useEntityCrud<InvoiceResponse, InvoiceCreate, InvoiceUpdate>(
    invoicesApi,
    'No se pudieron cargar las facturas',
    '¿Eliminar esta factura?'
  )
  const [form, setForm] = useState(defaultForm)
  const [lines, setLines] = useState<LineRow[]>([emptyRow()])
  const [customers, setCustomers] = useState<CustomerResponse[]>([])
  const [products, setProducts] = useState<ProductResponse[]>([])
  const [branches, setBranches] = useState<BranchResponse[]>([])
  const [warehouses, setWarehouses] = useState<WarehouseResponse[]>([])
  const [refsLoading, setRefsLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [scanQuery, setScanQuery] = useState('')
  const [scanMessage, setScanMessage] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [formWarning, setFormWarning] = useState<string | null>(null)
  const [emitOpen, setEmitOpen] = useState(false)
  const [emitInvoice, setEmitInvoice] = useState<InvoiceResponse | null>(null)
  const [emitCertificateId, setEmitCertificateId] = useState('')
  const [certificates, setCertificates] = useState<CertificateResponse[]>([])
  const [emitError, setEmitError] = useState<string | null>(null)
  const [emitSaving, setEmitSaving] = useState(false)
  const [creditBusyId, setCreditBusyId] = useState<string | null>(null)
  const [listMessage, setListMessage] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<InvoiceSortKey>('issue_date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDocType, setFilterDocType] = useState('')
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const scanInputRef = useRef<HTMLInputElement>(null)

  const ticketMode = catalog
    ? Boolean(catalog.document_types.find((d) => d.value === form.document_type)?.is_ticket)
    : isTicketType(form.document_type)
  const scanSuggestions = useMemo(() => suggestProducts(products, scanQuery), [products, scanQuery])

  const filteredInvoices = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return crud.items.filter((inv) => {
      if (filterStatus && inv.status !== filterStatus) return false
      if (filterDocType && inv.document_type !== filterDocType) return false
      const issue = (inv.issue_date || '').slice(0, 10)
      if (filterDateFrom && issue < filterDateFrom) return false
      if (filterDateTo && issue > filterDateTo) return false
      if (!q) return true
      const haystack = [
        inv.series,
        inv.number,
        `${inv.series}-${inv.number}`,
        inv.status,
        statusLabel(inv.status),
        inv.document_type,
        typeLabel(inv.document_type),
        inv.notes || '',
        inv.currency || '',
        String(inv.total ?? ''),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [crud.items, searchQuery, filterStatus, filterDocType, filterDateFrom, filterDateTo, statusLabel, typeLabel])

  const sortedInvoices = useMemo(() => {
    const items = [...filteredInvoices]
    items.sort((a, b) => {
      const cmp = compareInvoices(a, b, sortKey)
      return sortDir === 'asc' ? cmp : -cmp
    })
    return items
  }, [filteredInvoices, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(sortedInvoices.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const pagedInvoices = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return sortedInvoices.slice(start, start + pageSize)
  }, [sortedInvoices, currentPage, pageSize])

  useEffect(() => {
    setPage(1)
  }, [searchQuery, filterStatus, filterDocType, filterDateFrom, filterDateTo, pageSize])

  const toggleSort = (key: InvoiceSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortKey(key)
    setSortDir(key === 'issue_date' || key === 'due_date' || key === 'total' ? 'desc' : 'asc')
  }

  const sortIndicator = (key: InvoiceSortKey) => {
    if (sortKey !== key) return ''
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  const clearFilters = () => {
    setSearchQuery('')
    setFilterStatus('')
    setFilterDocType('')
    setFilterDateFrom('')
    setFilterDateTo('')
    setPage(1)
  }

  const totals = useMemo(() => {
    return lines.reduce(
      (acc, row) => {
        const amounts = rowAmounts(row)
        acc.subtotal = money(acc.subtotal + amounts.net)
        acc.tax_total = money(acc.tax_total + amounts.tax)
        acc.discount_total = money(acc.discount_total + (Number(row.discount) || 0))
        acc.total = money(acc.total + amounts.total)
        return acc
      },
      { subtotal: 0, tax_total: 0, discount_total: 0, total: 0 }
    )
  }, [lines])

  useEffect(() => {
    if (!crud.modalOpen) return
    const loadRefs = async () => {
      setRefsLoading(true)
      setModalError(null)
      try {
        const [c, p, b, w] = await Promise.all([
          customersApi.list(),
          productsApi.list(),
          branchesApi.list(),
          warehousesApi.list(),
        ])
        setCustomers(c)
        setProducts(p)
        setBranches(b)
        setWarehouses(w)

        if (crud.editing) {
          const existingItems = await invoiceItemsApi.list(crud.editing.id)
          const mapped = existingItems.map((item) => {
            const product = p.find((prod) => prod.id === item.product_id)
            const net = Math.max(Number(item.quantity) * Number(item.unit_price) - Number(item.discount || 0), 0)
            const taxRate = net > 0 ? money((Number(item.tax_amount) / net) * 100) : product?.tax_rate ?? 22
            return {
              key: newRowKey(),
              id: item.id,
              product_id: item.product_id || '',
              description: item.description || product?.name || '',
              quantity: Number(item.quantity),
              unit_price: Number(item.unit_price),
              tax_rate: taxRate,
              discount: Number(item.discount || 0),
            } as LineRow
          })
          setLines(mapped.length ? mapped : [])
        } else {
          setLines([])
          setScanQuery('')
          setScanMessage(null)
        }
      } catch (err) {
        setModalError(getErrorMessage(err, 'No se pudieron cargar productos/clientes'))
      } finally {
        setRefsLoading(false)
      }
    }
    loadRefs()
  }, [crud.modalOpen, crud.editing])

  useEffect(() => {
    if (!crud.modalOpen || refsLoading) return
    const timer = window.setTimeout(() => scanInputRef.current?.focus(), 50)
    return () => window.clearTimeout(timer)
  }, [crud.modalOpen, refsLoading])

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        document_type: crud.editing.document_type,
        series: crud.editing.series,
        number: crud.editing.number,
        status: crud.editing.status,
        issue_date: crud.editing.issue_date.slice(0, 10),
        due_date: crud.editing.due_date.slice(0, 10),
        customer_id: crud.editing.customer_id ?? '',
        branch_id: crud.editing.branch_id ?? '',
        warehouse_id: crud.editing.warehouse_id ?? '',
        currency: crud.editing.currency,
        exchange_rate: crud.editing.exchange_rate,
        notes: crud.editing.notes ?? '',
      })
    } else {
      setForm({
        ...defaultForm,
        document_type: catalog?.defaults.invoice_document_type || documentTypes[0]?.value || '',
        status: catalog?.defaults.invoice_status || 'draft',
        currency: companyCurrency,
        issue_date: today(),
        due_date: dueIn30(),
      })
    }
  }, [crud.modalOpen, crud.editing, catalog, companyCurrency, documentTypes])

  useEffect(() => {
    if (!crud.modalOpen || crud.editing || refsLoading) return

    const finalConsumer =
      customers.find((c) => c.customer_type === 'final_consumer') ||
      customers.find((c) => /consumidor final/i.test(c.legal_name))
    const companyCustomer = customers.find((c) => c.customer_type === 'company') || customers[0]
    const preferredCustomer = ticketMode ? finalConsumer || customers[0] : companyCustomer
    const suggestedNumber = nextNumberForSeries(crud.items, form.series || defaultForm.series)

    setForm((prev) => ({
      ...prev,
      customer_id: prev.customer_id || preferredCustomer?.id || '',
      branch_id: prev.branch_id || branches[0]?.id || '',
      warehouse_id: prev.warehouse_id || warehouses[0]?.id || '',
      number: prev.number || suggestedNumber,
    }))
  }, [crud.modalOpen, crud.editing, refsLoading, customers, branches, warehouses, ticketMode, crud.items, form.series])

  const handleDocumentTypeChange = (document_type: string) => {
    const nextTicket = catalog
      ? Boolean(catalog.document_types.find((d) => d.value === document_type)?.is_ticket)
      : isTicketType(document_type)
    const finalConsumer =
      customers.find((c) => c.customer_type === 'final_consumer') ||
      customers.find((c) => /consumidor final/i.test(c.legal_name))
    const companyCustomer = customers.find((c) => c.customer_type === 'company') || customers[0]
    setForm((prev) => ({
      ...prev,
      document_type,
      customer_id: nextTicket ? finalConsumer?.id || prev.customer_id : companyCustomer?.id || prev.customer_id,
    }))
  }

  const handleSeriesChange = (series: string) => {
    setForm((prev) => {
      if (crud.editing) return { ...prev, series }
      return { ...prev, series, number: nextNumberForSeries(crud.items, series) }
    })
  }

  const openEmitFiscal = async (invoice: InvoiceResponse) => {
    setEmitInvoice(invoice)
    setEmitError(null)
    setEmitCertificateId('')
    setEmitOpen(true)
    try {
      const certs = await certificatesApi.list()
      const active = certs.filter((c) => c.is_active)
      setCertificates(active)
      if (active[0]) setEmitCertificateId(active[0].id)
    } catch (err) {
      setEmitError(getErrorMessage(err, 'No se pudieron cargar los certificados'))
    }
  }

  const closeEmitFiscal = () => {
    setEmitOpen(false)
    setEmitInvoice(null)
    setEmitError(null)
  }

  const canCreateCreditNote = (invoice: InvoiceResponse) => {
    const nc = creditNoteTypeFromCatalog(catalog, invoice.document_type)
    if (!nc) return false
    const status = statusOptions.find((s) => s.value === invoice.status) as
      | { allows_credit_note?: boolean }
      | undefined
    return status?.allows_credit_note !== false
  }

  const creditNoteType = (documentType: string) => creditNoteTypeFromCatalog(catalog, documentType)

  const handleCreateCreditNote = async (parent: InvoiceResponse) => {
    if (!user) return
    const ncType = creditNoteType(parent.document_type)
    if (!ncType) return
    if (
      !window.confirm(
        `¿Crear nota de crédito (${ncType}) para ${parent.series}-${parent.number}? Se creará un borrador con las mismas líneas.`
      )
    ) {
      return
    }

    setCreditBusyId(parent.id)
    setListMessage(null)
    try {
      if (!parent.customer_id || !parent.branch_id || !parent.warehouse_id) {
        throw new Error('La factura origen no tiene cliente/sucursal/depósito')
      }
      const number = nextNumberForSeries(crud.items, parent.series)
      const created = await invoicesApi.create({
        tenant_id: user.tenant_id,
        company_id: parent.company_id || user.company_id,
        customer_id: parent.customer_id,
        branch_id: parent.branch_id,
        warehouse_id: parent.warehouse_id,
        document_type: ncType,
        series: parent.series,
        number,
        status: 'draft',
        issue_date: toIsoDate(today()),
        due_date: toIsoDate(dueIn30()),
        subtotal: Number(parent.subtotal) || 0,
        tax_total: Number(parent.tax_total) || 0,
        discount_total: Number(parent.discount_total) || 0,
        total: Number(parent.total) || 0,
        currency: parent.currency || companyCurrency,
        exchange_rate: parent.exchange_rate ?? 1,
        notes: parent.notes || undefined,
        metadata: {
          parent_invoice_id: parent.id,
          reference_reason: 'Anulación / nota de crédito',
        },
      })

      let items = await invoiceItemsApi.list(parent.id)
      items = items.filter((item) => item.invoice_id === parent.id)
      for (const item of items) {
        await invoiceItemsApi.create({
          tenant_id: user.tenant_id,
          company_id: created.company_id || user.company_id,
          invoice_id: created.id,
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          discount: item.discount,
          tax_amount: item.tax_amount,
          total: item.total,
          description: item.description,
        })
      }

      await crud.reload()
      setListMessage(`Nota de crédito ${created.series}-${created.number} creada.`)
      crud.openEdit(created)
    } catch (err) {
      setListMessage(getErrorMessage(err, 'No se pudo crear la nota de crédito'))
    } finally {
      setCreditBusyId(null)
    }
  }

  const handleEmitFiscal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user || !emitInvoice || !emitCertificateId) return
    setEmitSaving(true)
    setEmitError(null)
    try {
      const fiscalDoc = await fiscalDocumentsApi.create({
        tenant_id: user.tenant_id,
        company_id: emitInvoice.company_id || user.company_id,
        invoice_id: emitInvoice.id,
        document_type: emitInvoice.document_type,
        series: emitInvoice.series,
        number: emitInvoice.number,
        state: 'draft',
      })
      await fiscalDocumentsApi.issue(fiscalDoc.id, { certificate_id: emitCertificateId })
      closeEmitFiscal()
    } catch (err) {
      setEmitError(getErrorMessage(err, 'No se pudo emitir el documento fiscal'))
    } finally {
      setEmitSaving(false)
    }
  }

  const updateLine = (key: string, patch: Partial<LineRow>) => {
    setLines((prev) => prev.map((row) => (row.key === key ? { ...row, ...patch } : row)))
  }

  const handleProductPick = (key: string, productId: string) => {
    const product = products.find((p) => p.id === productId)
    updateLine(key, {
      product_id: productId,
      description: product?.name || '',
      unit_price: product?.sales_price ?? 0,
      tax_rate: product?.tax_rate ?? 22,
    })
  }

  const addOrIncrementProduct = (product: ProductResponse) => {
    setLines((prev) => {
      const existing = prev.find((row) => row.product_id === product.id)
      if (existing) {
        return prev.map((row) =>
          row.key === existing.key ? { ...row, quantity: Number(row.quantity) + 1 } : row
        )
      }
      return [
        ...prev,
        {
          key: newRowKey(),
          product_id: product.id,
          description: product.name,
          quantity: 1,
          unit_price: Number(product.sales_price),
          tax_rate: Number(product.tax_rate),
          discount: 0,
        },
      ]
    })
    setScanMessage(`+ ${product.name}`)
    setScanQuery('')
    setShowSuggestions(false)
    scanInputRef.current?.focus()
  }

  const handleScanSubmit = () => {
    const query = scanQuery.trim()
    if (!query) return
    const product = matchProduct(products, query)
    if (!product) {
      setScanMessage(`No se encontró: ${query}`)
      setShowSuggestions(true)
      return
    }
    addOrIncrementProduct(product)
  }

  const addLine = () => setLines((prev) => [...prev, emptyRow()])

  const removeLine = (key: string) => {
    setLines((prev) => prev.filter((row) => row.key !== key))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const validLines = lines.filter((row) => row.product_id && row.quantity > 0)
    if (!validLines.length) {
      setModalError('Agregá al menos un producto en la tabla')
      return
    }

    if (!form.customer_id) {
      setModalError('Seleccioná un cliente')
      return
    }

    const customer = customers.find((c) => c.id === form.customer_id)
    const docMeta = catalog?.document_types.find((d) => d.value === form.document_type)
    setFormWarning(null)

    if (docMeta?.requires_receptor_rut) {
      if (!isCompanyLikeCustomer(customer)) {
        setModalError(
          `Para ${docMeta.label} el cliente no puede ser consumidor final; se requiere RUT válido.`
        )
        return
      }
    }

    if (docMeta?.is_ticket) {
      if (customer && customer.customer_type !== 'final_consumer') {
        setFormWarning(`Advertencia: ${docMeta.name} suele usarse con consumidor final.`)
      }
    }

    setSaving(true)
    setModalError(null)
    try {
      const base = {
        document_type: form.document_type,
        series: form.series,
        number: form.number,
        status: form.status,
        issue_date: toIsoDate(form.issue_date),
        due_date: toIsoDate(form.due_date),
        subtotal: totals.subtotal,
        tax_total: totals.tax_total,
        discount_total: totals.discount_total,
        total: totals.total,
        currency: form.currency,
        exchange_rate: form.exchange_rate,
        notes: form.notes || undefined,
      }

      let invoiceId = crud.editing?.id
      if (crud.editing) {
        await invoicesApi.update(crud.editing.id, {
          ...base,
          customer_id: form.customer_id || undefined,
          branch_id: form.branch_id || undefined,
          warehouse_id: form.warehouse_id || undefined,
        })
      } else {
        const created = await invoicesApi.create({
          ...base,
          tenant_id: user.tenant_id,
          company_id: user.company_id,
          customer_id: form.customer_id,
          branch_id: form.branch_id,
          warehouse_id: form.warehouse_id,
        })
        invoiceId = created.id
      }

      if (!invoiceId) throw new Error('No se pudo guardar la factura')

      const existing = crud.editing ? await invoiceItemsApi.list(invoiceId) : []
      const keepIds = new Set(validLines.filter((row) => row.id).map((row) => row.id as string))

      await Promise.all(
        existing.filter((item) => !keepIds.has(item.id)).map((item) => invoiceItemsApi.delete(item.id))
      )

      await Promise.all(
        validLines.map(async (row) => {
          const amounts = rowAmounts(row)
          const payload = {
            product_id: row.product_id,
            quantity: row.quantity,
            unit_price: row.unit_price,
            discount: row.discount || 0,
            tax_amount: amounts.tax,
            total: amounts.total,
            description: row.description || undefined,
          }
          if (row.id) {
            await invoiceItemsApi.update(row.id, payload)
          } else {
            await invoiceItemsApi.create({
              ...payload,
              tenant_id: user.tenant_id,
              company_id: user.company_id,
              invoice_id: invoiceId!,
            })
          }
        })
      )

      crud.closeModal()
      await crud.reload()
    } catch (err) {
      setModalError(getErrorMessage(err, 'Error al guardar la factura'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Facturas</h2>
          <p className="mt-1 text-sm text-gray-500">Hacé click en un registro para abrir el formulario completo (cabecera + líneas).</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/pos"
            className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700"
          >
            Caja rápida
          </Link>
          <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
            Agregar factura
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        {listMessage && <div className="p-4 text-sm text-emerald-700 bg-emerald-50">{listMessage}</div>}

        <div className="px-4 py-3 border-b border-gray-200 grid grid-cols-1 md:grid-cols-6 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Buscar</label>
            <input
              className={inputClass}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Número, tipo, estado, notas..."
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
            <select className={inputClass} value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
              <option value="">Todos</option>
              {statusOptions.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Tipo</label>
            <select className={inputClass} value={filterDocType} onChange={(e) => setFilterDocType(e.target.value)}>
              <option value="">Todos</option>
              {catalog?.document_types?.length
                ? catalog.document_types.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))
                : DOCUMENT_TYPE_OPTIONS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Desde</label>
            <input
              className={inputClass}
              type="date"
              value={filterDateFrom}
              onChange={(e) => setFilterDateFrom(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Hasta</label>
            <input
              className={inputClass}
              type="date"
              value={filterDateTo}
              onChange={(e) => setFilterDateTo(e.target.value)}
            />
          </div>
        </div>
        <div className="px-4 py-2 border-b border-gray-100 flex flex-wrap items-center justify-between gap-2 text-sm text-gray-600">
          <span>
            {sortedInvoices.length} resultado{sortedInvoices.length === 1 ? '' : 's'}
            {sortedInvoices.length !== crud.items.length ? ` (de ${crud.items.length})` : ''}
          </span>
          <div className="flex items-center gap-3">
            <button type="button" onClick={clearFilters} className="text-blue-600 hover:underline">
              Limpiar filtros
            </button>
            <label className="flex items-center gap-1">
              Por página
              <select
                className={`${inputClass} w-20 py-1`}
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
              >
                {[10, 25, 50, 100].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {(
                [
                  { key: 'number' as const, label: 'Número' },
                  { key: 'document_type' as const, label: 'Tipo' },
                  { key: 'issue_date' as const, label: 'Emisión' },
                  { key: 'due_date' as const, label: 'Vencimiento' },
                  { key: 'total' as const, label: 'Total' },
                  { key: 'status' as const, label: 'Estado' },
                ] as const
              ).map((col) => (
                <th key={col.key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    type="button"
                    onClick={() => toggleSort(col.key)}
                    className="inline-flex items-center gap-0.5 hover:text-gray-800 focus:outline-none"
                    title={`Ordenar por ${col.label.toLowerCase()}`}
                  >
                    {col.label}
                    <span className="text-gray-400 normal-case tracking-normal">{sortIndicator(col.key)}</span>
                  </button>
                </th>
              ))}
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {pagedInvoices.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                  {crud.items.length === 0
                    ? 'No hay facturas cargadas. Creá la primera para empezar.'
                    : 'Ninguna factura coincide con los filtros.'}
                </td>
              </tr>
            ) : (
              pagedInvoices.map((invoice) => (
                <EntityListRow
                  key={invoice.id}
                  onOpen={() => crud.openEdit(invoice)}
                  actions={
                    <>
                      <button
                        type="button"
                        onClick={() => openEmitFiscal(invoice)}
                        className="text-emerald-600 hover:text-emerald-900 mr-4"
                      >
                        Emitir fiscal
                      </button>
                      {canCreateCreditNote(invoice) && (
                        <button
                          type="button"
                          onClick={() => handleCreateCreditNote(invoice)}
                          disabled={creditBusyId === invoice.id}
                          className="text-amber-700 hover:text-amber-900 mr-4 disabled:opacity-50"
                        >
                          {creditBusyId === invoice.id ? 'Creando NC...' : 'Nota de crédito'}
                        </button>
                      )}
                      <button type="button" onClick={() => crud.openEdit(invoice)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(invoice.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {invoice.series}-{invoice.number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {typeLabel(invoice.document_type)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(invoice.issue_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(invoice.due_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {invoice.total} {invoice.currency}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {statusLabel(invoice.status)}
                  </td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>

        <div className="px-4 py-3 border-t border-gray-200 flex flex-wrap items-center justify-between gap-2 text-sm text-gray-600">
          <span>
            Página {currentPage} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="px-3 py-1 rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      </div>

      <Modal
        open={crud.modalOpen}
        title={
          crud.editing
            ? `Factura · ${crud.editing.series}-${crud.editing.number}`
            : 'Agregar factura'
        }
        onClose={crud.closeModal}
        size="xl"
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="invoice-form"
              disabled={saving || refsLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {(modalError || crud.modalError) && (
          <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{modalError || crud.modalError}</div>
        )}
        {formWarning && (
          <div className="mb-4 rounded-md bg-amber-50 p-3 text-amber-800 text-sm">{formWarning}</div>
        )}
        {refsLoading ? (
          <div className="text-gray-500">Cargando referencias...</div>
        ) : (
          <form id="invoice-form" onSubmit={handleSubmit} className="space-y-4">
            {ticketMode && (
              <div className="rounded-md bg-sky-50 p-3 text-sm text-sky-900">
                e-Ticket: venta a consumidor final. Escaneá códigos o buscá por nombre/SKU abajo.
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <FormField label="Tipo documento">
                <select className={inputClass} value={form.document_type} onChange={(e) => handleDocumentTypeChange(e.target.value)}>
                  {documentTypes.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Cliente">
                <select className={inputClass} required value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}>
                  <option value="">Seleccionar cliente</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.legal_name}
                      {c.customer_type === 'final_consumer' ? ' (final)' : ''}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <FormField label="Serie">
                <input className={inputClass} required value={form.series} onChange={(e) => handleSeriesChange(e.target.value)} />
              </FormField>
              <FormField label="Número">
                <input className={inputClass} required value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
              </FormField>
              <FormField label="Estado">
                <select className={inputClass} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  {statusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Moneda">
                <input className={inputClass} required value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
              </FormField>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <h4 className="text-sm font-semibold text-gray-800">Detalle de productos</h4>
                <button type="button" onClick={addLine} className="text-sm text-blue-600 hover:text-blue-800">
                  + Fila manual
                </button>
              </div>

              <div className="relative mb-3">
                <label className="mb-1 block text-xs font-medium text-gray-600">
                  Código de barras / SKU / nombre
                </label>
                <div className="flex gap-2">
                  <input
                    ref={scanInputRef}
                    className={inputClass}
                    value={scanQuery}
                    placeholder="Escaneá o escribí y Enter…"
                    autoComplete="off"
                    onChange={(e) => {
                      setScanQuery(e.target.value)
                      setScanMessage(null)
                      setShowSuggestions(true)
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => window.setTimeout(() => setShowSuggestions(false), 150)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleScanSubmit()
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleScanSubmit}
                    className="shrink-0 rounded-md bg-slate-800 px-3 py-2 text-sm text-white hover:bg-slate-900"
                  >
                    Agregar
                  </button>
                </div>
                {showSuggestions && scanSuggestions.length > 0 && (
                  <ul className="absolute z-20 mt-1 max-h-56 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg">
                    {scanSuggestions.map((p) => (
                      <li key={p.id}>
                        <button
                          type="button"
                          className="block w-full px-3 py-2 text-left text-sm hover:bg-sky-50"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => addOrIncrementProduct(p)}
                        >
                          <span className="font-medium text-gray-900">{p.name}</span>
                          <span className="ml-2 text-xs text-gray-500">
                            {[p.sku, p.barcode].filter(Boolean).join(' · ')} · ${Number(p.sales_price).toFixed(2)}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {scanMessage && (
                  <p className={`mt-1 text-xs ${scanMessage.startsWith('+') ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {scanMessage}
                  </p>
                )}
              </div>

              <div className="overflow-x-auto rounded-md border border-gray-200">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-2 py-2">Producto</th>
                      <th className="px-2 py-2">Cant.</th>
                      <th className="px-2 py-2">Precio</th>
                      <th className="px-2 py-2">Desc.</th>
                      <th className="px-2 py-2">IVA %</th>
                      <th className="px-2 py-2">Total</th>
                      <th className="px-2 py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-3 py-6 text-center text-gray-500">
                          Escaneá un código o buscá por nombre/SKU para cargar productos.
                        </td>
                      </tr>
                    ) : (
                      lines.map((row) => {
                        const amounts = rowAmounts(row)
                        return (
                          <tr key={row.key} className="border-t border-gray-100">
                            <td className="px-2 py-2 min-w-[240px]">
                              <select
                                className={inputClass}
                                value={row.product_id}
                                onChange={(e) => handleProductPick(row.key, e.target.value)}
                              >
                                <option value="">Elegir producto</option>
                                {products.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    {productLabel(p)}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td className="px-2 py-2 w-24">
                              <input
                                className={inputClass}
                                type="number"
                                min={0}
                                step="0.01"
                                value={row.quantity}
                                onChange={(e) => updateLine(row.key, { quantity: Number(e.target.value) })}
                              />
                            </td>
                            <td className="px-2 py-2 w-28">
                              <input
                                className={inputClass}
                                type="number"
                                min={0}
                                step="0.01"
                                value={row.unit_price}
                                onChange={(e) => updateLine(row.key, { unit_price: Number(e.target.value) })}
                              />
                            </td>
                            <td className="px-2 py-2 w-24">
                              <input
                                className={inputClass}
                                type="number"
                                min={0}
                                step="0.01"
                                value={row.discount}
                                onChange={(e) => updateLine(row.key, { discount: Number(e.target.value) })}
                              />
                            </td>
                            <td className="px-2 py-2 w-20">
                              <input
                                className={inputClass}
                                type="number"
                                min={0}
                                step="0.01"
                                value={row.tax_rate}
                                onChange={(e) => updateLine(row.key, { tax_rate: Number(e.target.value) })}
                              />
                            </td>
                            <td className="px-2 py-2 w-28 font-medium text-gray-800">${amounts.total.toFixed(2)}</td>
                            <td className="px-2 py-2 w-16 text-right">
                              <button
                                type="button"
                                onClick={() => removeLine(row.key)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Quitar
                              </button>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 rounded-md bg-gray-50 p-3 text-sm">
              <div>
                <span className="text-gray-500">Subtotal</span>
                <div className="font-semibold">${totals.subtotal.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-gray-500">IVA</span>
                <div className="font-semibold">${totals.tax_total.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-gray-500">Total factura</span>
                <div className="font-semibold">${totals.total.toFixed(2)}</div>
              </div>
            </div>

            <details className="rounded-md border border-gray-200 p-3">
              <summary className="cursor-pointer text-sm text-gray-600">Más opciones</summary>
              <div className="mt-3 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField label="Fecha emisión">
                    <input className={inputClass} type="date" required value={form.issue_date} onChange={(e) => setForm({ ...form, issue_date: e.target.value })} />
                  </FormField>
                  <FormField label="Fecha vencimiento">
                    <input className={inputClass} type="date" required value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
                  </FormField>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <FormField label="Sucursal">
                    <select className={inputClass} required value={form.branch_id} onChange={(e) => setForm({ ...form, branch_id: e.target.value })}>
                      <option value="">Seleccionar sucursal</option>
                      {branches.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  </FormField>
                  <FormField label="Depósito">
                    <select className={inputClass} required value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}>
                      <option value="">Seleccionar depósito</option>
                      {warehouses.map((w) => (
                        <option key={w.id} value={w.id}>
                          {w.name}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>
                <FormField label="Notas">
                  <textarea className={inputClass} rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                </FormField>
              </div>
            </details>
          </form>
        )}
      </Modal>

      <Modal
        open={emitOpen}
        title={emitInvoice ? `Emitir fiscal ${emitInvoice.series}-${emitInvoice.number}` : 'Emitir fiscal'}
        onClose={closeEmitFiscal}
        footer={
          <>
            <button type="button" onClick={closeEmitFiscal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="emit-fiscal-form"
              disabled={emitSaving || !emitCertificateId}
              className="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {emitSaving ? 'Emitiendo...' : 'Crear y emitir'}
            </button>
          </>
        }
      >
        {emitError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{emitError}</div>}
        <form id="emit-fiscal-form" onSubmit={handleEmitFiscal} className="space-y-4">
          <p className="text-sm text-gray-600">
            Se creará un documento fiscal con los datos de la factura y se emitirá con el certificado seleccionado.
          </p>
          <FormField label="Certificado">
            <select
              className={inputClass}
              required
              value={emitCertificateId}
              onChange={(e) => setEmitCertificateId(e.target.value)}
            >
              <option value="">Seleccionar certificado</option>
              {certificates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </FormField>
        </form>
      </Modal>
    </div>
  )
}

export default Invoices
