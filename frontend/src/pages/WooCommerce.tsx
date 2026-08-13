import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  woocommerceApi,
  WooOrderItem,
  WooProductSyncItem,
  WooProductSyncResult,
  WooStockSyncResult,
} from '../services/woocommerce'
import { warehousesApi, WarehouseResponse } from '../services/warehouses'
import { getErrorMessage } from '../utils/errors'
import FormField, { inputClass } from '../components/FormField'

const SAMPLE_JSON = `[
  { "sku": "SKU-001", "name": "Producto demo", "regular_price": 100, "barcode": "779000000001" }
]`

type Tab = 'orders' | 'sync' | 'stock'

const WooCommerce = () => {
  const [tab, setTab] = useState<Tab>('orders')
  const [orders, setOrders] = useState<WooOrderItem[]>([])
  const [ordersLoading, setOrdersLoading] = useState(true)
  const [ordersError, setOrdersError] = useState<string | null>(null)

  const [jsonText, setJsonText] = useState(SAMPLE_JSON)
  const [dryRun, setDryRun] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncResult, setSyncResult] = useState<WooProductSyncResult | null>(null)

  const [warehouses, setWarehouses] = useState<WarehouseResponse[]>([])
  const [stockWarehouseId, setStockWarehouseId] = useState('')
  const [stockDryRun, setStockDryRun] = useState(true)
  const [stockPush, setStockPush] = useState(true)
  const [stockSyncing, setStockSyncing] = useState(false)
  const [stockError, setStockError] = useState<string | null>(null)
  const [stockResult, setStockResult] = useState<WooStockSyncResult | null>(null)

  const loadOrders = async () => {
    setOrdersLoading(true)
    setOrdersError(null)
    try {
      const data = await woocommerceApi.listOrders()
      setOrders(data)
    } catch (err) {
      setOrdersError(getErrorMessage(err, 'No se pudieron cargar los pedidos Woo'))
    } finally {
      setOrdersLoading(false)
    }
  }

  useEffect(() => {
    loadOrders()
    warehousesApi
      .list()
      .then((w) => {
        setWarehouses(w)
        setStockWarehouseId((prev) => prev || w[0]?.id || '')
      })
      .catch(() => setWarehouses([]))
  }, [])

  const handleSync = async () => {
    setSyncing(true)
    setSyncError(null)
    setSyncResult(null)
    try {
      const parsed = JSON.parse(jsonText) as unknown
      let products: WooProductSyncItem[]
      if (Array.isArray(parsed)) {
        products = parsed as WooProductSyncItem[]
      } else if (parsed && typeof parsed === 'object' && Array.isArray((parsed as { products?: unknown }).products)) {
        products = (parsed as { products: WooProductSyncItem[] }).products
      } else {
        throw new Error('El JSON debe ser un array de productos')
      }
      const result = await woocommerceApi.syncProducts(products, { dry_run: dryRun })
      setSyncResult(result)
    } catch (err) {
      setSyncError(getErrorMessage(err, 'Error al sincronizar productos'))
    } finally {
      setSyncing(false)
    }
  }

  const handleStockSync = async () => {
    setStockSyncing(true)
    setStockError(null)
    setStockResult(null)
    try {
      const result = await woocommerceApi.syncStock({
        dry_run: stockDryRun,
        push: stockPush && !stockDryRun,
        warehouse_id: stockWarehouseId || undefined,
      })
      setStockResult(result)
    } catch (err) {
      setStockError(getErrorMessage(err, 'Error al sincronizar stock'))
    } finally {
      setStockSyncing(false)
    }
  }

  const tabBtn = (id: Tab, label: string) => (
    <button
      type="button"
      onClick={() => setTab(id)}
      className={`px-4 py-2 rounded-md text-sm ${
        tab === id ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div>
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">WooCommerce</h2>
          <p className="text-sm text-gray-500">
            Pedidos → factura · reembolsos → NC · stock Nexorux → Woo
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {tabBtn('orders', 'Pedidos Woo')}
          {tabBtn('sync', 'Sync catálogo')}
          {tabBtn('stock', 'Sync stock')}
        </div>
      </div>

      {tab === 'orders' && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Facturas con <code className="text-xs">woocommerce_order_id</code>. Reembolsos Woo crean NC (102/112).
              Detalle en{' '}
              <Link to="/invoices" className="text-blue-600 hover:underline">
                Facturas
              </Link>
              .
            </div>
            <button type="button" onClick={loadOrders} className="text-sm text-blue-600 hover:text-blue-800">
              Actualizar
            </button>
          </div>
          {ordersLoading && <div className="p-4 text-gray-500">Cargando...</div>}
          {ordersError && <div className="p-4 text-red-600">{ordersError}</div>}
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Pedido Woo</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Factura</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado Woo</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado factura</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {!ordersLoading && orders.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-4 text-center text-sm text-gray-500">
                    No hay pedidos Woo vinculados todavía.
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr key={o.id}>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {o.woocommerce_order_number || o.woocommerce_order_id || '—'}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      <Link to="/invoices" className="text-blue-600 hover:underline">
                        {o.series}-{o.number}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">{o.woocommerce_status || '—'}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">{o.status}</td>
                    <td className="px-4 py-2 text-sm text-gray-500 text-right">{o.total}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'sync' && (
        <div className="bg-white shadow rounded-lg p-4 space-y-4">
          <p className="text-sm text-gray-600">
            Pegá un array JSON de productos Woo con campos sku, name, regular_price o price, y barcode opcional.
            Se upsertan por SKU del tenant.
          </p>
          <FormField label="JSON de productos">
            <textarea
              className={`${inputClass} font-mono text-sm min-h-[220px]`}
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
          </FormField>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
            Dry run (no escribe en la base)
          </label>
          {syncError && <div className="rounded-md bg-red-50 p-3 text-red-700 text-sm">{syncError}</div>}
          {syncResult && (
            <div className="rounded-md bg-emerald-50 p-3 text-emerald-800 text-sm">
              Sync {syncResult.dry_run ? '(dry run) ' : ''}completado — creados: {syncResult.created}, actualizados:{' '}
              {syncResult.updated}, omitidos: {syncResult.skipped}, total: {syncResult.total}
              {syncResult.detail ? ` — ${syncResult.detail}` : ''}
            </div>
          )}
          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {syncing ? 'Sincronizando...' : 'Sync catálogo'}
          </button>
        </div>
      )}

      {tab === 'stock' && (
        <div className="bg-white shadow rounded-lg p-4 space-y-4">
          <p className="text-sm text-gray-600">
            Calcula el stock Nexorux por SKU y lo empuja a WooCommerce (REST API). Configurá{' '}
            <code className="text-xs">WOOCOMMERCE_URL</code>, <code className="text-xs">WOOCOMMERCE_CONSUMER_KEY</code>{' '}
            y <code className="text-xs">WOOCOMMERCE_CONSUMER_SECRET</code> en el backend. Sin eso, podés exportar
            (dry run) igual.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Depósito (opcional — vacío = suma todos)">
              <select
                className={inputClass}
                value={stockWarehouseId}
                onChange={(e) => setStockWarehouseId(e.target.value)}
              >
                <option value="">Todos los depósitos</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </FormField>
            <div className="space-y-2 pt-6">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={stockDryRun}
                  onChange={(e) => setStockDryRun(e.target.checked)}
                />
                Dry run (solo calcular, no empujar)
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={stockPush}
                  disabled={stockDryRun}
                  onChange={(e) => setStockPush(e.target.checked)}
                />
                Empujar a Woo si hay API configurada
              </label>
            </div>
          </div>
          {stockError && <div className="rounded-md bg-red-50 p-3 text-red-700 text-sm">{stockError}</div>}
          {stockResult && (
            <div className="rounded-md bg-emerald-50 p-3 text-emerald-900 text-sm space-y-1">
              <div>
                Stock sync — total {stockResult.total}
                {stockResult.pushed
                  ? ` · actualizados ${stockResult.updated} · omitidos ${stockResult.skipped} · fallidos ${stockResult.failed}`
                  : ' · export solamente'}
                {stockResult.configured ? '' : ' · Woo API no configurada'}
              </div>
              {stockResult.detail && <div>{stockResult.detail}</div>}
            </div>
          )}
          {stockResult && stockResult.items.length > 0 && (
            <div className="overflow-auto max-h-80 border border-gray-200 rounded-md">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <tr>
                    <th className="px-3 py-2">SKU</th>
                    <th className="px-3 py-2">Producto</th>
                    <th className="px-3 py-2 text-right">Stock</th>
                  </tr>
                </thead>
                <tbody>
                  {stockResult.items.map((row) => (
                    <tr key={row.product_id} className="border-t border-gray-100">
                      <td className="px-3 py-2 font-mono text-xs">{row.sku}</td>
                      <td className="px-3 py-2">{row.name}</td>
                      <td className="px-3 py-2 text-right">{row.stock_quantity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <button
            type="button"
            onClick={handleStockSync}
            disabled={stockSyncing}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {stockSyncing ? 'Sincronizando stock...' : stockDryRun ? 'Calcular stock' : 'Sync stock → Woo'}
          </button>
        </div>
      )}
    </div>
  )
}

export default WooCommerce
