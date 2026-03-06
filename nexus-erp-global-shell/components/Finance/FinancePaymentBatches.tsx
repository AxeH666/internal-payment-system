
import React, { useState } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Role } from '../../types';

interface FinancePaymentBatchesProps {
  onSelectBatch: (batchId: string) => void;
  onCreateNew: () => void;
  role: Role;
}

export const FinancePaymentBatches: React.FC<FinancePaymentBatchesProps> = ({ onSelectBatch, onCreateNew, role }) => {
  const [activePage, setActivePage] = useState(1);
  const canCreate = role === 'Admin' || role === 'Creator';

  const stats = [
    { label: 'TOTAL OPEN VALUE', value: '₹ 4,20,000' },
    { label: 'TOTAL CLOSED (MONTH)', value: '₹ 1.20 Cr' },
  ];

  const batches = [
    { name: '#K_121025', type: 'KHARCHI', typeVariant: 'warning' as const, date: '12 Oct 2025', requested: '₹ 1,45,000', approved: '₹ 1,42,500', status: 'OPEN', statusVariant: 'blue' as const },
    { name: '#P_141025', type: 'PAYMENTS', typeVariant: 'blue' as const, date: '14 Oct 2025', requested: '₹ 12,40,500', approved: '₹ 12,40,500', status: 'Approved', statusVariant: 'success' as const },
    { name: '#K_151025', type: 'KHARCHI', typeVariant: 'warning' as const, date: '15 Oct 2025', requested: '₹ 56,200', approved: '₹ 50,000', status: 'OPEN', statusVariant: 'blue' as const },
    { name: '#P_300925', type: 'PAYMENTS', typeVariant: 'blue' as const, date: '30 Sep 2025', requested: '₹ 45,00,000', approved: '₹ 45,00,000', status: 'Closed', statusVariant: 'neutral' as const },
    { name: '#K_280925', type: 'KHARCHI', typeVariant: 'warning' as const, date: '28 Sep 2025', requested: '₹ 12,000', approved: '₹ 12,000', status: 'Closed', statusVariant: 'neutral' as const },
  ];

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-extrabold text-slate-800 tracking-tight uppercase">Payment Batches</h1>
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            {stats.map((stat, i) => (
              <div key={i} className="bg-white px-3 py-1.5 border border-slate-200 flex flex-col justify-center min-w-[120px] shadow-sm">
                <p className="text-[8px] font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
                <p className={`text-xs font-black tracking-tight ${i === 0 ? 'text-slate-800' : 'text-emerald-600'}`}>{stat.value}</p>
              </div>
            ))}
          </div>
          {canCreate && (
            <Button onClick={onCreateNew} size="sm" className="rounded-none bg-blue-600 h-8 font-black uppercase">New Batch</Button>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 p-2 grid grid-cols-4 gap-2">
        <input type="text" placeholder="Search Batch ID..." className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none focus:bg-white" />
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option>Open Batches</option>
          <option>All Status</option>
        </select>
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option>All Periods</option>
          <option>Oct 2025</option>
        </select>
        <Button variant="secondary" size="sm" className="rounded-none border-slate-300 uppercase font-bold text-[10px]">Filter Results</Button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Batch Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-24">Type</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Date</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Requested</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-right">Batch Value</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter text-center w-24">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {batches.map((batch, i) => (
              <tr key={i} onClick={() => onSelectBatch(batch.name)} className="hover:bg-blue-50/50 transition-colors group cursor-pointer">
                <td className="px-3 py-2.5 border-r border-slate-100 font-bold text-blue-600">{batch.name}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center"><Badge variant={batch.typeVariant}>{batch.type}</Badge></td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-500 font-medium italic">{batch.date}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-right font-bold text-slate-800">{batch.requested}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-right font-black text-slate-600">{batch.approved}</td>
                <td className="px-3 py-2.5 text-center"><Badge variant={batch.statusVariant}>{batch.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-center gap-1 py-2 bg-slate-50 border-t border-slate-200">
          <button className="p-1 text-slate-400 hover:text-slate-600">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 19l-7-7 7-7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={3}/></svg>
          </button>
          {[1, 2, 3].map(page => (
            <button key={page} onClick={() => setActivePage(page)} className={`w-6 h-6 text-[10px] font-bold ${activePage === page ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-400'}`}>{page}</button>
          ))}
          <button className="p-1 text-slate-400 hover:text-slate-600">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={3}/></svg>
          </button>
        </div>
      </div>
    </div>
  );
};
