import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import { suppliersApi, SupplierCreate, SupplierResponse, SupplierUpdate } from '../services/suppliers'
import { useCatalog } from '../hooks/useCatalog'

const defaultForm = {
  legal_name: '',
  trade_name: '',
  rut: '',
  email: '',
  phone: '',
  currency: '',
  is_active: true,
}

const Suppliers = () => {
  const { user } = useAuth()
  const { currency: companyCurrency } = useCatalog()
  const crud = useEntityCrud<SupplierResponse, SupplierCreate, SupplierUpdate>(
    suppliersApi,
    'No se pudieron cargar los proveedores',
    '¿Eliminar este proveedor?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      setForm({
        legal_name: crud.editing.legal_name,
        trade_name: crud.editing.trade_name ?? '',
        rut: crud.editing.rut,
        email: crud.editing.email ?? '',
        phone: crud.editing.phone ?? '',
        currency: crud.editing.currency,
        is_active: crud.editing.is_active,
      })
    } else {
      setForm({ ...defaultForm, currency: companyCurrency })
    }
  }, [crud.modalOpen, crud.editing, companyCurrency])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const payload = {
      ...form,
      trade_name: form.trade_name || undefined,
      email: form.email || undefined,
      phone: form.phone || undefined,
    }
    const createData: SupplierCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Proveedores</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar proveedor
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">RUT</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Moneda</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay proveedores cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((supplier) => (
                <EntityListRow
                  key={supplier.id}
                  onOpen={() => crud.openEdit(supplier)}
                  actions={
                    <>
                      <button type="button" onClick={() => crud.openEdit(supplier)} className="text-blue-600 hover:text-blue-900 mr-4">
                        Abrir
                      </button>
                      <button type="button" onClick={() => crud.handleDelete(supplier.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{supplier.legal_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{supplier.rut}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{supplier.email || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{supplier.currency}</td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={crud.modalOpen}
        title={crud.editing ? `Proveedor · ${crud.editing.legal_name}` : 'Agregar proveedor'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button type="submit" form="supplier-form" disabled={crud.saving} className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="supplier-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre legal">
            <input className={inputClass} required value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} />
          </FormField>
          <FormField label="Nombre comercial">
            <input className={inputClass} value={form.trade_name} onChange={(e) => setForm({ ...form, trade_name: e.target.value })} />
          </FormField>
          <FormField label="RUT">
            <input className={inputClass} required value={form.rut} onChange={(e) => setForm({ ...form, rut: e.target.value })} />
          </FormField>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Email">
              <input className={inputClass} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </FormField>
            <FormField label="Teléfono">
              <input className={inputClass} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </FormField>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Activo
          </label>
        </form>
      </Modal>
    </div>
  )
}

export default Suppliers
