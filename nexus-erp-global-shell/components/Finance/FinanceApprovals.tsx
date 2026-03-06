
import React, { useState, useMemo } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Role } from '../../types';

interface ApprovalBatch {
  name: string;
  type: 'KHR' | 'PAY';
  site: string;
  period: string;
  totalRequested: number;
  pendingCount: number;
  status: 'AWAITING APPROVAL' | 'PARTIALLY APPROVED' | 'FULLY APPROVED' | 'CLOSED';
}

interface FinanceApprovalsProps {
  onSelectBatch: (batchId: string) => void;
  role: Role;
}

export const FinanceApprovals: React.FC<FinanceApprovalsProps> = ({ onSelectBatch, role }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const batches: ApprovalBatch[] = [
    { name: '#K_241025', type: 'KHR', site: 'Gurugram', period: 'Oct 2025 - W4', totalRequested: 415000, pendingCount: 5, status: 'AWAITING APPROVAL' },
    { name: '#P_221025', type: 'PAY', site: 'Mumbai', period: 'Oct 2025', totalRequested: 1240000, pendingCount: 12, status: 'PARTIALLY APPROVED' },
    { name: '#K_251025', type: 'KHR', site: 'Noida', period: 'Oct 2025 - W4', totalRequested: 85000, pendingCount: 0, status: 'FULLY APPROVED' },
    { name: '#P_011025', type: 'PAY', site: 'Bengaluru', period: 'Sep 2025', totalRequested: 4500000, pendingCount: 0, status: 'CLOSED' },
  ];

  const filteredBatches = useMemo(() => {
    return batches.filter(b => 
      b.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
      b.site.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'AWAITING APPROVAL': return 'warning';
      case 'PARTIALLY APPROVED': return 'partial';
      case 'FULLY APPROVED': return 'success';
      case 'CLOSED': return 'neutral';
      default: return 'neutral';
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-900 tracking-tight">Approval Dashboard</h1>
        <div className="flex gap-2">
          <Badge variant="warning">{batches.filter(b => b.status === 'AWAITING APPROVAL').length} Pending</Badge>
          <Badge variant="partial">{batches.filter(b => b.status === 'PARTIALLY APPROVED').length} Active</Badge>
        </div>
      </div>

      <div className="bg-white border border-slate-200 p-2 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input 
            type="text" 
            placeholder="Search batches..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 pl-8 pr-3 py-1.5 text-[11px] font-bold text-slate-600 focus:bg-white outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
           <span className="text-[10px] font-bold text-slate-400 uppercase">View:</span>
           <div className="flex border border-slate-200 rounded overflow-hidden">
              <button className="px-2 py-1 bg-slate-100 text-[10px] font-bold text-slate-700 border-r border-slate-200">Grid</button>
              <button className="px-2 py-1 bg-white text-[10px] font-bold text-slate-400 hover:bg-slate-50">List</button>
           </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-[12%]">Batch Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Site</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-16 text-center">Type</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Period</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Requested</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-20 text-center">Pending</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center">Status</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter w-20 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filteredBatches.map((batch) => (
              <tr 
                key={batch.name} 
                onClick={() => onSelectBatch(batch.name)}
                className="hover:bg-blue-50/50 transition-colors group cursor-pointer"
              >
                <td className="px-3 py-2.5 border-r border-slate-100">
                  <span className="font-bold text-blue-600 group-hover:underline">{batch.name}</span>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-700 font-medium">{batch.site}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <Badge variant={batch.type === 'KHR' ? 'warning' : 'blue'}>{batch.type}</Badge>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-500 font-medium italic">{batch.period}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-right font-bold text-slate-900">
                  {formatCurrency(batch.totalRequested)}
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <span className={`font-black ${batch.pendingCount > 0 ? 'text-orange-600' : 'text-slate-400'}`}>
                    {batch.pendingCount}
                  </span>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <Badge variant={getStatusVariant(batch.status)}>{batch.status}</Badge>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button className="text-[10px] font-black uppercase text-blue-600 hover:text-blue-800 tracking-wider underline underline-offset-2">
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
