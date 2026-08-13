import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import { productsApi, ProductCreate, ProductResponse, ProductUpdate } from '../services/products'

const defaultForm = {
  name: '',
  sku: '',
  barcode: '',
  sales_price: 0,
  cost_price: 0,
  tax_rate: 22,
  product_type: 'good',
  unit_of_measure: 'unit',
  is_active: true,
}

const Products = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<ProductResponse, ProductCreate, ProductUpdate>(
    productsApi,
    'No se pudieron cargar los productos',
    '¿Eliminar este producto?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        name: crud.editing.name,
        sku: crud.editing.sku,
        barcode: crud.editing.barcode || '',
        sales_price: crud.editing.sales_price,
        cost_price: crud.editing.cost_price,
        tax_rate: crud.editing.tax_rate,
        product_type: crud.editing.product_type,
        unit_of_measure: crud.editing.unit_of_measure,
        is_active: crud.editing.is_active,
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const updateData: ProductUpdate = {
      ...form,
      barcode: form.barcode || undefined,
    }
    const createData: ProductCreate = {
      ...form,
      barcode: form.barcode || undefined,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, updateData)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Productos</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar producto
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cód. barras</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Impuesto</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No hay productos cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((product) => (
                <tr key={product.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.sku}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.barcode || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.sales_price}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.tax_rate}%</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(product)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(product.id)} className="text-red-600 hover:text-red-900">
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
        open={crud.modalOpen}
        title={crud.editing ? 'Editar producto' : 'Agregar producto'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="product-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="product-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="SKU">
            <input className={inputClass} required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
          </FormField>
          <FormField label="Código de barras">
            <input
              className={inputClass}
              value={form.barcode}
              placeholder="EAN / UPC / interno"
              onChange={(e) => setForm({ ...form, barcode: e.target.value })}
            />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Precio venta">
              <input className={inputClass} type="number" step="0.01" required value={form.sales_price} onChange={(e) => setForm({ ...form, sales_price: Number(e.target.value) })} />
            </FormField>
            <FormField label="Costo">
              <input className={inputClass} type="number" step="0.01" required value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: Number(e.target.value) })} />
            </FormField>
          </div>
          <FormField label="Impuesto (%)">
            <input className={inputClass} type="number" step="0.01" value={form.tax_rate} onChange={(e) => setForm({ ...form, tax_rate: Number(e.target.value) })} />
          </FormField>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Activo
          </label>
        </form>
      </Modal>
    </div>
  )
}

export default Products
