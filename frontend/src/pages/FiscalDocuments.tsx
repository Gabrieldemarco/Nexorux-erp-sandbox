import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'
import Modal from '../components/Modal'
import FormField, { inputClass } from '../components/FormField'
import EntityListRow from '../components/EntityListRow'
import {
  fiscalDocumentsApi,
  FiscalDocumentCreate,
  FiscalDocumentResponse,
} from '../services/fiscalDocuments'
import { invoicesApi, InvoiceResponse } from '../services/invoices'
import { certificatesApi, CertificateResponse } from '../services/certificates'
import { DOCUMENT_TYPE_OPTIONS, documentTypeLabel } from '../utils/documentTypes'
import { fiscalStateLabel } from '../utils/statusLabels'
import { useCatalog } from '../hooks/useCatalog'
import { documentTypeLabelFromCatalog, fiscalStateLabel as catalogFiscalStateLabel } from '../services/catalog'

const defaultForm = {
  invoice_id: '',
  document_type: '',
  series: 'A',
  number: '',
  is_contingency: false,
}

const FiscalDocuments = () => {
  const { user } = useAuth()
  const { catalog } = useCatalog()
  const typeLabel = (code: string) =>
    catalog ? documentTypeLabelFromCatalog(catalog, code) : documentTypeLabel(code)
  const stateLabel = (code?: string | null) =>
    catalog ? catalogFiscalStateLabel(catalog, code) : fiscalStateLabel(code)
  const documentTypes = catalog?.document_types?.length ? catalog.document_types : [...DOCUMENT_TYPE_OPTIONS]
  const [docs, setDocs] = useState<FiscalDocumentResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const [createOpen, setCreateOpen] = useState(false)
  const [createSaving, setCreateSaving] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [form, setForm] = useState(defaultForm)
  const [invoices, setInvoices] = useState<InvoiceResponse[]>([])
  const [refsLoading, setRefsLoading] = useState(false)

  const [issueOpen, setIssueOpen] = useState(false)
  const [issueDocId, setIssueDocId] = useState<string | null>(null)
  const [certificateId, setCertificateId] = useState('')
  const [certificates, setCertificates] = useState<CertificateResponse[]>([])
  const [issueError, setIssueError] = useState<string | null>(null)

  const [detailDoc, setDetailDoc] = useState<FiscalDocumentResponse | null>(null)

  const loadDocs = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fiscalDocumentsApi.list()
      setDocs(data)
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudieron cargar los documentos fiscales'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocs()
  }, [])

  useEffect(() => {
    if (!createOpen) return
    const loadRefs = async () => {
      setRefsLoading(true)
      try {
        const data = await invoicesApi.list()
        setInvoices(data)
        if (!form.invoice_id && data[0]) {
          setForm((prev) => ({
            ...prev,
            invoice_id: data[0].id,
            document_type: data[0].document_type,
            series: data[0].series,
            number: data[0].number,
          }))
        }
      } finally {
        setRefsLoading(false)
      }
    }
    loadRefs()
  }, [createOpen, form.invoice_id])

  const handleInvoiceChange = (invoiceId: string) => {
    const invoice = invoices.find((i) => i.id === invoiceId)
    setForm({
      ...form,
      invoice_id: invoiceId,
      document_type: invoice?.document_type ?? form.document_type,
      series: invoice?.series ?? form.series,
      number: invoice?.number ?? form.number,
    })
  }

  const openCreate = () => {
    setForm(defaultForm)
    setCreateError(null)
    setCreateOpen(true)
  }

  const closeCreate = () => {
    setCreateOpen(false)
    setCreateError(null)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    setCreateSaving(true)
    setCreateError(null)
    try {
      const invoice = invoices.find((i) => i.id === form.invoice_id)
      const payload: FiscalDocumentCreate = {
        tenant_id: user.tenant_id,
        company_id: invoice?.company_id || user.company_id,
        invoice_id: form.invoice_id,
        document_type: form.document_type,
        series: form.series,
        number: form.number,
        state: 'draft',
        is_contingency: form.is_contingency,
      }
      await fiscalDocumentsApi.create(payload)
      closeCreate()
      await loadDocs()
    } catch (err) {
      setCreateError(getErrorMessage(err, 'No se pudo crear el documento fiscal'))
    } finally {
      setCreateSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Eliminar este documento fiscal?')) return
    setActionLoading(id)
    setError(null)
    try {
      await fiscalDocumentsApi.delete(id)
      await loadDocs()
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudo eliminar el documento fiscal'))
    } finally {
      setActionLoading(null)
    }
  }

  const openIssue = async (id: string) => {
    setIssueDocId(id)
    setIssueError(null)
    setCertificateId('')
    setIssueOpen(true)
    try {
      const certs = await certificatesApi.list()
      setCertificates(certs.filter((c) => c.is_active))
      if (certs[0]) setCertificateId(certs[0].id)
    } catch (err) {
      setIssueError(getErrorMessage(err, 'No se pudieron cargar los certificados'))
    }
  }

  const closeIssue = () => {
    setIssueOpen(false)
    setIssueDocId(null)
    setIssueError(null)
  }

  const handleIssue = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issueDocId || !certificateId) return
    setActionLoading(issueDocId)
    setIssueError(null)
    try {
      await fiscalDocumentsApi.issue(issueDocId, { certificate_id: certificateId })
      closeIssue()
      await loadDocs()
    } catch (err) {
      setIssueError(getErrorMessage(err, 'No se pudo emitir el documento fiscal'))
    } finally {
      setActionLoading(null)
    }
  }

  const handleSend = async (id: string) => {
    setActionLoading(id)
    setError(null)
    try {
      await fiscalDocumentsApi.send(id, { environment: 'testing' })
      await loadDocs()
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudo enviar el documento fiscal'))
    } finally {
      setActionLoading(null)
    }
  }

  const handleQuery = async (id: string) => {
    setActionLoading(id)
    setError(null)
    try {
      await fiscalDocumentsApi.queryStatus(id, 'testing')
      await loadDocs()
    } catch (err) {
      setError(getErrorMessage(err, 'No se pudo consultar el estado del documento fiscal'))
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Documentos fiscales</h2>
          <p className="mt-1 text-sm text-gray-500">Hacé click en un registro para ver el detalle fiscal.</p>
        </div>
        <button onClick={openCreate} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Agregar documento fiscal
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading && <div className="p-4 text-gray-500">Cargando...</div>}
        {error && <div className="p-4 text-red-600">{error}</div>}
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documento</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Emitido el</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {docs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                  No hay documentos fiscales cargados. Creá el primero para empezar.
                </td>
              </tr>
            ) : (
              docs.map((doc) => (
                <EntityListRow
                  key={doc.id}
                  onOpen={() => setDetailDoc(doc)}
                  actions={
                    <>
                      <button
                        type="button"
                        className="text-slate-700 hover:text-slate-900 mr-3"
                        onClick={() => setDetailDoc(doc)}
                      >
                        Abrir
                      </button>
                      <button
                        type="button"
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        onClick={() => openIssue(doc.id)}
                        disabled={actionLoading === doc.id}
                      >
                        Emitir
                      </button>
                      <button
                        type="button"
                        className="text-green-600 hover:text-green-900 mr-3"
                        onClick={() => handleSend(doc.id)}
                        disabled={actionLoading === doc.id}
                      >
                        Enviar
                      </button>
                      <button
                        type="button"
                        className="text-purple-600 hover:text-purple-900 mr-3"
                        onClick={() => handleQuery(doc.id)}
                        disabled={actionLoading === doc.id}
                      >
                        Consultar
                      </button>
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-900"
                        onClick={() => handleDelete(doc.id)}
                        disabled={actionLoading === doc.id}
                      >
                        Eliminar
                      </button>
                    </>
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {typeLabel(doc.document_type)} {doc.series}-{doc.number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stateLabel(doc.state)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {doc.issued_at ? new Date(doc.issued_at).toLocaleDateString() : '-'}
                  </td>
                </EntityListRow>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        open={createOpen}
        title="Agregar documento fiscal"
        onClose={closeCreate}
        footer={
          <>
            <button type="button" onClick={closeCreate} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="fiscal-create-form"
              disabled={createSaving || refsLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createSaving ? 'Guardando...' : 'Guardar'}
            </button>
          </>
        }
      >
        {createError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{createError}</div>}
        {refsLoading ? (
          <div className="text-gray-500">Cargando facturas...</div>
        ) : (
          <form id="fiscal-create-form" onSubmit={handleCreate} className="space-y-4">
            <FormField label="Factura">
              <select
                className={inputClass}
                required
                value={form.invoice_id}
                onChange={(e) => handleInvoiceChange(e.target.value)}
              >
                <option value="">Seleccionar factura</option>
                {invoices.map((inv) => (
                  <option key={inv.id} value={inv.id}>
                    {inv.series}-{inv.number} ({typeLabel(inv.document_type)})
                  </option>
                ))}
              </select>
            </FormField>
            <FormField label="Tipo documento">
              <select
                className={inputClass}
                value={form.document_type}
                onChange={(e) => setForm({ ...form, document_type: e.target.value })}
              >
                {documentTypes.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </FormField>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Serie">
                <input className={inputClass} required value={form.series} onChange={(e) => setForm({ ...form, series: e.target.value })} />
              </FormField>
              <FormField label="Número">
                <input className={inputClass} required value={form.number} onChange={(e) => setForm({ ...form, number: e.target.value })} />
              </FormField>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.is_contingency}
                onChange={(e) => setForm({ ...form, is_contingency: e.target.checked })}
              />
              Contingencia
            </label>
          </form>
        )}
      </Modal>

      <Modal
        open={issueOpen}
        title="Emitir documento fiscal"
        onClose={closeIssue}
        footer={
          <>
            <button type="button" onClick={closeIssue} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
              Cancelar
            </button>
            <button
              type="submit"
              form="fiscal-issue-form"
              disabled={!certificateId || actionLoading === issueDocId}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {actionLoading === issueDocId ? 'Emitiendo...' : 'Emitir'}
            </button>
          </>
        }
      >
        {issueError && <div className="mb-4 rounded-md bg-red-50 p-3 text-red-700 text-sm">{issueError}</div>}
        <form id="fiscal-issue-form" onSubmit={handleIssue} className="space-y-4">
          <FormField label="Certificado digital">
            <select
              className={inputClass}
              required
              value={certificateId}
              onChange={(e) => setCertificateId(e.target.value)}
            >
              <option value="">Seleccionar certificado</option>
              {certificates.map((cert) => (
                <option key={cert.id} value={cert.id}>
                  {cert.name} ({cert.thumbprint})
                </option>
              ))}
            </select>
          </FormField>
          {certificates.length === 0 && (
            <p className="text-sm text-amber-600">No hay certificados activos. Creá uno antes de emitir.</p>
          )}
        </form>
      </Modal>

      <Modal
        open={!!detailDoc}
        title={
          detailDoc
            ? `Fiscal · ${typeLabel(detailDoc.document_type)} ${detailDoc.series}-${detailDoc.number}`
            : 'Detalle fiscal'
        }
        onClose={() => setDetailDoc(null)}
        size="xl"
        footer={
          detailDoc ? (
            <>
              <button
                type="button"
                onClick={() => setDetailDoc(null)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cerrar
              </button>
              <button
                type="button"
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                onClick={() => {
                  const id = detailDoc.id
                  setDetailDoc(null)
                  openIssue(id)
                }}
              >
                Emitir
              </button>
            </>
          ) : undefined
        }
      >
        {detailDoc && (
          <div className="space-y-4 text-sm">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Estado</div>
                <div className="mt-0.5 font-medium text-slate-900">{stateLabel(detailDoc.state)}</div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Tipo</div>
                <div className="mt-0.5 font-medium text-slate-900">{typeLabel(detailDoc.document_type)}</div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Serie / Número</div>
                <div className="mt-0.5 font-medium text-slate-900">
                  {detailDoc.series}-{detailDoc.number}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Contingencia</div>
                <div className="mt-0.5 font-medium text-slate-900">{detailDoc.is_contingency ? 'Sí' : 'No'}</div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Emitido</div>
                <div className="mt-0.5 text-slate-700">
                  {detailDoc.issued_at ? new Date(detailDoc.issued_at).toLocaleString('es-UY') : '—'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Firmado</div>
                <div className="mt-0.5 text-slate-700">
                  {detailDoc.signed_at ? new Date(detailDoc.signed_at).toLocaleString('es-UY') : '—'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Enviado</div>
                <div className="mt-0.5 text-slate-700">
                  {detailDoc.sent_at ? new Date(detailDoc.sent_at).toLocaleString('es-UY') : '—'}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Respuesta</div>
                <div className="mt-0.5 text-slate-700">
                  {detailDoc.response_at ? new Date(detailDoc.response_at).toLocaleString('es-UY') : '—'}
                </div>
              </div>
            </div>
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Factura vinculada</div>
              <div className="mt-0.5 break-all font-mono text-xs text-slate-600">{detailDoc.invoice_id}</div>
            </div>
            {detailDoc.xml_reference && (
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-400">Referencia XML</div>
                <div className="mt-0.5 break-all text-slate-700">{detailDoc.xml_reference}</div>
              </div>
            )}
            {detailDoc.raw_payload && Object.keys(detailDoc.raw_payload).length > 0 && (
              <div>
                <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">Payload</div>
                <pre className="max-h-48 overflow-auto rounded-md bg-slate-50 p-3 text-[11px] text-slate-700">
                  {JSON.stringify(detailDoc.raw_payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default FiscalDocuments
