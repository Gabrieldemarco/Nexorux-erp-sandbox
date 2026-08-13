import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useEntityCrud } from '../hooks/useEntityCrud'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import {
  certificatesApi,
  CertificateCreate,
  CertificateResponse,
  CertificateUpdate,
} from '../services/certificates'

const defaultForm = {
  name: '',
  thumbprint: '',
  usage: 'signing',
  is_active: true,
  cert_path: '',
  key_path: '',
}

const Certificates = () => {
  const { user } = useAuth()
  const crud = useEntityCrud<CertificateResponse, CertificateCreate, CertificateUpdate>(
    certificatesApi,
    'No se pudieron cargar los certificados',
    '¿Eliminar este certificado?'
  )
  const [form, setForm] = useState(defaultForm)

  useEffect(() => {
    if (!crud.modalOpen) return
    if (crud.editing) {
      const meta = crud.editing.metadata || {}
      setForm({
        name: crud.editing.name,
        thumbprint: crud.editing.thumbprint,
        usage: crud.editing.usage || 'signing',
        is_active: crud.editing.is_active,
        cert_path: typeof meta.cert_path === 'string' ? meta.cert_path : '',
        key_path: typeof meta.key_path === 'string' ? meta.key_path : '',
      })
    } else {
      setForm(defaultForm)
    }
  }, [crud.modalOpen, crud.editing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    const metadata = {
      ...(form.cert_path ? { cert_path: form.cert_path } : {}),
      ...(form.key_path ? { key_path: form.key_path } : {}),
    }
    const payload = {
      name: form.name,
      thumbprint: form.thumbprint,
      usage: form.usage || undefined,
      is_active: form.is_active,
      metadata: Object.keys(metadata).length ? metadata : undefined,
    }
    const createData: CertificateCreate = {
      ...payload,
      tenant_id: user.tenant_id,
      company_id: user.company_id,
    }
    await crud.handleSave(createData, payload)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Certificados</h2>
        <button onClick={crud.openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar certificado
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {crud.loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {crud.error && <div className="p-4 text-red-600">{crud.error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thumbprint</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uso</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {crud.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                  No hay certificados cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              crud.items.map((cert) => (
                <tr key={cert.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{cert.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono text-xs">{cert.thumbprint}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cert.usage || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cert.is_active ? 'Activo' : 'Inactivo'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => crud.openEdit(cert)} className="text-blue-600 hover:text-blue-900 mr-4">
                      Editar
                    </button>
                    <button onClick={() => crud.handleDelete(cert.id)} className="text-red-600 hover:text-red-900">
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
        title={crud.editing ? 'Editar certificado' : 'Agregar certificado'}
        onClose={crud.closeModal}
        footer={
          <>
            <button type="button" onClick={crud.closeModal} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="certificate-form"
              disabled={crud.saving}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {crud.saving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {crud.modalError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{crud.modalError}</div>}
        <form id="certificate-form" onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Nombre">
            <input className={inputClass} required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </FormField>
          <FormField label="Thumbprint">
            <input
              className={inputClass}
              required
              value={form.thumbprint}
              onChange={(e) => setForm({ ...form, thumbprint: e.target.value })}
            />
          </FormField>
          <FormField label="Uso">
            <input className={inputClass} value={form.usage} onChange={(e) => setForm({ ...form, usage: e.target.value })} />
          </FormField>
          <FormField label="Ruta certificado (cert_path)">
            <input
              className={inputClass}
              value={form.cert_path}
              placeholder="/path/to/cert.pem"
              onChange={(e) => setForm({ ...form, cert_path: e.target.value })}
            />
          </FormField>
          <FormField label="Ruta clave (key_path)">
            <input
              className={inputClass}
              value={form.key_path}
              placeholder="/path/to/key.pem"
              onChange={(e) => setForm({ ...form, key_path: e.target.value })}
            />
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

export default Certificates
