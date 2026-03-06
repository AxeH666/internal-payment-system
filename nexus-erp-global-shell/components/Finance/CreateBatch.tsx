
import React, { useState, useMemo } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Role, Subcontractor, Vendor } from '../../types';

interface BatchRow {
  id: string;
  partyName: string;
  partyType: 'SC' | 'VENDOR' | '';
  siteRef: string;
  amount: number;
  additional: number;
  remarks: string;
  paymentMode: 'NEFT' | 'CASH' | '';
}

interface CreateBatchProps {
  onCancel: () => void;
  onSave: (data: any) => void;
  isViewMode?: boolean;
  batchId?: string;
  status?: string;
  role: Role;
  subcontractors: Subcontractor[];
  vendors: Vendor[];
  isSidebarCollapsed?: boolean;
}

export const CreateBatch: React.FC<CreateBatchProps> = ({ 
  onCancel, 
  onSave, 
  isViewMode, 
  batchId, 
  status = 'OPEN', 
  role,
  subcontractors,
  vendors,
  isSidebarCollapsed
}) => {
  const [batchName, setBatchName] = useState(batchId || '');
  const [currentStatus, setCurrentStatus] = useState(status);
  
  const canEdit = (role === 'Admin' || role === 'Creator') && !isViewMode;
  const isApprover = role === 'Approver';
  const isViewer = role === 'Viewer';
  const isReadOnly = isViewer || (isApprover && isViewMode) || isViewMode;

  // Initialize with a single empty row for new batch creation
  const [rows, setRows] = useState<BatchRow[]>(() => {
    return [{ id: Date.now().toString(), partyName: '', partyType: '', siteRef: '', amount: 0, additional: 0, remarks: '', paymentMode: '' }];
  });

  const handleRowChange = (id: string, field: keyof BatchRow, value: any) => {
    if (isReadOnly) return;
    setRows(prev => prev.map(row => {
      if (row.id === id) {
        let val = value;
        if (field === 'amount' || field === 'additional') {
          val = parseFloat(value) || 0;
        }
        
        // Auto-fill Logic: Link S/Name to Site Code
        if (field === 'partyName') {
          // Check if it's a subcontractor or vendor
          const sub = subcontractors.find(s => s.name === val);
          if (sub) {
            return { ...row, partyName: val, partyType: 'SC', siteRef: sub.siteCode };
          }
          const ven = vendors.find(v => v.name === val);
          if (ven) {
            return { ...row, partyName: val, partyType: 'VENDOR', siteRef: 'N/A' };
          }
          return { ...row, partyName: val, partyType: '', siteRef: '' };
        }
        
        return { ...row, [field]: val };
      }
      return row;
    }));
  };

  const addRow = () => {
    if (isReadOnly) return;
    setRows([...rows, { id: Date.now().toString(), partyName: '', partyType: '', siteRef: '', amount: 0, additional: 0, remarks: '', paymentMode: '' }]);
  };

  const removeRow = (id: string) => {
    if (isReadOnly) return;
    if (rows.length > 1) {
      setRows(rows.filter(r => r.id !== id));
    } else {
      setRows([{ id: Date.now().toString(), partyName: '', partyType: '', siteRef: '', amount: 0, additional: 0, remarks: '', paymentMode: '' }]);
    }
  };

  const totals = useMemo(() => {
    const requested = rows.reduce((sum, r) => sum + r.amount + r.additional, 0);
    const approved = isViewMode ? requested * 0.98 : 0;
    const paid = isViewMode ? (status === 'Closed' ? approved : 45000) : 0;
    const outstanding = isViewMode ? approved - paid : requested;
    return { requested, approved, paid, outstanding };
  }, [rows, isViewMode, status]);

  const formatINR = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount).replace('₹', 'INR ');
  };

  const formatWithCommas = (val: string | number) => {
    const num = typeof val === 'string' ? parseFloat(val.replace(/,/g, '')) : val;
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('en-IN').format(num);
  };

  const parseCommas = (val: string) => {
    return val.replace(/,/g, '');
  };

  const batchType = batchName.includes('#K_') ? 'KHARCHI' : 'PAYMENTS';

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400 pb-24">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase">{batchName || 'NEW BATCH'}</h1>
          <Badge variant={isViewMode ? 'neutral' : 'blue'}>{isViewMode ? currentStatus : 'DRAFT'}</Badge>
          <div className="h-4 w-px bg-slate-200" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">TYPE: <span className="text-slate-600">{batchType}</span></span>
        </div>
        <div className="flex gap-2">
          {!isReadOnly && <Button onClick={addRow} size="sm" className="rounded-none bg-blue-600 h-8 font-black uppercase">Add Row</Button>}
          <Button variant="secondary" size="sm" onClick={onCancel} className="rounded-none border-slate-300 h-8 uppercase font-bold text-[10px]">Close View</Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-2 py-2.5 font-bold text-slate-600 border-r border-slate-200 text-center w-8">#</th>
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Party Name (S/Name)</th>
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-32 text-center">Site Ref (Auto)</th>
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Amount</th>
              {batchType === 'PAYMENTS' && <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Addl.</th>}
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Total</th>
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-24">Mode</th>
              <th className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Remarks</th>
              <th className="px-2 py-2.5 font-bold text-slate-600 text-center w-8">Act.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row, idx) => (
              <tr key={row.id} className={`hover:bg-blue-50/20 transition-colors ${
                row.paymentMode === 'NEFT' ? 'bg-orange-100/50' : 
                row.paymentMode === 'CASH' ? 'bg-emerald-100/50' : ''
              }`}>
                <td className="px-2 py-2 text-center border-r border-slate-100 text-slate-400">{idx + 1}</td>
                <td className="px-1 py-1 border-r border-slate-100">
                  <div className="flex items-center gap-2 px-2">
                    <select 
                      disabled={isReadOnly}
                      value={row.partyName}
                      onChange={(e) => handleRowChange(row.id, 'partyName', e.target.value)}
                      className="flex-1 bg-transparent border-none text-[11px] font-bold text-slate-800 focus:ring-0 outline-none py-2 appearance-none cursor-pointer"
                    >
                      <option value="">Select Party...</option>
                      {batchType === 'KHARCHI' ? (
                        subcontractors.map(sub => (
                          <option key={sub.id} value={sub.name}>{sub.name} ({sub.scope})</option>
                        ))
                      ) : (
                        <>
                          <optgroup label="Subcontractors">
                            {subcontractors.map(sub => (
                              <option key={sub.id} value={sub.name}>{sub.name} (SC)</option>
                            ))}
                          </optgroup>
                          <optgroup label="Vendors">
                            {vendors.map(ven => (
                              <option key={ven.id} value={ven.name}>{ven.name} (VENDOR)</option>
                            ))}
                          </optgroup>
                        </>
                      )}
                    </select>
                    {row.partyType && (
                      <span className={`text-[8px] font-black px-1.5 py-0.5 rounded uppercase tracking-tighter ${
                        row.partyType === 'SC' ? 'bg-orange-100 text-orange-600' : 'bg-blue-100 text-blue-600'
                      }`}>
                        {row.partyType}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-1 py-1 border-r border-slate-100">
                  <input 
                    type="text" 
                    readOnly
                    value={row.siteRef}
                    className="w-full bg-slate-50/50 border-none text-[11px] font-black text-slate-500 text-center focus:ring-0 outline-none p-2"
                    placeholder="AUTO"
                  />
                </td>
                <td className="px-1 py-1 border-r border-slate-100">
                  <input 
                    type="text" 
                    disabled={isReadOnly}
                    value={row.amount === 0 ? '' : formatWithCommas(row.amount)}
                    onChange={(e) => handleRowChange(row.id, 'amount', parseCommas(e.target.value))}
                    className="w-full bg-transparent border-none text-[11px] font-mono font-bold text-slate-800 text-right focus:ring-0 outline-none p-2"
                    placeholder="0"
                  />
                </td>
                {batchType === 'PAYMENTS' && (
                  <td className="px-1 py-1 border-r border-slate-100">
                    <input 
                      type="text" 
                      disabled={isReadOnly}
                      value={row.additional === 0 ? '' : formatWithCommas(row.additional)}
                      onChange={(e) => handleRowChange(row.id, 'additional', parseCommas(e.target.value))}
                      className="w-full bg-transparent border-none text-[11px] font-mono font-medium text-slate-400 text-right focus:ring-0 outline-none p-2"
                      placeholder="0"
                    />
                  </td>
                )}
                <td className="px-3 py-2 border-r border-slate-100 text-right font-mono font-black text-slate-900">
                  {formatINR(row.amount + row.additional)}
                </td>
                <td className="px-0 py-0 border-r border-slate-100 w-24">
                  <div className="flex h-8 w-full divide-x divide-slate-100">
                    <button 
                      disabled={isReadOnly}
                      onClick={() => handleRowChange(row.id, 'paymentMode', row.paymentMode === 'NEFT' ? '' : 'NEFT')}
                      className={`flex-1 text-[9px] font-black transition-all ${
                        row.paymentMode === 'NEFT' 
                          ? 'bg-orange-500 text-white shadow-inner' 
                          : 'text-slate-400 hover:bg-slate-50'
                      }`}
                    >
                      NEFT
                    </button>
                    <button 
                      disabled={isReadOnly}
                      onClick={() => handleRowChange(row.id, 'paymentMode', row.paymentMode === 'CASH' ? '' : 'CASH')}
                      className={`flex-1 text-[9px] font-black transition-all ${
                        row.paymentMode === 'CASH' 
                          ? 'bg-emerald-500 text-white shadow-inner' 
                          : 'text-slate-400 hover:bg-slate-50'
                      }`}
                    >
                      CASH
                    </button>
                  </div>
                </td>
                <td className="px-1 py-1 border-r border-slate-100">
                  <input 
                    type="text" 
                    disabled={isReadOnly}
                    value={row.remarks}
                    onChange={(e) => handleRowChange(row.id, 'remarks', e.target.value)}
                    className="w-full bg-transparent border-none text-[11px] font-medium text-slate-500 focus:ring-0 outline-none p-2"
                    placeholder="Remarks..."
                  />
                </td>
                <td className="px-1 py-1 text-center">
                  {!isReadOnly && <button onClick={() => removeRow(row.id)} className="text-slate-300 hover:text-rose-600 p-1">×</button>}
                </td>
              </tr>
            ))}
            {/* Spacer row for total row separation */}
            <tr className="h-4 bg-white">
              <td colSpan={batchType === 'PAYMENTS' ? 9 : 8} className="border-none"></td>
            </tr>
          </tbody>
          <tfoot className="bg-slate-50 border-t border-slate-300 font-black font-mono">
            <tr>
              <td colSpan={batchType === 'PAYMENTS' ? 3 : 4} className="px-3 py-2.5 text-right border-r border-slate-200 uppercase text-[9px] font-sans text-slate-400">Totals</td>
              {batchType === 'PAYMENTS' && (
                <>
                  <td className="px-3 py-2.5 text-right border-r border-slate-200">{formatINR(rows.reduce((s,r) => s+r.amount,0))}</td>
                  <td className="px-3 py-2.5 text-right border-r border-slate-200">{formatINR(rows.reduce((s,r) => s+r.additional,0))}</td>
                </>
              )}
              <td className="px-3 py-2.5 text-right border-r border-slate-200 text-blue-600">{formatINR(totals.requested)}</td>
              <td colSpan={3}></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className={`fixed bottom-0 ${isSidebarCollapsed ? 'left-20' : 'left-64'} right-0 h-12 bg-slate-900 flex items-center justify-between px-6 z-20 transition-all duration-300`}>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest italic flex items-center gap-2">
          <svg className="w-3 h-3 text-emerald-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" /></svg>
          SEVEN Sheet Interface — Auto-save Active
        </span>
        {!isReadOnly && (
          <div className="flex items-center gap-3">
             <span className="text-[10px] font-black text-white/50 uppercase tracking-widest font-mono">Total Value: {formatINR(totals.requested)}</span>
             <Button onClick={() => onSave({ name: batchName })} size="sm" className="rounded-none bg-blue-600 h-8 px-8 font-black uppercase tracking-widest border-none">Finalize Sheet</Button>
          </div>
        )}
      </div>
    </div>
  );
};
