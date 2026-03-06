import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { SectionHeader, ErrorBanner, LoadingSpinner } from '../components/ui'

export default function CreateRequest() {
  const navigate = useNavigate()
  const { batchId } = useParams()

  const [form, setForm] = useState({
    amount: '',
    currency: 'INR',
    beneficiaryName: '',
    beneficiaryAccount: '',
    purpose: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.amount || !form.currency || !form.beneficiaryName || !form.beneficiaryAccount || !form.purpose) {
      setError('All fields are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.post(
        `/batches/${batchId}/requests`,
        {
          amount: form.amount,
          currency: form.currency,
          beneficiaryName: form.beneficiaryName.trim(),
          beneficiaryAccount: form.beneficiaryAccount.trim(),
          purpose: form.purpose.trim(),
        },
        {
          headers: {
            'Idempotency-Key': `create-request-${batchId}-${Date.now()}`,
          },
        },
      )
      navigate(`/batches/${batchId}`)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in max-w-xl">
      <SectionHeader
        title="New Payment Request"
        subtitle="Add a payment request to this batch"
        action={
          <button className="btn-ghost" onClick={() => navigate(`/batches/${batchId}`)}>
            ← Back to Batch
          </button>
        }
      />

      <div className="card p-6">
        <ErrorBanner message={error} onDismiss={() => setError('')} />

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="form-group">
            <label className="label">Amount (numeric)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              className="input"
              value={form.amount}
              onChange={handleChange('amount')}
              placeholder="e.g. 1000.00"
            />
          </div>

          <div className="form-group">
            <label className="label">Currency</label>
            <input
              type="text"
              className="input"
              value={form.currency}
              onChange={handleChange('currency')}
              placeholder="INR"
              maxLength={3}
            />
          </div>

          <div className="form-group">
            <label className="label">Beneficiary Name</label>
            <input
              type="text"
              className="input"
              value={form.beneficiaryName}
              onChange={handleChange('beneficiaryName')}
              placeholder="Legal beneficiary name"
            />
          </div>

          <div className="form-group">
            <label className="label">Beneficiary Account</label>
            <input
              type="text"
              className="input"
              value={form.beneficiaryAccount}
              onChange={handleChange('beneficiaryAccount')}
              placeholder="Account number / identifier"
            />
          </div>

          <div className="form-group">
            <label className="label">Purpose</label>
            <textarea
              className="input resize-none"
              rows={3}
              value={form.purpose}
              onChange={handleChange('purpose')}
              placeholder="Describe the reason for this payment"
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate(`/batches/${batchId}`)}
              disabled={loading}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <LoadingSpinner size="sm" /> Creating…
                </>
              ) : (
                'Create Request'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

