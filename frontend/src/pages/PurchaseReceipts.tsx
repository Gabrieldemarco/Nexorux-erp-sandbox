import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import {
  purchaseReceiptsApi,
  PurchaseReceiptResponse,
} from '../services/purchaseReceipts'
import { suppliersApi, SupplierResponse } from '../services/suppliers'
import { productsApi, ProductResponse } from '../services/products'
import { warehousesApi, WarehouseResponse } from '../services/warehouses'
import { getErrorMessage } from '../utils/errors'

type LineDraft = {
  key: string
  product_id: string
  quantity: number
  unit_cost: number
}

const newKey = () => `line-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
const todayLocal = () => new Date().toISOString().slice(0, 16)

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  const d = value.slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return value
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

const PurchaseReceipts = () => {
  const { user } = useAuth()
  const [items, setItems] = useState<PurchaseReceiptResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)

  const [suppliers, setSuppliers] = useState<SupplierResponse[]>([])
  const [products, setProducts] = useState<ProductResponse[]>([])
  const [warehouses, setWarehouses] = useState<WarehouseResponse[]>([])

  const [supplierId, setSupplierId] = useState('')
  const [warehouseId, setWarehouseId] = useState('')
  const [receiptDate, setReceiptDate] = useState(todayLocal())
  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState<LineDraft[]>([
    { key: newKey(), product_id: '', quantity: 1, unit_cost: 0 },
  ])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [receipts, s, p, w] = await Promise.all([
        purchaseReceiptsApi.list(),
        suppliersApi.list(),
        productsApi.list(),
        warehousesApi.list(),
      ])
      setItems(receipts)
      setSuppliers(s)
      setProducts(p.filter((prod) => !prod.is_service))
      setWarehouses(w)
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudieron cargar las entradas de proveedor'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const openCreate = () => {
    setModalError(null)
    setSupplierId(suppliers[0]?.id || '')
    setWarehouseId(warehouses[0]?.id || '')
    setReceiptDate(todayLocal())
    setNotes('')
    setLines([
      {
        key: newKey(),
        product_id: products[0]?.id || '',
        quantity: 1,
        unit_cost: Number(products[0]?.cost_price || 0),
      },
    ])
    setModalOpen(true)
  }

  const supplierName = (id?: string) =>
    suppliers.find((s) => s.id === id)?.legal_name || (id ? id.slice(0, 8) : '—')
  const warehouseName = (id?: string) =>
    warehouses.find((w) => w.id === id)?.name || (id ? id.slice(0, 8) : '—')
  const productName = (id?: string) =>
    products.find((p) => p.id === id)?.name || (id ? id.slice(0, 8) : '—')

  const updateLine = (key: string, patch: Partial<LineDraft>) => {
    setLines((prev) => prev.map((l) => (l.key === key ? { ...l, ...patch } : l)))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    const validLines = lines.filter((l) => l.product_id && Number(l.quantity) > 0)
    if (!supplierId || !warehouseId) {
      setModalError('Elegí proveedor y depósito')
      return
    }
    if (!validLines.length) {
      setModalError('Agregá al menos un producto con cantidad')
      return
    }

    setSaving(true)
    setModalError(null)
    try {
      await purchaseReceiptsApi.create({
        tenant_id: user.tenant_id,
        company_id: user.company_id,
        supplier_id: supplierId,
        warehouse_id: warehouseId,
        receipt_date: new Date(receiptDate).toISOString(),
        notes: notes || undefined,
        items: validLines.map((l) => ({
          product_id: l.product_id,
          quantity: Number(l.quantity),
          unit_cost: Number(l.unit_cost) || 0,
          description: products.find((p) => p.id === l.product_id)?.name,
        })),
      })
      setModalOpen(false)
      setMessage('Entrada registrada: el stock se sumó al depósito')
      await load()
    } catch (err) {
      setModalError(getErrorMessage(err, 'No se pudo registrar la entrada'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar esta entrada? También se revierte el stock sumado.')) return
    try {
      await purchaseReceiptsApi.delete(id)
      setMessage('Entrada eliminada')
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudo eliminar'))
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Entradas de proveedor</h2>
          <p className="text-sm text-gray-500">
            Mercadería que entra suma stock. Las ventas (factura / caja) lo restan. Ver saldos en{' '}
            <Link to="/stock-movements" className="text-blue-600 hover:underline">
              Stock
            </Link>
            .
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Registrar entrada
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {error && <div className="p-4 text-red-600">{error}</div>}
        {message && <div className="p-4 text-sm text-emerald-700 bg-emerald-50">{message}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Depósito</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Líneas</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.length === 0 && !loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  Todavía no hay entradas. Registrá la mercadería del proveedor para sumar stock.
                </td>
              </tr>
            ) : (
              items.map((r) => (
                <tr key={r.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{r.number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(r.receipt_date)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{supplierName(r.supplier_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warehouseName(r.warehouse_id)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {(r.items || [])
                      .map((i) => `${productName(i.product_id)} × ${i.quantity}`)
                      .join(', ') || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <button onClick={() => handleDelete(r.id)} className="text-red-600 hover:text-red-900">
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={modalOpen}
        title="Registrar entrada de proveedor"
        onClose={() => setModalOpen(false)}
        size="xl"
        footer={
          <>
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
            >
              Cancelar
            </button>
            <button
              type="submit"
              form="purchase-receipt-form"
              disabled={saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Sumar al stock'}
            </button>
          </>
        }
      >
        <form id="purchase-receipt-form" onSubmit={handleSubmit} className="space-y-4">
          {modalError && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{modalError}</div>}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormField label="Proveedor">
              <select
                className={inputClass}
                required
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
              >
                <option value="">Elegir...</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.legal_name}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Depósito">
              <select
                className={inputClass}
                required
                value={warehouseId}
                onChange={(e) => setWarehouseId(e.target.value)}
              >
                <option value="">Elegir...</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Fecha">
              <input
                className={inputClass}
                type="datetime-local"
                required
                value={receiptDate}
                onChange={(e) => setReceiptDate(e.target.value)}
              />
            </FormField>
          </div>
          <FormField label="Notas">
            <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </FormField>

          <div>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-medium text-gray-700">Productos</h3>
              <button
                type="button"
                className="text-sm text-blue-600 hover:underline"
                onClick={() =>
                  setLines((prev) => [
                    ...prev,
                    {
                      key: newKey(),
                      product_id: products[0]?.id || '',
                      quantity: 1,
                      unit_cost: Number(products[0]?.cost_price || 0),
                    },
                  ])
                }
              >
                + Línea
              </button>
            </div>
            <div className="space-y-2">
              {lines.map((line) => (
                <div key={line.key} className="grid grid-cols-12 gap-2 items-end">
                  <div className="col-span-6">
                    <select
                      className={inputClass}
                      value={line.product_id}
                      onChange={(e) => {
                        const prod = products.find((p) => p.id === e.target.value)
                        updateLine(line.key, {
                          product_id: e.target.value,
                          unit_cost: Number(prod?.cost_price || 0),
                        })
                      }}
                    >
                      <option value="">Producto...</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.sku})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input
                      className={inputClass}
                      type="number"
                      min={0.001}
                      step="any"
                      value={line.quantity}
                      onChange={(e) => updateLine(line.key, { quantity: Number(e.target.value) })}
                    />
                  </div>
                  <div className="col-span-3">
                    <input
                      className={inputClass}
                      type="number"
                      min={0}
                      step="any"
                      value={line.unit_cost}
                      onChange={(e) => updateLine(line.key, { unit_cost: Number(e.target.value) })}
                      placeholder="Costo"
                    />
                  </div>
                  <div className="col-span-1">
                    <button
                      type="button"
                      className="text-red-600 text-sm"
                      onClick={() => setLines((prev) => prev.filter((l) => l.key !== line.key))}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default PurchaseReceipts
