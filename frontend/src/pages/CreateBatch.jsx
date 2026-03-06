import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { ErrorBanner } from '../components/ui'
import { CreateBatch as SheetCreateBatch } from '../nexus-shell/components/Finance/CreateBatch'
import { SUBCONTRACTORS, VENDORS } from '../nexus-shell/constants'
import { getRole } from '../utils/auth'

const mapBackendRoleToUiRole = (role) => {
  switch (role) {
    case 'ADMIN': return 'Admin'
    case 'CREATOR': return 'Creator'
    case 'APPROVER': return 'Approver'
    case 'VIEWER': return 'Viewer'
    default: return 'Viewer'
  }
}

const generateBatchName = (type) => {
  const now = new Date()
  const d = String(now.getDate()).padStart(2, '0')
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const y = String(now.getFullYear()).slice(-2)
  return `#${type}_${d}${m}${y}`
}

export default function CreateBatch() {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [typeModalOpen, setTypeModalOpen] = useState(true)
  const [batchName, setBatchName] = useState('')

  const uiRole = mapBackendRoleToUiRole(getRole())

  const handleSelectType = (type) => {
    setBatchName(generateBatchName(type))
    setTypeModalOpen(false)
  }

  const handleFinalize = async ({ name, rows }) => {
    if (!rows || rows.length === 0) {
      navigate('/batches')
      return
    }
    setLoading(true)
    setError('')
    try {
      const title = name || batchName || generateBatchName('K')
      const batchRes = await api.post(
        '/batches',
        { title },
        { headers: { 'Idempotency-Key': `create-batch-${title}-${Date.now()}` } },
      )
      const batchId = batchRes.data.data.id

      for (const row of rows) {
        const amount = Number(row.amount || 0) + Number(row.additional || 0)
        if (!row.partyName || amount <= 0) continue
        await api.post(
          `/batches/${batchId}/requests`,
          {
            amount: amount.toFixed(2),
            currency: 'INR',
            beneficiaryName: row.partyName,
            beneficiaryAccount: 'AUTO',
            purpose: row.remarks || title,
          },
          {
            headers: {
              'Idempotency-Key': `create-req-${batchId}-${row.id}`,
            },
          },
        )
      }

      navigate(`/batches/${batchId}`)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex-1">
      <div className="max-w-6xl mx-auto pt-6 px-6">
        <button className="btn-ghost mb-4" onClick={() => navigate('/batches')}>
          ← Back to Batches
        </button>
        <ErrorBanner message={error} onDismiss={() => setError('')} />
        {batchName && (
          <SheetCreateBatch
            onCancel={() => navigate('/batches')}
            onSave={handleFinalize}
            isViewMode={false}
            batchId={batchName}
            status="OPEN"
            role={uiRole}
            subcontractors={SUBCONTRACTORS}
            vendors={VENDORS}
            isSidebarCollapsed={false}
          />
        )}
      </div>

      {typeModalOpen && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6">
          <div
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={() => navigate('/batches')}
          />
          <div className="relative bg-white w-full max-w-md rounded-[2.5rem] shadow-2xl p-10">
            <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-2 text-center">
              Create New Batch
            </h3>
            <p className="text-slate-500 font-medium text-sm mb-8 text-center px-4">
              Select the type of financial batch you wish to initialize.
            </p>
            <div className="grid grid-cols-1 gap-4">
              <button
                onClick={() => handleSelectType('K')}
                className="group flex items-center justify-between p-5 bg-slate-50 border border-slate-200 rounded-2xl hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
                disabled={loading}
              >
                <div>
                  <p className="font-black text-slate-800 tracking-tight text-lg">Kharchi Request</p>
                  <p className="text-xs font-medium text-slate-500 mt-1">
                    Petty cash and site maintenance
                  </p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
              </button>
              <button
                onClick={() => handleSelectType('P')}
                className="group flex items-center justify-between p-5 bg-slate-50 border border-slate-200 rounded-2xl hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
                disabled={loading}
              >
                <div>
                  <p className="font-black text-slate-800 tracking-tight text-lg">Monthly Payment</p>
                  <p className="text-xs font-medium text-slate-500 mt-1">
                    Vendor payouts and salary batches
                  </p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-10V4m-5 0V4h5M9 21h6"
                    />
                  </svg>
                </div>
              </button>
            </div>
            <button
              onClick={() => navigate('/batches')}
              className="mt-6 w-full py-3 text-sm font-bold text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-widest"
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

