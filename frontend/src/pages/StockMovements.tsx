import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import {
  stockMovementsApi,
  StockMovementCreate,
  StockMovementResponse,
  StockMovementUpdate,
} from '../services/stockMovements'
import { productsApi, ProductResponse } from '../services/products'
import { warehousesApi, WarehouseResponse } from '../services/warehouses'

const movementTypes = [
  { value: 'in', label: 'Entrada' },
  { value: 'out', label: 'Salida' },
  { value: 'adjustment', label: 'Ajuste' },
]

const todayIso = () => new Date().toISOString()

const defaultForm = {
  product_id: '',
  warehouse_id: '',
  movement_type: 'in',
  quantity: 1,
  movement_date: todayIso().slice(0, 16),
}

const StockMovements = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<StockMovementResponse, StockMovementCreate, StockMovementUpdate>(
    stockMovementsApi,
    'No se pudieron cargar los movimientos de stock',
    '¿Eliminar este movimiento?'
  )
  const [form, setForm] = useState(defaultForm)
  const [products, setProducts] = useState<ProductResponse[]>([])
  const [warehouses, setWarehouses] = useState<WarehouseResponse[]>([])
  const [balances, setBalances] = useState<
    { product_id: string; warehouse_id: string; qty: number }[]
  >([])

  useEffect(() => {
    Promise.all([productsApi.list(), warehousesApi.list(), stockMovementsApi.balances()])
      .then(([p, w, b]) => {
        setProducts(p)
        setWarehouses(w)
        setBalances(
          b
            .map((row) => ({
              product_id: row.product_id,
              warehouse_id: row.warehouse_id,
              qty: Number(row.quantity) || 0,
            }))
            .sort((a, bRow) => {
              const pa = p.find((x) => x.id === a.product_id)?.name || a.product_id
              const pb = p.find((x) => x.id === bRow.product_id)?.name || bRow.product_id
              if (pa !== pb) return pa.localeCompare(pb)
              const wa = w.find((x) => x.id === a.warehouse_id)?.name || a.warehouse_id
              const wb = w.find((x) => x.id === bRow.warehouse_id)?.name || bRow.warehouse_id
              return wa.localeCompare(wb)
            })
        )
      })
      .catch(() => {
        setProducts([])
        setWarehouses([])
        setBalances([])
      })
  }, [crud.items])

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        product_id: crud.editing.product_id,
        warehouse_id: crud.editing.warehouse_id,
        movement_type: crud.editing.movement_type,
        quantity: Number(crud.editing.quantity),
        movement_date: crud.editing.movement_date.slice(0, 16),
      })
    } else {
      setForm({
        ...defaultForm,
        product_id: products[0]?.id || '',
        warehouse_id: warehouses[0]?.id || '',
        movement_date: todayIso().slice(0, 16),
      })
    }
  }, [crud.modalOpen, crud.editing, products, warehouses])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const movement_date = new Date(form.movement_date).toISOString()
    const payload = {
      product_id: form.product_id,
      warehouse_id: form.warehouse_id,
      movement_type: form.movement_type,
      quantity: form.quantity,
      movement_date,
    }
    const createData: StockMovementCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  const productName = (id: string) => products.find((p) => p.id === id)?.name || id.slice(0, 8)
  const warehouseName = (id: string) => warehouses.find((w) => w.id === id)?.name || id.slice(0, 8)
  const typeLabel = (t: string) => movementTypes.find((m) => m.value === t)?.label || t

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Movimientos de stock</h2>
          <p className="text-sm text-gray-500 mt-1">
            Saldos por producto y depósito. Para mercadería de proveedor usá{' '}
            <Link to="/purchase-receipts" className="text-blue-600 hover:underline">
              Entradas proveedor
            </Link>
            . Las ventas (caja / factura) restan stock automáticamente.
          </p>
        </div>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar movimiento
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        <div className="px-6 py-3 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-900">Saldos por producto / depósito</h3>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Producto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Depósito</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {balances.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-4 text-center text-gray-500 text-sm">
                  Sin saldos (no hay movimientos).
                </td>
              </tr>
            ) : (
              balances.map((b) => (
                <tr key={`${b.product_id}-${b.warehouse_id}`}>
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900">{productName(b.product_id)}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-500">{warehouseName(b.warehouse_id)}</td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{b.qty}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Producto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Depósito</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No hay movimientos de stock. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((row) => (
                <EntityListRow
                  key={row.id}
                  onOpen={() => crud.openEdit(row)}
                  actions={
                    <>
                      <button type="button" onClick={() => crud.openEdit(row)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(row.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{productName(row.product_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warehouseName(row.warehouse_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{typeLabel(row.movement_type)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.quantity}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.movement_date.slice(0, 10)}</td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={
          crud.editing
            ? `Movimiento · ${productName(crud.editing.product_id)} · ${crud.editing.movement_date.slice(0, 10)}`
            : 'Agregar movimiento'
        }
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="stock-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="stock-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Producto">
            <select
              className={inputClass}
              required
              value={form.product_id}
              onChange={(e) => setForm({ ...form, product_id: e.target.value })}
            >
              <option value="">Seleccionar producto</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Depósito">
            <select
              className={inputClass}
              required
              value={form.warehouse_id}
              onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}
            >
              <option value="">Seleccionar depósito</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Tipo">
              <select
                className={inputClass}
                value={form.movement_type}
                onChange={(e) => setForm({ ...form, movement_type: e.target.value })}
              >
                {movementTypes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Cantidad">
              <input
                className={inputClass}
                type="number"
                min={0}
                step="0.01"
                required
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
              />
            </FormField>
          </div>
          <FormField label="Fecha">
            <input
              className={inputClass}
              type="datetime-local"
              required
              value={form.movement_date}
              onChange={(e) => setForm({ ...form, movement_date: e.target.value })}
            />
          </FormField>
        </form>
      </Modal>
    </div>
  )
}

export default StockMovements
