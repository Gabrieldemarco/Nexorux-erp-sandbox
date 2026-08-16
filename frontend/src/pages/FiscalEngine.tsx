import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import Modal from '../components/Modal'

interface FiscalEngine {
  engine_id: string
  engine_name: string
  country: string
  fiscal_authority: string
  version: string
  supports_electronic_invoice: boolean
  supports_credit_note: boolean
  supports_debit_note: boolean
  supports_contingency: boolean
  supports_cancellation: boolean
  supports_query_status: boolean
  supported_document_types: string[]
}

interface TenantConfig {
  fiscal_engine_id: string
  fiscal_config: Record<string, any>
}

const FiscalEngine = () => {
  const { user } = useAuth()
  const [engines, setEngines] = useState<FiscalEngine[]>([])
  const [currentConfig, setCurrentConfig] = useState<TenantConfig | null>(null)
  const [selectedEngine, setSelectedEngine] = useState<string>('')
  const [environment, setEnvironment] = useState<string>('testing')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadAvailableEngines()
    loadCurrentConfig()
  }, [])

  const loadAvailableEngines = async () => {
    try {
      // En una implementación real, esto vendría de un endpoint del backend
      // Por ahora simulo los motores disponibles
      const mockEngines: FiscalEngine[] = [
        {
          engine_id: 'dgi_uruguay',
          engine_name: 'DGI Uruguay Engine',
          country: 'UY',
          fiscal_authority: 'Dirección General Impositiva',
          version: '1.0',
          supports_electronic_invoice: true,
          supports_credit_note: true,
          supports_debit_note: true,
          supports_contingency: true,
          supports_cancellation: false,
          supports_query_status: true,
          supported_document_types: ['111', '101', '112', '113', '102', '103', '201', '202', '203', '211', '212', '213']
        },
        {
          engine_id: 'mock_fiscal',
          engine_name: 'Mock Fiscal Authority',
          country: 'XX',
          fiscal_authority: 'MockFiscal Authority',
          version: '1.0',
          supports_electronic_invoice: true,
          supports_credit_note: true,
          supports_debit_note: true,
          supports_contingency: true,
          supports_cancellation: true,
          supports_query_status: true,
          supported_document_types: ['invoice', 'credit_note', 'debit_note', 'contingency_invoice']
        }
      ]
      setEngines(mockEngines)
    } catch (error) {
      console.error('Error loading engines:', error)
      setMessage({ type: 'error', text: 'Error al cargar motores fiscales disponibles' })
    } finally {
      setLoading(false)
    }
  }

  const loadCurrentConfig = async () => {
    try {
      // En una implementación real, esto vendría de un endpoint del backend
      // Por ahora simulo la configuración actual
      const mockConfig: TenantConfig = {
        fiscal_engine_id: 'dgi_uruguay',
        fiscal_config: { environment: 'testing' }
      }
      setCurrentConfig(mockConfig)
      setSelectedEngine(mockConfig.fiscal_engine_id)
      setEnvironment(mockConfig.fiscal_config.environment || 'testing')
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      // En una implementación real, esto enviaría la configuración al backend
      // Por ahora simulo el guardado exitoso
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setCurrentConfig({
        fiscal_engine_id: selectedEngine,
        fiscal_config: { environment }
      })
      
      setMessage({ type: 'success', text: 'Motor fiscal actualizado exitosamente' })
      setShowModal(false)
    } catch (error) {
      console.error('Error saving config:', error)
      setMessage({ type: 'error', text: 'Error al actualizar el motor fiscal' })
    } finally {
      setSaving(false)
    }
  }

  const handleOpenModal = () => {
    if (currentConfig) {
      setSelectedEngine(currentConfig.fiscal_engine_id)
      setEnvironment(currentConfig.fiscal_config.environment || 'testing')
    }
    setShowModal(true)
  }

  const getEngineInfo = (engineId: string) => {
    return engines.find(e => e.engine_id === engineId)
  }

  const currentEngine = currentConfig ? getEngineInfo(currentConfig.fiscal_engine_id) : null

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-[#0A2463]"></div>
          <p className="text-sm text-slate-600">Cargando motores fiscales...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#0A2463]">Motor Fiscal</h1>
          <p className="text-sm text-slate-600">Configuración del motor fiscal para el tenant actual</p>
        </div>
        <button
          onClick={handleOpenModal}
          className="rounded-lg bg-[#0A2463] px-4 py-2 text-sm font-medium text-white hover:bg-[#1E293B] transition-colors"
        >
          Cambiar Motor
        </button>
      </div>

      {message && (
        <div
          className={`rounded-lg px-4 py-3 ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Configuración Actual */}
      {currentEngine && (
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-[#0A2463]">Configuración Actual</h2>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Motor</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium">
                  {currentEngine.engine_name}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">ID del Motor</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  {currentEngine.fiscal_engine_id}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">País</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  {currentEngine.country}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Autoridad Fiscal</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  {currentEngine.fiscal_authority}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Versión</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  {currentEngine.version}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-500">Entorno</label>
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  {currentConfig?.fiscal_config.environment || 'testing'}
                </div>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-slate-500">Capacidades</label>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_electronic_invoice ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_electronic_invoice ? '✓' : '✗'}
                  </span>
                  <span>Factura electrónica</span>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_credit_note ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_credit_note ? '✓' : '✗'}
                  </span>
                  <span>Notas de crédito</span>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_debit_note ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_debit_note ? '✓' : '✗'}
                  </span>
                  <span>Notas de débito</span>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_contingency ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_contingency ? '✓' : '✗'}
                  </span>
                  <span>Contingencia</span>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_cancellation ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_cancellation ? '✓' : '✗'}
                  </span>
                  <span>Cancelación</span>
                </div>
                <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                  <span className={currentEngine.supports_query_status ? 'text-green-600' : 'text-slate-400'}>
                    {currentEngine.supports_query_status ? '✓' : '✗'}
                  </span>
                  <span>Consulta estado</span>
                </div>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium text-slate-500">Documentos Soportados</label>
              <div className="flex flex-wrap gap-2">
                {currentEngine.supported_document_types.map((docType) => (
                  <span
                    key={docType}
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs"
                  >
                    {docType}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Motores Disponibles */}
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-[#0A2463]">Motores Disponibles</h2>
        
        <div className="grid gap-4 md:grid-cols-2">
          {engines.map((engine) => (
            <div
              key={engine.engine_id}
              className={`rounded-lg border p-4 transition-colors ${
                currentConfig?.fiscal_engine_id === engine.engine_id
                  ? 'border-[#0A2463] bg-[#0A2463]/5'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="mb-2 flex items-center justify-between">
                <h3 className="font-semibold text-[#0A2463]">{engine.engine_name}</h3>
                {currentConfig?.fiscal_engine_id === engine.engine_id && (
                  <span className="rounded-full bg-[#0A2463] px-2 py-1 text-xs font-medium text-white">
                    Activo
                  </span>
                )}
              </div>
              <div className="mb-3 space-y-1 text-xs text-slate-600">
                <div><span className="font-medium">País:</span> {engine.country}</div>
                <div><span className="font-medium">Autoridad:</span> {engine.fiscal_authority}</div>
                <div><span className="font-medium">Versión:</span> {engine.version}</div>
              </div>
              <div className="flex flex-wrap gap-1">
                {engine.supports_electronic_invoice && (
                  <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800">Facturación electrónica</span>
                )}
                {engine.supports_credit_note && (
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800">Notas de crédito</span>
                )}
                {engine.supports_contingency && (
                  <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800">Contingencia</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal de Cambio de Motor */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Cambiar Motor Fiscal"
      >
        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Seleccionar Motor</label>
            <select
              value={selectedEngine}
              onChange={(e) => setSelectedEngine(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-[#0A2463] focus:outline-none focus:ring-1 focus:ring-[#0A2463]"
            >
              {engines.map((engine) => (
                <option key={engine.engine_id} value={engine.engine_id}>
                  {engine.engine_name} ({engine.engine_id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Entorno</label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-[#0A2463] focus:outline-none focus:ring-1 focus:ring-[#0A2463]"
            >
              <option value="testing">Testing (Pruebas)</option>
              <option value="homologacion">Homologación</option>
              <option value="produccion">Producción</option>
            </select>
          </div>

          {selectedEngine && (
            <div className="rounded-md bg-slate-50 p-3">
              <p className="mb-2 text-sm font-medium text-slate-700">Información del Motor Seleccionado:</p>
              {(() => {
                const engine = getEngineInfo(selectedEngine)
                return engine ? (
                  <div className="space-y-1 text-xs text-slate-600">
                    <div><span className="font-medium">Nombre:</span> {engine.engine_name}</div>
                    <div><span className="font-medium">País:</span> {engine.country}</div>
                    <div><span className="font-medium">Autoridad:</span> {engine.fiscal_authority}</div>
                  </div>
                ) : null
              })()}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={() => setShowModal(false)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-[#0A2463] px-4 py-2 text-sm font-medium text-white hover:bg-[#1E293B] transition-colors disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default FiscalEngine