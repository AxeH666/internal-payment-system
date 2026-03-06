
import React from 'react';
import { Card } from '../UI/Primitives';

interface DirectoryLandingProps {
  onNavigate: (tab: string) => void;
}

export const DirectoryLanding: React.FC<DirectoryLandingProps> = ({ onNavigate }) => {
  const stats = [
    { title: 'Subcontractors', count: '42', color: 'bg-blue-600', tab: 'dir-sc' },
    { title: 'Vendors', count: '128', color: 'bg-indigo-600', tab: 'dir-vendors' },
    { title: 'Sites', count: '14', color: 'bg-emerald-600', tab: 'dir-sites' },
    { title: 'Clients', count: '8', color: 'bg-slate-800', tab: 'dir-clients' }
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="space-y-2">
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Directory (Master Data)</h1>
        <p className="text-slate-500 font-medium text-lg">Manage your organization's core records for operational speed and consistency.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <button 
            key={i} 
            onClick={() => onNavigate(stat.tab)}
            className="text-left bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-slate-200/50 transition-all group relative overflow-hidden"
          >
            <div className={`absolute top-0 right-0 w-24 h-24 ${stat.color} opacity-[0.03] rounded-bl-full group-hover:scale-110 transition-transform`}></div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">{stat.title}</p>
            <div className="flex items-end justify-between">
              <h2 className="text-5xl font-black text-slate-900 tracking-tighter">{stat.count}</h2>
              <div className={`w-10 h-10 rounded-2xl ${stat.color} text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                 <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="bg-blue-50/50 border border-blue-100 rounded-[2rem] p-6 flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 shrink-0">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <div>
          <h4 className="font-black text-blue-900 uppercase tracking-tight text-sm">Integration Note</h4>
          <p className="text-blue-700/80 text-xs font-medium leading-relaxed mt-1">
            These records are used as verified dropdown options across the ERP, specifically in <strong>Finance {' > '} Create Batch</strong> and <strong>Add Payment Request</strong>. Keeping these accurate ensures error-free disbursements.
          </p>
        </div>
      </div>
    </div>
  );
};
