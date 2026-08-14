import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Modal from '../components/Modal'
import { invoicesApi, InvoiceResponse } from '../services/invoices'
import { invoiceItemsApi } from '../services/invoiceItems'
import { customersApi, CustomerResponse } from '../services/customers'
import { productsApi, ProductResponse } from '../services/products'
import { branchesApi, BranchResponse } from '../services/branches'
import { warehousesApi, WarehouseResponse } from '../services/warehouses'
import { paymentsApi } from '../services/payments'
import { stockMovementsApi } from '../services/stockMovements'
import { certificatesApi, CertificateResponse } from '../services/certificates'
import { fiscalDocumentsApi } from '../services/fiscalDocuments'
import { getErrorMessage } from '../utils/errors'
import { inputClass } from '../components/FormField'
import BrandLogo from '../components/BrandLogo'
import { useCatalog } from '../hooks/useCatalog'
import {
  clearHeldCart,
  loadHeldCart,
  loadPosPrefs,
  loadRecentProductIds,
  playPosTone,
  pushRecentProductId,
  saveHeldCart,
  savePosPrefs,
  type PosPrefs,
} from '../utils/posExtras'

const normalizeCode = (value: string) => value.trim().toLowerCase()

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
      (p.barcode ? normalizeCode(p.barcode).includes(query) : false)
  )
  return partial.length === 1 ? partial[0] : null
}

const suggestProducts = (products: ProductResponse[], rawQuery: string, limit = 8): ProductResponse[] => {
  const query = normalizeCode(rawQuery)
  if (!query) return []
  return products
    .filter(
      (p) =>
        normalizeCode(p.name).includes(query) ||
        normalizeCode(p.sku).includes(query) ||
        (p.barcode ? normalizeCode(p.barcode).includes(query) : false)
    )
    .slice(0, limit)
}

const money = (n: number) => Number((n || 0).toFixed(2))
const todayIso = () => new Date().toISOString().slice(0, 10)
const toIsoDate = (date: string) => `${date}T00:00:00`

const nextNumberForSeries = (invoices: InvoiceResponse[], series: string): string => {
  const nums = invoices
    .filter((inv) => inv.series === series)
    .map((inv) => parseInt(inv.number, 10))
    .filter((n) => !Number.isNaN(n))
  const next = nums.length ? Math.max(...nums) + 1 : 1
  return String(next).padStart(8, '0')
}

type CartLine = {
  key: string
  product_id: string
  name: string
  sku?: string
  quantity: number
  unit_price: number
  tax_rate: number
  is_service?: boolean
}

type LastSale = {
  invoice: InvoiceResponse
  label: string
  lines: CartLine[]
  subtotal: number
  tax_total: number
  total: number
  payment_method: string
  warehouse_name: string
  customer_name: string
}

const lineAmounts = (line: CartLine) => {
  const net = money(line.quantity * line.unit_price)
  const tax = money((net * (line.tax_rate || 0)) / 100)
  return { net, tax, total: money(net + tax) }
}

const POS_PAYMENT_HINTS: Record<string, string> = { cash: 'F5', card: 'F6', transfer: 'F7' }

const printTicket = (sale: LastSale, formatMoney: (n: number) => string, paymentLabel: (v: string) => string) => {
  const rows = sale.lines
    .map((line) => {
      const a = lineAmounts(line)
      return `<tr>
        <td>${line.name}</td>
        <td style="text-align:right">${line.quantity}</td>
        <td style="text-align:right">${a.total.toFixed(2)}</td>
      </tr>`
    })
    .join('')
  const html = `<!doctype html><html><head><title>${sale.label}</title>
    <style>
      body{font-family:ui-monospace,Consolas,monospace;padding:16px;color:#111;max-width:320px}
      h1{font-size:15px;margin:0 0 4px;letter-spacing:0.02em}
      .brand{font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:#666;margin-bottom:8px}
      table{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}
      th,td{padding:4px 0;border-bottom:1px solid #ddd}
      .muted{color:#555;font-size:11px;line-height:1.5}
      .total{font-size:18px;font-weight:700;margin-top:12px;border-top:2px solid #111;padding-top:8px}
    </style></head><body>
    <div class="brand">Nexorux POS</div>
    <h1>e-Ticket ${sale.label}</h1>
    <div class="muted">${new Date().toLocaleString('es-UY')}</div>
    <div class="muted">Cliente: ${sale.customer_name}</div>
    <div class="muted">Depósito: ${sale.warehouse_name}</div>
    <div class="muted">Pago: ${paymentLabel(sale.payment_method)}</div>
    <table>
      <thead><tr><th align="left">Producto</th><th align="right">Cant</th><th align="right">Total</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="muted">Subtotal ${sale.subtotal.toFixed(2)} · IVA ${sale.tax_total.toFixed(2)}</div>
    <div class="total">TOTAL ${formatMoney(sale.total)}</div>
    <script>window.onload=()=>{window.print();}</script>
    </body></html>`
  const w = window.open('', '_blank', 'noopener,noreferrer,width=420,height=640')
  if (!w) return
  w.document.write(html)
  w.document.close()
}

const Kbd = ({ children }: { children: string }) => (
  <kbd className="rounded border border-slate-300 bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
    {children}
  </kbd>
)

const Pos = () => {
  const { user } = useAuth()
  const { catalog, currency: companyCurrency } = useCatalog()
  const formatMoney = (n: number) =>
    new Intl.NumberFormat('es-UY', { style: 'currency', currency: companyCurrency || 'UYU' }).format(n)
  const paymentMethods = (catalog?.payment_methods || []).filter((m) =>
    ['cash', 'card', 'transfer'].includes(m.value)
  )
  const paymentLabel = (value: string) =>
    paymentMethods.find((m) => m.value === value)?.label ||
    catalog?.payment_methods.find((m) => m.value === value)?.label ||
    value
  const posDocType = catalog?.defaults.pos_document_type || '101'
  const posDocLabel = catalog?.document_types.find((d) => d.value === posDocType)?.label || 'e-Ticket'
  const posPaidStatus = catalog?.defaults.pos_invoice_status || 'paid'
  const scanRef = useRef<HTMLInputElement>(null)
  const cashRef = useRef<HTMLInputElement>(null)

  const [products, setProducts] = useState<ProductResponse[]>([])
  const [customers, setCustomers] = useState<CustomerResponse[]>([])
  const [branches, setBranches] = useState<BranchResponse[]>([])
  const [warehouses, setWarehouses] = useState<WarehouseResponse[]>([])
  const [existingInvoices, setExistingInvoices] = useState<InvoiceResponse[]>([])
  const [balances, setBalances] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [now, setNow] = useState(() => new Date())

  const [cart, setCart] = useState<CartLine[]>([])
  const [scanQuery, setScanQuery] = useState('')
  const [scanMessage, setScanMessage] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [series, setSeries] = useState('A')
  const [warehouseId, setWarehouseId] = useState('')
  const [branchId, setBranchId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [amountReceived, setAmountReceived] = useState('')
  const [saving, setSaving] = useState(false)
  const [checkoutError, setCheckoutError] = useState<string | null>(null)
  const [lastSale, setLastSale] = useState<LastSale | null>(null)

  const [emitOpen, setEmitOpen] = useState(false)
  const [certificates, setCertificates] = useState<CertificateResponse[]>([])
  const [emitCertificateId, setEmitCertificateId] = useState('')
  const [emitError, setEmitError] = useState<string | null>(null)
  const [emitSaving, setEmitSaving] = useState(false)

  const [prefs, setPrefs] = useState<PosPrefs>(() => loadPosPrefs())
  const [recentIds, setRecentIds] = useState<string[]>(() => loadRecentProductIds())
  const [heldAt, setHeldAt] = useState<string | null>(() => loadHeldCart()?.savedAt ?? null)
  const [modoCaja, setModoCaja] = useState(false)

  const suggestions = useMemo(() => suggestProducts(products, scanQuery), [products, scanQuery])

  const totals = useMemo(() => {
    return cart.reduce(
      (acc, line) => {
        const a = lineAmounts(line)
        acc.subtotal = money(acc.subtotal + a.net)
        acc.tax_total = money(acc.tax_total + a.tax)
        acc.total = money(acc.total + a.total)
        return acc
      },
      { subtotal: 0, tax_total: 0, total: 0 }
    )
  }, [cart])

  const receivedNum = money(Number(amountReceived) || 0)
  const changeDue =
    paymentMethod === 'cash' && amountReceived !== '' ? money(receivedNum - totals.total) : null

  const finalConsumer = useMemo(
    () =>
      customers.find((c) => c.customer_type === 'final_consumer') ||
      customers.find((c) => /consumidor final/i.test(c.legal_name)) ||
      customers[0],
    [customers]
  )

  const stockWarnings = useMemo(() => {
    const msgs: string[] = []
    for (const line of cart) {
      if (line.is_service) continue
      const available = balances[line.product_id] ?? 0
      if (line.quantity > available) {
        msgs.push(`${line.name}: pedís ${line.quantity}, hay ${available}`)
      }
    }
    return msgs
  }, [cart, balances])

  const nextTicket = `${series}-${nextNumberForSeries(existingInvoices, series)}`
  const selectedWarehouse = warehouses.find((w) => w.id === warehouseId)
  const selectedBranch = branches.find((b) => b.id === branchId)

  const sessionStats = useMemo(() => {
    const today = todayIso()
    const posInvoices = existingInvoices.filter((inv) => {
      const day = (inv.issue_date || '').slice(0, 10)
      if (day !== today) return false
      const meta = inv.metadata || {}
      const notes = inv.notes || ''
      return meta.pos === true || meta.channel === 'pos' || /caja rápida|POS/i.test(notes)
    })
    return {
      count: posInvoices.length,
      total: money(posInvoices.reduce((s, inv) => s + Number(inv.total || 0), 0)),
    }
  }, [existingInvoices])

  const quickProducts = useMemo(() => {
    const byId = new Map(products.map((p) => [p.id, p]))
    const fromRecent = recentIds.map((id) => byId.get(id)).filter(Boolean) as ProductResponse[]
    if (fromRecent.length >= 12) return fromRecent.slice(0, 12)
    const rest = products.filter((p) => !recentIds.includes(p.id)).slice(0, 12 - fromRecent.length)
    return [...fromRecent, ...rest]
  }, [products, recentIds])

  const updatePrefs = (patch: Partial<PosPrefs>) => {
    setPrefs((prev) => {
      const next = { ...prev, ...patch }
      savePosPrefs(next)
      return next
    })
  }

  const tone = (kind: 'ok' | 'err' | 'cash') => {
    if (prefs.sound) playPosTone(kind)
  }

  const loadBalances = async (wid: string) => {
    if (!wid) {
      setBalances({})
      return
    }
    try {
      const rows = await stockMovementsApi.balances({ warehouse_id: wid })
      const map: Record<string, number> = {}
      for (const row of rows) {
        map[row.product_id] = Number(row.quantity) || 0
      }
      setBalances(map)
    } catch {
      setBalances({})
    }
  }

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setLoadError(null)
      try {
        const [p, c, b, w, inv] = await Promise.all([
          productsApi.list(),
          customersApi.list(),
          branchesApi.list(),
          warehousesApi.list(),
          invoicesApi.list(),
        ])
        setProducts(p.filter((x) => x.is_active !== false))
        setCustomers(c)
        setBranches(b)
        setWarehouses(w)
        setExistingInvoices(inv)
        setWarehouseId((prev) => prev || w[0]?.id || '')
        setBranchId((prev) => prev || b[0]?.id || '')
      } catch (err) {
        setLoadError(getErrorMessage(err, 'No se pudieron cargar datos de caja'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if (warehouseId) loadBalances(warehouseId)
  }, [warehouseId])

  useEffect(() => {
    if (loading) return
    const t = window.setTimeout(() => scanRef.current?.focus(), 50)
    return () => window.clearTimeout(t)
  }, [loading, lastSale, cart.length])

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  const addOrIncrementProduct = (product: ProductResponse) => {
    const available = balances[product.id] ?? 0
    const isService = Boolean(product.is_service) || product.product_type === 'service'
    const existing = cart.find((l) => l.product_id === product.id)
    const nextQty = existing ? money(Number(existing.quantity) + 1) : 1
    if (!isService && nextQty > available) {
      setScanMessage(`Stock insuficiente: ${product.name} (hay ${available})`)
      tone('err')
      return
    }
    setCart((prev) => {
      const found = prev.find((l) => l.product_id === product.id)
      if (found) {
        return prev.map((l) => (l.key === found.key ? { ...l, quantity: nextQty } : l))
      }
      return [
        ...prev,
        {
          key: `pos-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          quantity: 1,
          unit_price: Number(product.sales_price),
          tax_rate: Number(product.tax_rate ?? 22),
          is_service: isService,
        },
      ]
    })
    setRecentIds(pushRecentProductId(product.id))
    setScanMessage(`+ ${product.name}`)
    setScanQuery('')
    setShowSuggestions(false)
    tone('ok')
    scanRef.current?.focus()
  }

  const handleScanSubmit = () => {
    const q = scanQuery.trim()
    if (!q) return
    const product = matchProduct(products, q)
    if (!product) {
      setScanMessage(`No encontrado: ${q}`)
      setShowSuggestions(true)
      tone('err')
      return
    }
    addOrIncrementProduct(product)
  }

  const updateUnitPrice = (key: string, unit_price: number) => {
    setCart((prev) =>
      prev.map((l) => (l.key === key ? { ...l, unit_price: Math.max(0, money(unit_price)) } : l))
    )
  }

  const updateQty = (key: string, quantity: number) => {
    setCart((prev) =>
      prev
        .map((l) => {
          if (l.key !== key) return l
          const qty = Math.max(0, quantity)
          if (!l.is_service) {
            const available = balances[l.product_id] ?? 0
            if (qty > available) {
              setScanMessage(`Stock insuficiente: ${l.name} (hay ${available})`)
              return { ...l, quantity: available > 0 ? available : l.quantity }
            }
          }
          return { ...l, quantity: qty }
        })
        .filter((l) => l.quantity > 0)
    )
  }

  const removeLine = (key: string) => setCart((prev) => prev.filter((l) => l.key !== key))

  const clearCart = (opts?: { force?: boolean }) => {
    if (!opts?.force && cart.length > 0) {
      const ok = window.confirm('¿Vaciar el ticket actual?')
      if (!ok) return
    }
    setCart([])
    setCheckoutError(null)
    setScanMessage(null)
    setScanQuery('')
    setAmountReceived('')
    scanRef.current?.focus()
  }

  /** F1 — deja el ticket listo para escanear de nuevo (cierra banner de última venta). */
  const startNewSale = (opts?: { force?: boolean }) => {
    if (!opts?.force && cart.length > 0) {
      const ok = window.confirm('¿Cerrar el ticket actual y empezar una nueva venta?')
      if (!ok) return
    }
    setCart([])
    setLastSale(null)
    setCheckoutError(null)
    setScanMessage(null)
    setScanQuery('')
    setAmountReceived('')
    setEmitOpen(false)
    scanRef.current?.focus()
  }

  const holdCart = () => {
    if (!cart.length) {
      setScanMessage('Nada para poner en espera')
      tone('err')
      return
    }
    const savedAt = new Date().toISOString()
    saveHeldCart({
      cart,
      paymentMethod,
      amountReceived,
      series,
      warehouseId,
      branchId,
      savedAt,
    })
    setHeldAt(savedAt)
    setCart([])
    setAmountReceived('')
    setScanMessage('Ticket en espera — podés recuperarlo cuando quieras')
    tone('ok')
    scanRef.current?.focus()
  }

  const resumeHeldCart = () => {
    const held = loadHeldCart()
    if (!held || !Array.isArray(held.cart) || held.cart.length === 0) {
      setScanMessage('No hay ticket en espera')
      tone('err')
      return
    }
    if (cart.length > 0) {
      const ok = window.confirm('Hay un ticket abierto. ¿Reemplazarlo con el que está en espera?')
      if (!ok) return
    }
    setCart(held.cart as CartLine[])
    setPaymentMethod(held.paymentMethod || 'cash')
    setAmountReceived(held.amountReceived || '')
    if (held.series) setSeries(held.series)
    if (held.warehouseId) setWarehouseId(held.warehouseId)
    if (held.branchId) setBranchId(held.branchId)
    clearHeldCart()
    setHeldAt(null)
    setScanMessage('Ticket en espera restaurado')
    tone('ok')
    scanRef.current?.focus()
  }

  const enterModoCaja = async () => {
    setModoCaja(true)
    document.body.style.overflow = 'hidden'
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
      }
    } catch {
      // overlay still works without browser fullscreen
    }
    window.setTimeout(() => scanRef.current?.focus(), 80)
  }

  const exitModoCaja = async () => {
    setModoCaja(false)
    document.body.style.overflow = ''
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen()
      }
    } catch {
      // ignore
    }
    window.setTimeout(() => scanRef.current?.focus(), 80)
  }

  const toggleModoCaja = () => {
    if (modoCaja) void exitModoCaja()
    else void enterModoCaja()
  }

  const handleCheckout = async () => {
    if (!user) return
    if (!cart.length) {
      setCheckoutError('Agregá al menos un producto')
      return
    }
    if (!finalConsumer) {
      setCheckoutError('Falta cliente Consumidor Final. Crealo en Clientes.')
      return
    }
    const branch = branches.find((b) => b.id === branchId) || branches[0]
    const warehouse = warehouses.find((w) => w.id === warehouseId) || warehouses[0]
    if (!branch || !warehouse) {
      setCheckoutError('Configurá al menos una sucursal y un depósito')
      return
    }
    if (stockWarnings.length) {
      setCheckoutError(`Stock insuficiente: ${stockWarnings.join(' · ')}`)
      return
    }
    if (paymentMethod === 'cash' && amountReceived !== '' && receivedNum < totals.total) {
      setCheckoutError('El monto recibido es menor al total')
      return
    }

    setSaving(true)
    setCheckoutError(null)
    try {
      const number = nextNumberForSeries(existingInvoices, series)
      const issue = todayIso()
      const created = await invoicesApi.create({
        tenant_id: user.tenant_id,
        company_id: user.company_id,
        customer_id: finalConsumer.id,
        branch_id: branch.id,
        warehouse_id: warehouse.id,
        document_type: posDocType,
        series,
        number,
        status: posPaidStatus,
        issue_date: toIsoDate(issue),
        due_date: toIsoDate(issue),
        subtotal: totals.subtotal,
        tax_total: totals.tax_total,
        discount_total: 0,
        total: totals.total,
        currency: companyCurrency,
        exchange_rate: 1,
        notes: `Caja rápida (POS) · ${paymentLabel(paymentMethod)}`,
        metadata: {
          pos: true,
          channel: 'pos',
          payment_method: paymentMethod,
          ...(paymentMethod === 'cash' && amountReceived
            ? { amount_received: receivedNum, change: money(receivedNum - totals.total) }
            : {}),
        },
      })

      for (const line of cart) {
        const a = lineAmounts(line)
        await invoiceItemsApi.create({
          tenant_id: user.tenant_id,
          company_id: user.company_id,
          invoice_id: created.id,
          product_id: line.product_id,
          quantity: line.quantity,
          unit_price: line.unit_price,
          discount: 0,
          tax_amount: a.tax,
          total: a.total,
          description: line.name,
        })
      }

      try {
        await paymentsApi.create({
          tenant_id: user.tenant_id,
          company_id: user.company_id,
          invoice_id: created.id,
          customer_id: finalConsumer.id,
          payment_date: new Date().toISOString(),
          amount: totals.total,
          currency: companyCurrency,
          payment_method: paymentMethod,
          status: catalog?.defaults.payment_status === 'pending' ? 'completed' : catalog?.payment_statuses.find((s) => s.value === 'completed')?.value || 'completed',
          reference: `POS ${series}-${number}`,
        })
      } catch {
        // Payment optional if permissions missing; ticket still created
      }

      const sale: LastSale = {
        invoice: created,
        label: `${series}-${number}`,
        lines: cart,
        subtotal: totals.subtotal,
        tax_total: totals.tax_total,
        total: totals.total,
        payment_method: paymentMethod,
        warehouse_name: warehouse.name,
        customer_name: finalConsumer.legal_name,
      }

      setExistingInvoices((prev) => [...prev, created])
      setLastSale(sale)
      setCart([])
      setAmountReceived('')
      setScanMessage(null)
      tone('cash')
      if (prefs.autoPrint) {
        window.setTimeout(() => printTicket(sale, formatMoney, paymentLabel), 120)
      }
      await loadBalances(warehouse.id)
    } catch (err) {
      setCheckoutError(getErrorMessage(err, 'No se pudo cobrar el ticket'))
    } finally {
      setSaving(false)
      scanRef.current?.focus()
    }
  }

  const openEmitFiscal = async () => {
    if (!lastSale) return
    setEmitError(null)
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

  const handleEmitFiscal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user || !lastSale || !emitCertificateId) return
    setEmitSaving(true)
    setEmitError(null)
    try {
      const fiscalDoc = await fiscalDocumentsApi.create({
        tenant_id: user.tenant_id,
        company_id: lastSale.invoice.company_id || user.company_id,
        invoice_id: lastSale.invoice.id,
        document_type: lastSale.invoice.document_type,
        series: lastSale.invoice.series,
        number: lastSale.invoice.number,
        state: 'draft',
      })
      await fiscalDocumentsApi.issue(fiscalDoc.id, { certificate_id: emitCertificateId })
      setEmitOpen(false)
      setScanMessage(`Fiscal emitido para ${lastSale.label}`)
    } catch (err) {
      setEmitError(getErrorMessage(err, 'No se pudo emitir el documento fiscal'))
    } finally {
      setEmitSaving(false)
    }
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'

      if (e.key === 'F1') {
        e.preventDefault()
        startNewSale()
        return
      }
      if (e.key === 'F2') {
        e.preventDefault()
        scanRef.current?.focus()
        return
      }
      if (e.key === 'F4') {
        e.preventDefault()
        holdCart()
        return
      }
      if (e.key === 'F5') {
        e.preventDefault()
        setPaymentMethod('cash')
        return
      }
      if (e.key === 'F6') {
        e.preventDefault()
        setPaymentMethod('card')
        return
      }
      if (e.key === 'F7') {
        e.preventDefault()
        setPaymentMethod('transfer')
        return
      }
      if (e.key === 'F8') {
        e.preventDefault()
        cashRef.current?.focus()
        return
      }
      if (e.key === 'F9') {
        e.preventDefault()
        if (!saving && cart.length > 0 && stockWarnings.length === 0) {
          void handleCheckout()
        }
        return
      }
      if (e.key === 'F11') {
        e.preventDefault()
        toggleModoCaja()
        return
      }
      if (e.key === 'Escape' && !typing) {
        e.preventDefault()
        if (cart.length > 0) {
          clearCart()
        } else if (modoCaja) {
          void exitModoCaja()
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saving, cart.length, stockWarnings.length, paymentMethod, amountReceived, totals.total, modoCaja])

  useEffect(() => {
    const onFs = () => {
      // If user exits browser fullscreen with Esc, also leave modo caja
      if (!document.fullscreenElement && modoCaja) {
        setModoCaja(false)
        document.body.style.overflow = ''
      }
    }
    document.addEventListener('fullscreenchange', onFs)
    return () => document.removeEventListener('fullscreenchange', onFs)
  }, [modoCaja])

  useEffect(() => {
    return () => {
      document.body.style.overflow = ''
    }
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
        <div className="text-center">
          <div className="mx-auto mb-3 h-8 w-8 animate-pulse rounded-full border-2 border-slate-300 border-t-slate-700" />
          Preparando caja…
        </div>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{loadError}</div>
    )
  }

  const posUi = (
    <div
      className={
        modoCaja
          ? 'mx-auto h-full max-w-[1600px] space-y-4'
          : '-mx-1 max-w-[1400px] space-y-4 lg:mx-0'
      }
    >
      {/* Top bar */}
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <BrandLogo size="sm" className="h-10 max-h-10" />
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">Caja rápida</h2>
              <p className="text-xs text-slate-500">
                {posDocLabel} · {finalConsumer?.legal_name || 'Consumidor final'}
                {!modoCaja && (
                  <>
                    {' · '}
                    <Link to="/invoices" className="text-slate-700 underline-offset-2 hover:underline">
                      Ver facturas
                    </Link>
                  </>
                )}
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <div className="hidden rounded-md bg-slate-100 px-2.5 py-1.5 text-xs text-slate-700 sm:block">
            Hoy POS:{' '}
            <span className="font-semibold tabular-nums">
              {sessionStats.count} · {formatMoney(sessionStats.total)}
            </span>
          </div>
          <div className="hidden tabular-nums text-slate-500 md:block">
            {now.toLocaleDateString('es-UY', { weekday: 'short', day: '2-digit', month: 'short' })}{' '}
            <span className="font-medium text-slate-800">
              {now.toLocaleTimeString('es-UY', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>
          <label className="flex items-center gap-2 text-slate-600">
            Serie
            <input
              className={`${inputClass} w-14 text-center font-semibold uppercase`}
              value={series}
              onChange={(e) => setSeries(e.target.value.toUpperCase() || 'A')}
              maxLength={5}
              aria-label="Serie del ticket"
            />
          </label>
          <div className="rounded-md bg-slate-100 px-2.5 py-1.5 font-mono text-xs text-slate-700">
            Próx. {nextTicket}
          </div>
          <button
            type="button"
            onClick={toggleModoCaja}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold ${
              modoCaja
                ? 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50'
                : 'bg-slate-900 text-white hover:bg-slate-800'
            }`}
            title="Oculta el menú y usa toda la pantalla (F11)"
          >
            {modoCaja ? 'Salir modo caja' : 'Modo caja'}
          </button>
        </div>
      </header>

      {lastSale && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
              Venta registrada
            </div>
            <div className="text-sm text-emerald-950">
              Ticket <span className="font-semibold">{lastSale.label}</span>
              <span className="text-emerald-700"> · {paymentLabel(lastSale.payment_method)} · </span>
              <span className="font-semibold tabular-nums">{formatMoney(lastSale.total)}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => printTicket(lastSale, formatMoney, paymentLabel)}
              className="rounded-md border border-emerald-300 bg-white px-3 py-1.5 text-sm font-medium text-emerald-900 hover:bg-emerald-100"
            >
              Imprimir
            </button>
            <button
              type="button"
              onClick={openEmitFiscal}
              className="rounded-md border border-emerald-300 bg-white px-3 py-1.5 text-sm font-medium text-emerald-900 hover:bg-emerald-100"
            >
              Emitir fiscal
            </button>
            <button
              type="button"
              onClick={() => startNewSale({ force: true })}
              className="inline-flex items-center gap-1.5 rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-800"
            >
              Nueva venta
              <span className="rounded border border-emerald-500/50 bg-emerald-800/50 px-1 py-0.5 font-mono text-[10px] text-emerald-50">
                F1
              </span>
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12 xl:items-start">
        {/* Left: scan + cart */}
        <section className="space-y-3 xl:col-span-8">
          <div className="relative">
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
              Buscar / escanear <Kbd>F2</Kbd>
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path
                    d="M4 7V5a1 1 0 0 1 1-1h2M4 17v2a1 1 0 0 0 1 1h2M20 7V5a1 1 0 0 0-1-1h-2M20 17v2a1 1 0 0 1-1 1h-2M7 12h10"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                  />
                </svg>
              </span>
              <input
                ref={scanRef}
                className="w-full rounded-lg border border-slate-300 bg-white py-3.5 pl-10 pr-4 text-base text-slate-900 shadow-sm outline-none ring-slate-900/10 placeholder:text-slate-400 focus:border-slate-500 focus:ring-2"
                value={scanQuery}
                placeholder="Código de barras, SKU o nombre · Enter para agregar"
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
            </div>
            {showSuggestions && suggestions.length > 0 && (
              <ul className="absolute z-30 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-xl">
                {suggestions.map((p) => {
                  const available = balances[p.id]
                  return (
                    <li key={p.id}>
                      <button
                        type="button"
                        className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left hover:bg-slate-50"
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => addOrIncrementProduct(p)}
                      >
                        <span className="min-w-0">
                          <span className="block truncate font-medium text-slate-900">{p.name}</span>
                          <span className="text-xs text-slate-500">
                            {[p.sku, p.barcode].filter(Boolean).join(' · ')}
                            {!p.is_service && available !== undefined ? ` · stock ${available}` : ''}
                          </span>
                        </span>
                        <span className="shrink-0 tabular-nums text-sm font-semibold text-slate-800">
                          {formatMoney(Number(p.sales_price))}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
            {scanMessage && (
              <p
                className={`mt-1.5 text-sm ${
                  scanMessage.startsWith('+') || scanMessage.includes('espera')
                    ? 'text-emerald-700'
                    : 'text-amber-700'
                }`}
                role="status"
              >
                {scanMessage}
              </p>
            )}
          </div>

          {quickProducts.length > 0 && (
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <h3 className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Acceso rápido
                </h3>
                <span className="text-[11px] text-slate-400">Recientes + catálogo</span>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                {quickProducts.map((p) => {
                  const available = balances[p.id]
                  const isService = Boolean(p.is_service) || p.product_type === 'service'
                  const out = !isService && available !== undefined && available <= 0
                  return (
                    <button
                      key={p.id}
                      type="button"
                      disabled={out}
                      onClick={() => addOrIncrementProduct(p)}
                      className="rounded-lg border border-slate-200 bg-white px-2.5 py-2.5 text-left shadow-sm transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
                    >
                      <div className="truncate text-sm font-medium text-slate-900">{p.name}</div>
                      <div className="mt-1 flex items-center justify-between gap-1 text-[11px] text-slate-500">
                        <span className="tabular-nums font-semibold text-slate-800">
                          {formatMoney(Number(p.sales_price))}
                        </span>
                        <span>{out ? 'Sin stock' : isService ? 'Serv.' : `Stk ${available ?? '—'}`}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-slate-50 px-3 py-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                Ticket · {cart.length} {cart.length === 1 ? 'ítem' : 'ítems'}
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={holdCart}
                  disabled={cart.length === 0}
                  className="text-xs font-medium text-slate-600 hover:text-slate-900 disabled:opacity-40"
                >
                  En espera <Kbd>F4</Kbd>
                </button>
                {heldAt && (
                  <button
                    type="button"
                    onClick={resumeHeldCart}
                    className="rounded-md bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-900 hover:bg-amber-200"
                  >
                    Recuperar espera
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => startNewSale()}
                  className="text-xs font-medium text-slate-600 hover:text-slate-900"
                >
                  Nueva venta <Kbd>F1</Kbd>
                </button>
                <button
                  type="button"
                  onClick={() => clearCart()}
                  disabled={cart.length === 0}
                  className="text-xs font-medium text-slate-500 hover:text-slate-800 disabled:opacity-40"
                >
                  Vaciar <Kbd>Esc</Kbd>
                </button>
              </div>
            </div>
            <div
              className={`overflow-auto ${
                modoCaja ? 'max-h-[min(62vh,720px)]' : 'max-h-[min(52vh,560px)] xl:max-h-[min(58vh,640px)]'
              }`}
            >
              <table className="min-w-full text-sm">
                <thead className="sticky top-0 bg-white text-left text-[11px] uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-3 py-2 font-medium">Producto</th>
                    <th className="px-3 py-2 font-medium w-36">Cantidad</th>
                    <th className="px-3 py-2 font-medium w-20">Stock</th>
                    <th className="px-3 py-2 font-medium w-28 text-right">P. unit.</th>
                    <th className="px-3 py-2 font-medium w-28 text-right">Total</th>
                    <th className="px-3 py-2 w-12" />
                  </tr>
                </thead>
                <tbody>
                  {cart.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-3 py-16 text-center">
                        <div className="text-slate-400">
                          <div className="mb-1 text-sm font-medium text-slate-500">Ticket vacío</div>
                          <p className="text-xs">Escaneá un código o buscá por nombre para empezar</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    cart.map((line) => {
                      const a = lineAmounts(line)
                      const available = line.is_service ? null : balances[line.product_id] ?? 0
                      const low = available !== null && line.quantity > available
                      return (
                        <tr
                          key={line.key}
                          className={`border-t border-slate-100 ${low ? 'bg-amber-50' : 'hover:bg-slate-50/80'}`}
                        >
                          <td className="px-3 py-2.5">
                            <div className="font-medium text-slate-900">{line.name}</div>
                            <div className="text-xs text-slate-500">
                              {line.sku || '—'} · IVA {line.tax_rate}%
                            </div>
                          </td>
                          <td className="px-3 py-2.5">
                            <div className="inline-flex items-center rounded-md border border-slate-200 bg-white">
                              <button
                                type="button"
                                className="h-9 w-9 text-lg text-slate-600 hover:bg-slate-50"
                                onClick={() => updateQty(line.key, line.quantity - 1)}
                                aria-label="Restar"
                              >
                                −
                              </button>
                              <input
                                className="w-12 border-x border-slate-200 py-1.5 text-center tabular-nums outline-none"
                                type="number"
                                min={0}
                                step="1"
                                value={line.quantity}
                                onChange={(e) => updateQty(line.key, Number(e.target.value))}
                              />
                              <button
                                type="button"
                                className="h-9 w-9 text-lg text-slate-600 hover:bg-slate-50"
                                onClick={() => updateQty(line.key, line.quantity + 1)}
                                aria-label="Sumar"
                              >
                                +
                              </button>
                            </div>
                          </td>
                          <td
                            className={`px-3 py-2.5 tabular-nums ${
                              low ? 'font-semibold text-amber-800' : 'text-slate-500'
                            }`}
                          >
                            {available === null ? '—' : available}
                          </td>
                          <td className="px-3 py-2.5 text-right">
                            <input
                              type="number"
                              min={0}
                              step="0.01"
                              className="w-24 rounded border border-slate-200 px-1.5 py-1 text-right tabular-nums text-slate-800 outline-none focus:border-slate-400"
                              value={line.unit_price}
                              onChange={(e) => updateUnitPrice(line.key, Number(e.target.value))}
                              aria-label={`Precio de ${line.name}`}
                            />
                          </td>
                          <td className="px-3 py-2.5 text-right font-semibold tabular-nums text-slate-900">
                            {formatMoney(a.total)}
                          </td>
                          <td className="px-3 py-2.5 text-right">
                            <button
                              type="button"
                              className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                              onClick={() => removeLine(line.key)}
                              aria-label="Quitar línea"
                            >
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
                                <path
                                  d="M6 6l12 12M18 6L6 18"
                                  stroke="currentColor"
                                  strokeWidth="1.75"
                                  strokeLinecap="round"
                                />
                              </svg>
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

          {stockWarnings.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Stock insuficiente: {stockWarnings.join(' · ')}
            </div>
          )}
        </section>

        {/* Right: checkout panel */}
        <aside className="xl:col-span-4">
          <div className="sticky top-4 space-y-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
                Depósito
                <select
                  className={`${inputClass} mt-1`}
                  value={warehouseId}
                  onChange={(e) => setWarehouseId(e.target.value)}
                >
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
                Sucursal
                <select
                  className={`${inputClass} mt-1`}
                  value={branchId}
                  onChange={(e) => setBranchId(e.target.value)}
                >
                  {branches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div>
              <div className="mb-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
                Medio de pago
              </div>
              <div className="grid grid-cols-3 gap-2">
                {(paymentMethods.length ? paymentMethods : [{ value: 'cash', label: 'Efectivo' }]).map((m) => {
                  const active = paymentMethod === m.value
                  const hint = POS_PAYMENT_HINTS[m.value]
                  return (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setPaymentMethod(m.value)}
                      className={`rounded-md border px-2 py-2.5 text-center transition ${
                        active
                          ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                          : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 hover:bg-white'
                      }`}
                    >
                      <div className="text-sm font-semibold leading-tight">{m.label}</div>
                      {hint ? (
                        <div className={`mt-0.5 text-[10px] ${active ? 'text-slate-300' : 'text-slate-400'}`}>
                          {hint}
                        </div>
                      ) : null}
                    </button>
                  )
                })}
              </div>
            </div>

            {paymentMethod === 'cash' && (
              <div>
                <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
                  Monto recibido <Kbd>F8</Kbd>
                  <input
                    ref={cashRef}
                    type="number"
                    min={0}
                    step="0.01"
                    className={`${inputClass} mt-1 text-lg font-semibold tabular-nums`}
                    placeholder={totals.total ? totals.total.toFixed(2) : '0.00'}
                    value={amountReceived}
                    onChange={(e) => setAmountReceived(e.target.value)}
                  />
                </label>
                {changeDue !== null && (
                  <div
                    className={`mt-2 flex items-center justify-between rounded-md px-3 py-2 text-sm ${
                      changeDue < 0
                        ? 'bg-red-50 text-red-800'
                        : 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    <span>Vuelto</span>
                    <span className="text-lg font-bold tabular-nums">{formatMoney(changeDue)}</span>
                  </div>
                )}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {[totals.total, 100, 200, 500, 1000, 2000]
                    .filter((v, i, arr) => v > 0 && arr.indexOf(v) === i)
                    .map((v) => (
                      <button
                        key={v}
                        type="button"
                        className="rounded border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
                        onClick={() => setAmountReceived(String(v))}
                      >
                        {v === totals.total ? 'Exacto' : `$${v}`}
                      </button>
                    ))}
                </div>
              </div>
            )}

            <div className="rounded-lg bg-slate-900 px-4 py-4 text-white">
              <div className="flex justify-between text-sm text-slate-300">
                <span>Subtotal</span>
                <span className="tabular-nums">{formatMoney(totals.subtotal)}</span>
              </div>
              <div className="mt-1 flex justify-between text-sm text-slate-300">
                <span>IVA</span>
                <span className="tabular-nums">{formatMoney(totals.tax_total)}</span>
              </div>
              <div className="mt-3 flex items-end justify-between border-t border-slate-700 pt-3">
                <span className="text-sm font-medium text-slate-300">Total</span>
                <span className="text-3xl font-bold tracking-tight tabular-nums">
                  {formatMoney(totals.total)}
                </span>
              </div>
              <p className="mt-2 text-[11px] text-slate-400">
                {selectedBranch?.name || 'Sucursal'} · {selectedWarehouse?.name || 'Depósito'} ·{' '}
                {paymentLabel(paymentMethod)}
              </p>
            </div>

            {checkoutError && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {checkoutError}
              </div>
            )}

            <button
              type="button"
              disabled={saving || cart.length === 0 || stockWarnings.length > 0}
              onClick={handleCheckout}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 py-3.5 text-base font-semibold text-white shadow-sm transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-45"
            >
              {saving ? (
                'Procesando cobro…'
              ) : (
                <>
                  Cobrar e-Ticket
                  <span className="rounded border border-emerald-400/60 bg-emerald-700/40 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide">
                    F9
                  </span>
                </>
              )}
            </button>

            <div className="space-y-2 border-t border-slate-100 pt-3">
              <label className="flex cursor-pointer items-center justify-between gap-2 text-sm text-slate-700">
                <span>Autoimprimir al cobrar</span>
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300"
                  checked={prefs.autoPrint}
                  onChange={(e) => updatePrefs({ autoPrint: e.target.checked })}
                />
              </label>
              <label className="flex cursor-pointer items-center justify-between gap-2 text-sm text-slate-700">
                <span>Sonido al escanear</span>
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300"
                  checked={prefs.sound}
                  onChange={(e) => updatePrefs({ sound: e.target.checked })}
                />
              </label>
            </div>

            <p className="text-center text-[11px] leading-relaxed text-slate-400">
              <Kbd>F1</Kbd> nueva venta · <Kbd>F2</Kbd> buscar · <Kbd>F4</Kbd> espera · <Kbd>F5–F7</Kbd> pago ·{' '}
              <Kbd>F9</Kbd> cobrar · <Kbd>F11</Kbd> modo caja · <Kbd>Esc</Kbd> vaciar
            </p>
          </div>
        </aside>
      </div>

      <Modal
        open={emitOpen}
        title={`Emitir fiscal ${lastSale?.label || ''}`}
        onClose={() => setEmitOpen(false)}
        footer={
          <>
            <button
              type="button"
              onClick={() => setEmitOpen(false)}
              className="rounded-md px-4 py-2 text-slate-700 hover:bg-slate-100"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="pos-emit-form"
              disabled={emitSaving || !emitCertificateId}
              className="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {emitSaving ? 'Emitiendo...' : 'Emitir'}
            </button>
          </>
        }
      >
        <form id="pos-emit-form" onSubmit={handleEmitFiscal} className="space-y-4">
          {emitError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{emitError}</div>
          )}
          <p className="text-sm text-slate-600">
            Crea el documento fiscal del e-Ticket y lo firma con el certificado elegido.
          </p>
          <label className="block text-sm text-slate-700">
            Certificado
            <select
              className={`${inputClass} mt-1`}
              required
              value={emitCertificateId}
              onChange={(e) => setEmitCertificateId(e.target.value)}
            >
              <option value="">Elegir...</option>
              {certificates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || c.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
        </form>
      </Modal>
    </div>
  )

  if (modoCaja) {
    return createPortal(
      <div className="fixed inset-0 z-[200] flex flex-col bg-slate-100">
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-800 bg-slate-900 px-4 py-2.5 text-white shadow-md">
            <div className="flex items-center gap-2">
              <img
                src="/nexorux-erp-logo.png"
                alt=""
                className="h-7 w-auto object-contain brightness-0 invert"
              />
              <div>
                <div className="text-sm font-semibold tracking-wide">Modo caja</div>
                <div className="truncate text-[11px] text-slate-300">
                  Solo facturación rápida · menú oculto · {finalConsumer?.legal_name || 'Consumidor final'}
                </div>
              </div>
            </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="hidden text-xs text-slate-400 sm:inline">
              Hoy {sessionStats.count} · {formatMoney(sessionStats.total)}
            </span>
            <button
              type="button"
              onClick={() => void exitModoCaja()}
              className="rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-slate-900 hover:bg-slate-100"
            >
              Salir modo caja
              <span className="ml-1.5 text-[10px] font-medium text-slate-500">F11</span>
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-3 sm:p-5">{posUi}</div>
      </div>,
      document.body
    )
  }

  return posUi
}

export default Pos
