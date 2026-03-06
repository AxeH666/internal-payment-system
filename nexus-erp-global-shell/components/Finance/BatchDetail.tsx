
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Role } from '../../types';

interface PaymentRequest {
  id: string;
  partyName: string;
  description: string;
  requestedAmount: number;
  approvedAmount: number;
  status: 'PENDING' | 'APPROVED' | 'HOLD' | 'PARTIAL' | 'PAID';
  remarks: string;
}

interface BatchDetailProps {
  batchId: string;
  role: Role;
  onBack: () => void;
}

type BatchStatus = 'OPEN' | 'PENDING' | 'APPROVED' | 'CLOSED' | 'CANCELLED';

const RowActionDropdown: React.FC<{
  onAction: (type: 'APPROVE' | 'HOLD' | 'PARTIAL') => void;
  disabled?: boolean;
}> = ({ onAction, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (disabled) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 text-slate-400 hover:text-blue-600 transition-all"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h.01M12 12h.01M19 12h.01" /></svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 top-7 w-40 bg-white border border-slate-200 shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
          <button onClick={() => { onAction('APPROVE'); setIsOpen(false); }} className="w-full text-left px-3 py-1.5 text-[10px] font-bold text-emerald-600 hover:bg-slate-50 uppercase tracking-wider">Approve Full</button>
          <button onClick={() => { onAction('PARTIAL'); setIsOpen(false); }} className="w-full text-left px-3 py-1.5 text-[10px] font-bold text-purple-600 hover:bg-slate-50 uppercase tracking-wider">Partial Pay</button>
          <button onClick={() => { onAction('HOLD'); setIsOpen(false); }} className="w-full text-left px-3 py-1.5 text-[10px] font-bold text-rose-600 hover:bg-slate-50 uppercase tracking-wider">Hold</button>
        </div>
      )}
    </div>
  );
};

export const BatchDetail: React.FC<BatchDetailProps> = ({ batchId, role, onBack }) => {
  const [currentBatchStatus, setCurrentBatchStatus] = useState<BatchStatus>('OPEN');
  const [isStatusMenuOpen, setIsStatusMenuOpen] = useState(false);
  const statusMenuRef = useRef<HTMLDivElement>(null);

  const [requests, setRequests] = useState<PaymentRequest[]>([
    { id: 'REQ-421', partyName: 'Modern Buildcon Pvt Ltd', description: 'Monthly rent for tower crane - Site GUR', requestedAmount: 125000, approvedAmount: 0, status: 'PENDING', remarks: '' },
    { id: 'REQ-422', partyName: 'Swift Logistics Solutions', description: 'Diesel supply for DG sets (Batch 42)', requestedAmount: 45000, approvedAmount: 45000, status: 'APPROVED', remarks: 'Standard rates applied' },
    { id: 'REQ-423', partyName: 'Global Manpower Services', description: 'Skilled labor payment - Sep 2025', requestedAmount: 210000, approvedAmount: 0, status: 'HOLD', remarks: 'Awaiting site attendance verification' },
    { id: 'REQ-424', partyName: 'Aggarwal Hardware & Tools', description: 'Safety gear and tool kits', requestedAmount: 35000, approvedAmount: 25000, status: 'PARTIAL', remarks: 'Pending quality check for 10 units' },
    { id: 'REQ-425', partyName: 'Precision Engineering', description: 'Structural fabrication works', requestedAmount: 550000, approvedAmount: 550000, status: 'PAID', remarks: 'Transaction ref: BANK_9921' },
  ]);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<{ type: 'APPROVE' | 'HOLD' | 'PARTIAL', targetIds: string[] } | null>(null);
  const [modalRemark, setModalRemark] = useState('');
  const [partialAmount, setPartialAmount] = useState<number>(0);

  const canCreate = role === 'Admin' || role === 'Creator';
  const canApprove = role === 'Admin' || role === 'Approver';
  const isReadOnly = role === 'Viewer' || role === 'Creator';

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (statusMenuRef.current && !statusMenuRef.current.contains(event.target as Node)) {
        setIsStatusMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val).replace('₹', '₹ ');
  };

  const totals = useMemo(() => {
    return requests.reduce((acc, req) => {
      acc.requested += req.requestedAmount;
      acc.approved += req.approvedAmount;
      if (req.status === 'PENDING' || req.status === 'PARTIAL') acc.pending += (req.requestedAmount - req.approvedAmount);
      if (req.status === 'HOLD') acc.onHold += req.requestedAmount;
      return acc;
    }, { requested: 0, approved: 0, pending: 0, onHold: 0 });
  }, [requests]);

  const toggleSelect = (id: string, status: string) => {
    if (isReadOnly || status === 'APPROVED' || status === 'PAID') return;
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    const selectable = requests.filter(r => r.status === 'PENDING' || r.status === 'PARTIAL' || r.status === 'HOLD');
    if (selectedIds.size === selectable.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(selectable.map(r => r.id)));
    }
  };

  const handleActionSubmit = () => {
    if (activeModal) {
      setRequests(prev => prev.map(req => {
        if (activeModal.targetIds.includes(req.id)) {
          const statusMap = { 'APPROVE': 'APPROVED' as const, 'HOLD': 'HOLD' as const, 'PARTIAL': 'PARTIAL' as const };
          return { 
            ...req, 
            status: statusMap[activeModal.type], 
            approvedAmount: activeModal.type === 'APPROVE' ? req.requestedAmount : (activeModal.type === 'PARTIAL' ? partialAmount : 0),
            remarks: modalRemark || req.remarks 
          };
        }
        return req;
      }));
    }
    setActiveModal(null);
    setModalRemark('');
    setPartialAmount(0);
    setSelectedIds(new Set());
  };

  const isKharchi = batchId.toUpperCase().includes('K_');

  const getStatusVariant = (status: BatchStatus) => {
    switch (status) {
      case 'OPEN': return 'blue';
      case 'PENDING': return 'warning';
      case 'APPROVED': return 'success';
      case 'CLOSED': return 'neutral';
      case 'CANCELLED': return 'error';
      default: return 'neutral';
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400 pb-20">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <nav className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <span className="hover:text-blue-600 cursor-pointer" onClick={onBack}>Finance</span>
          <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
          <span className="hover:text-blue-600 cursor-pointer" onClick={onBack}>Approvals</span>
          <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
          <span className="text-slate-900">{batchId}</span>
        </nav>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">{batchId}</h1>
            <div className="relative" ref={statusMenuRef}>
              <button disabled={!canApprove} onClick={() => setIsStatusMenuOpen(!isStatusMenuOpen)} className="flex items-center gap-1">
                <Badge variant={getStatusVariant(currentBatchStatus)}>{currentBatchStatus}</Badge>
                {canApprove && <svg className="w-3 h-3 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" /></svg>}
              </button>
              {isStatusMenuOpen && (
                <div className="absolute left-0 top-7 w-48 bg-white border border-slate-200 shadow-2xl py-1 z-50">
                  {(['OPEN', 'PENDING', 'APPROVED', 'CLOSED', 'CANCELLED'] as BatchStatus[]).map((status) => (
                    <button key={status} onClick={() => { setCurrentBatchStatus(status); setIsStatusMenuOpen(false); }} className={`w-full text-left px-4 py-2 text-[10px] font-bold transition-colors hover:bg-slate-50 ${currentBatchStatus === status ? 'text-blue-600 bg-blue-50/50' : 'text-slate-600'}`}>{status}</button>
                  ))}
                </div>
              )}
            </div>
            <div className="h-6 w-px bg-slate-200 mx-2" />
            <div className="flex items-center gap-4 text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
              <span className="flex items-center gap-1"><span className="text-slate-300">Site:</span> {isKharchi ? 'Gurugram' : 'Mumbai'}</span>
              <span className="flex items-center gap-1"><span className="text-slate-300">Type:</span> {isKharchi ? 'KHR' : 'PAY'}</span>
              <span className="flex items-center gap-1"><span className="text-slate-300">Period:</span> Oct 2025</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setCurrentBatchStatus('CLOSED')} className="rounded-none border-slate-300 h-8">Close Batch</Button>
            {canCreate && currentBatchStatus === 'OPEN' && <Button onClick={() => setIsDrawerOpen(true)} size="sm" className="rounded-none bg-blue-600 h-8">Add Request</Button>}
          </div>
        </div>
      </div>

      {/* Summary Strip (Excel Style) */}
      <div className="grid grid-cols-2 border border-slate-200 bg-white shadow-sm divide-x divide-slate-200">
        {/* Left: Total Requested */}
        <div className="p-4 flex flex-col justify-center">
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-2">Total Requested</span>
          <span className="text-3xl font-black tracking-tight text-slate-900">{formatCurrency(totals.requested)}</span>
        </div>

        {/* Right: Approved & Breakdown */}
        <div className="flex flex-col divide-y divide-slate-200">
          <div className="p-4 flex flex-col">
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-2">Total Approved</span>
            <span className="text-3xl font-black tracking-tight text-blue-600">{formatCurrency(totals.approved)}</span>
          </div>
          <div className="grid grid-cols-2 divide-x divide-slate-200 bg-slate-50/50">
            <div className="p-3 flex flex-col">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">Pending</span>
              <span className="text-lg font-black tracking-tight text-orange-600">{formatCurrency(totals.pending)}</span>
            </div>
            <div className="p-3 flex flex-col">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1.5">On Hold</span>
              <span className="text-lg font-black tracking-tight text-rose-600">{formatCurrency(totals.onHold)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Requests Table (Level 2 Excel Grid) */}
      <div className="bg-white border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[11px] border-collapse">
            <thead className="bg-slate-100 border-b border-slate-300">
              <tr>
                <th className="px-2 py-3 w-8 text-center border-r border-slate-200">
                  <input 
                    type="checkbox" 
                    disabled={isReadOnly || currentBatchStatus !== 'OPEN'}
                    onChange={toggleSelectAll}
                    checked={selectedIds.size > 0 && selectedIds.size === requests.filter(r => r.status === 'PENDING' || r.status === 'PARTIAL' || r.status === 'HOLD').length}
                    className="w-3 h-3 rounded-none" 
                  />
                </th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Party</th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Description</th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Req. ₹</th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Appr. ₹</th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center">Status</th>
                <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Remarks</th>
                <th className="px-3 py-3 font-bold text-slate-600 text-center uppercase tracking-tighter w-12">Act.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {requests.map((req) => {
                const isSelectable = !isReadOnly && currentBatchStatus === 'OPEN' && (req.status === 'PENDING' || req.status === 'PARTIAL' || req.status === 'HOLD');
                return (
                  <tr key={req.id} className={`hover:bg-blue-50/50 transition-colors ${selectedIds.has(req.id) ? 'bg-blue-50' : ''}`}>
                    <td className="px-2 py-2.5 text-center border-r border-slate-100">
                      <input type="checkbox" disabled={!isSelectable} checked={selectedIds.has(req.id)} onChange={() => toggleSelect(req.id, req.status)} className="w-3 h-3 rounded-none" />
                    </td>
                    <td className="px-3 py-2.5 border-r border-slate-100 font-black text-slate-800">{req.partyName}</td>
                    <td className="px-3 py-2.5 border-r border-slate-100 text-slate-500 font-medium truncate max-w-[200px]">{req.description}</td>
                    <td className="px-3 py-2.5 border-r border-slate-100 text-right font-bold text-slate-700">{req.requestedAmount.toLocaleString('en-IN')}</td>
                    <td className="px-3 py-2.5 border-r border-slate-100 text-right font-black text-blue-600">{req.approvedAmount > 0 ? req.approvedAmount.toLocaleString('en-IN') : '--'}</td>
                    <td className="px-3 py-2.5 border-r border-slate-100 text-center"><Badge variant={req.status === 'APPROVED' ? 'success' : req.status === 'HOLD' ? 'error' : req.status === 'PARTIAL' ? 'partial' : req.status === 'PAID' ? 'paid' : 'warning'}>{req.status}</Badge></td>
                    <td className="px-3 py-2.5 border-r border-slate-100 italic text-slate-400 font-medium">{req.remarks || '--'}</td>
                    <td className="px-3 py-2.5 text-center">
                      {canApprove && currentBatchStatus === 'OPEN' && req.status !== 'APPROVED' && req.status !== 'PAID' ? (
                        <RowActionDropdown onAction={(type) => setActiveModal({ type, targetIds: [req.id] })} />
                      ) : (
                        <svg className="w-3.5 h-3.5 text-slate-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} /></svg>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bulk Action Toolbar - Floating Bottom Right */}
      {canApprove && selectedIds.size > 0 && currentBatchStatus === 'OPEN' && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white p-2 rounded-lg shadow-2xl flex items-center gap-3 animate-in fade-in slide-in-from-bottom-2">
          <span className="text-[10px] font-black uppercase px-2 py-1 bg-blue-600 rounded">{selectedIds.size} SELECTED</span>
          <button onClick={() => setActiveModal({ type: 'HOLD', targetIds: Array.from(selectedIds) })} className="px-3 py-1.5 text-[10px] font-black hover:bg-slate-800 border border-slate-700 uppercase tracking-widest">Hold All</button>
          <button onClick={() => setActiveModal({ type: 'APPROVE', targetIds: Array.from(selectedIds) })} className="px-4 py-1.5 text-[10px] font-black bg-blue-600 hover:bg-blue-500 uppercase tracking-widest">Approve All</button>
        </div>
      )}
      
      {/* Modals & Drawer */}
      {activeModal && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setActiveModal(null)} />
          <div className="relative bg-white w-full max-w-xs rounded shadow-2xl p-6 text-center border-t-4 border-blue-600">
             <h3 className="text-sm font-black text-slate-900 tracking-tight mb-2 uppercase">Execution: {activeModal.type}</h3>
             <p className="text-slate-500 font-medium text-[11px] mb-4 leading-tight">Confirm action for {activeModal.targetIds.length} request(s).</p>
             <div className="text-left space-y-3 mb-6">
              {activeModal.type === 'PARTIAL' && (
                <div className="space-y-1">
                  <label className="text-[9px] font-black text-slate-400 uppercase">Amount (₹)</label>
                  <input type="number" value={partialAmount} onChange={(e) => setPartialAmount(parseFloat(e.target.value))} className="w-full bg-slate-50 border border-slate-200 px-3 py-2 text-sm font-black text-slate-800" />
                </div>
              )}
              <div className="space-y-1">
                <label className="text-[9px] font-black text-slate-400 uppercase">Remark</label>
                <textarea rows={2} value={modalRemark} onChange={(e) => setModalRemark(e.target.value)} placeholder="..." className="w-full bg-slate-50 border border-slate-200 px-3 py-2 text-[11px]" />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Button onClick={handleActionSubmit} className="w-full h-10 rounded-none bg-blue-600 font-black text-xs uppercase tracking-widest">Execute</Button>
              <button onClick={() => setActiveModal(null)} className="text-[10px] font-bold text-slate-400 hover:text-slate-600 uppercase">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
