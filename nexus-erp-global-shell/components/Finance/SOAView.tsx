
import React, { useState } from 'react';
import { Badge, Button } from '../UI/Primitives';

interface SOAVersion {
  id: string;
  name: string;
  status: 'FINAL' | 'INTERIM';
  date: string;
  generatedBy: string;
  summary: string[];
}

interface SOARecord {
  no: number;
  partyName: string;
  tranId: string;
  amount: number;
  utr: string;
  date: string;
  time: string;
  remarks: string;
}

export const SOAView: React.FC = () => {
  const [activeVersion, setActiveVersion] = useState('v3');
  const [activeTab, setActiveTab] = useState('neft');

  const versions: SOAVersion[] = [
    { id: 'v3', name: 'SOA v3', status: 'FINAL', date: 'Feb 5, 2025', generatedBy: 'admin', summary: ['+5 payments added', '₹ 1,95,000 added', '2 moved from HOLD to PAID'] },
    { id: 'v2', name: 'SOA v2', status: 'INTERIM', date: 'Jan 31, 2025', generatedBy: 'admin', summary: ['Initial draft review'] },
    { id: 'v1', name: 'SOA v1', status: 'INTERIM', date: 'Dec 25, 2024', generatedBy: 'admin', summary: ['Batch created'] },
  ];

  const records: SOARecord[] = [
    { no: 1, partyName: 'Kamini', tranId: 'X93661561', amount: 77959, utr: '0254181485', date: '31/01/2026', time: '16:01', remarks: '' },
    { no: 2, partyName: 'Vijay Kumar Sah', tranId: 'X93656613', amount: 35111, utr: '02541814757', date: '31/01/2026', time: '16:01', remarks: '' },
    { no: 3, partyName: 'Mona Parshuram', tranId: 'X93662242', amount: 38956, utr: '0254181488', date: '31/01/2026', time: '16:01', remarks: 'Confirmed' },
    { no: 4, partyName: 'Ajay Ahirwar', tranId: 'X93662787', amount: 71860, utr: '02541814855', date: '31/01/2026', time: '16:01', remarks: 'Moved from hold' },
    { no: 5, partyName: 'Jay Prakash', tranId: 'X93663996', amount: 221013, utr: '02541819922', date: '31/01/2026', time: '16:01', remarks: 'Confirmed' },
    { no: 6, partyName: 'Mahmood Ansari', tranId: 'T76185225', amount: 150000, utr: '', date: '04/02/2026', time: '15:41', remarks: 'Confirmed' },
    { no: 7, partyName: 'Banwari Mandal', tranId: 'T76202808', amount: 42295, utr: 'T76182208', date: '04/02/2026', time: '15:41', remarks: 'Confirmed' },
    { no: 11, partyName: 'Jaya Road Lines', tranId: 'T76197251', amount: 42295, utr: 'T76197251', date: '04/02/2026', time: '15:41', remarks: '' },
  ];

  const currentVersion = versions.find(v => v.id === activeVersion) || versions[0];

  const formatINR = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val).replace('₹', '₹ ');
  };

  return (
    <div className="max-w-[1200px] mx-auto space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
        <span>Payment Batches</span>
        <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
        <span className="text-slate-900">PRW DEC25</span>
      </nav>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Statement of Account (SOA)</h1>
        <div className="flex gap-2">
           <Button variant="secondary" size="sm" className="h-8 text-[10px] font-bold bg-white border-slate-200">
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              Screen
           </Button>
           <Button variant="secondary" size="sm" className="h-8 w-8 p-0 bg-white border-slate-200">
              <svg className="w-3.5 h-3.5 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
           </Button>
           <Button variant="secondary" size="sm" className="h-8 w-8 p-0 bg-white border-slate-200">
              <svg className="w-3.5 h-3.5 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
           </Button>
        </div>
      </div>

      <div className="bg-slate-900/5 border border-slate-200 rounded-lg p-3 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/20">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" /></svg>
        </div>
        <p className="text-[11px] font-bold text-slate-600">
          Viewing <span className="text-blue-600 font-black">PRW DEC25</span> - Batch of subcontractor payments, December 2025
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 space-y-4">
          {/* Version Info Card */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black text-slate-400 uppercase tracking-widest">VERSION:</span>
                  <span className="text-sm font-black text-slate-800">{currentVersion.name}</span>
                  <Badge variant={currentVersion.status === 'FINAL' ? 'success' : 'warning'} className="text-[9px] px-1.5 py-0">{currentVersion.status}</Badge>
                </div>
                <p className="text-[10px] font-medium text-slate-400 italic">
                  Generated by: <span className="text-slate-600 font-bold">{currentVersion.generatedBy}</span>. Wed, {currentVersion.date}, 12:47 PM
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <select 
                    value={activeVersion}
                    onChange={(e) => setActiveVersion(e.target.value)}
                    className="appearance-none bg-slate-50 border border-slate-200 rounded px-3 py-1.5 text-[10px] font-bold text-slate-600 pr-8 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="v3">Select Version: SOA v3</option>
                    <option value="v2">SOA v2</option>
                    <option value="v1">SOA v1</option>
                  </select>
                  <svg className="w-3 h-3 absolute right-2.5 top-2 text-slate-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </div>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white h-8 text-[10px] font-bold px-4">
                  <svg className="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  Export SOA
                </Button>
              </div>
            </div>

            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-black">1</div>
                <h3 className="text-[11px] font-black text-slate-800 uppercase tracking-tight">Change summary ({currentVersion.summary[0]}):</h3>
              </div>
              <ul className="space-y-1 ml-7">
                {currentVersion.summary.map((item, i) => (
                  <li key={i} className="text-[11px] font-medium text-slate-500 flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-slate-300" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Tabs & Table */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="flex border-b border-slate-200">
              {[
                { id: 'neft', label: 'NEFT/Cheque', count: 15 },
                { id: 'cash', label: 'Cash', count: 2 },
                { id: 'hold', label: 'Hold', count: 2 },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-3 text-[11px] font-black uppercase tracking-widest transition-all relative ${
                    activeTab === tab.id ? 'text-blue-600' : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {tab.label} ({tab.count})
                  {activeTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />}
                </button>
              ))}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead className="bg-slate-100 border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-2.5 font-bold text-slate-500 border-r border-slate-100 w-12 text-center">No.</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100">Party Name</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100">Tran Id</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100 text-right">Amount</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100">UTR</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100">Date</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500 border-r border-slate-100">Time</th>
                    <th className="px-4 py-2.5 font-bold text-slate-500">Remarks</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((row) => (
                    <tr key={row.no} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-3 py-2 text-center border-r border-slate-50 text-slate-400 font-medium">{row.no}</td>
                      <td className="px-4 py-2 border-r border-slate-50 font-bold text-slate-800">{row.partyName}</td>
                      <td className="px-4 py-2 border-r border-slate-50 text-slate-500 font-mono">{row.tranId}</td>
                      <td className="px-4 py-2 border-r border-slate-50 text-right font-black text-slate-900">{formatINR(row.amount)}</td>
                      <td className="px-4 py-2 border-r border-slate-50 text-slate-500 font-mono text-[10px]">{row.utr || '--'}</td>
                      <td className="px-4 py-2 border-r border-slate-50 text-slate-500">{row.date}</td>
                      <td className="px-4 py-2 border-r border-slate-50 text-slate-500">{row.time}</td>
                      <td className="px-4 py-2">
                        {row.remarks && (
                          <Badge variant="neutral" className="text-[9px] px-1.5 py-0 bg-slate-100 text-slate-600 border-none">{row.remarks}</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-50/80 border-t border-slate-200">
                  <tr className="font-black text-slate-800">
                    <td colSpan={3} className="px-4 py-3 text-right text-[10px] text-slate-400 uppercase tracking-widest">Total Paid</td>
                    <td className="px-4 py-3 text-right text-sm">{formatINR(1300197)}</td>
                    <td colSpan={3} className="px-4 py-3 text-right text-[10px] text-slate-400 uppercase tracking-widest">Total On Hold</td>
                    <td className="px-4 py-3 text-sm text-rose-600">{formatINR(30000)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-black text-slate-900 tracking-tight">PRW DEC25</h2>
              <button className="text-slate-300 hover:text-slate-600"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 5v.01M12 12v.01M12 19v.01" /></svg></button>
            </div>
            <div className="p-4 space-y-3">
              <p className="text-[11px] font-medium text-slate-500 leading-relaxed">Batch of subcontractor payments, December 2025</p>
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Total Paid</span>
                  <span className="text-xs font-black text-slate-800">{formatINR(1300197)}</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Total On Hold</span>
                  <span className="text-xs font-black text-slate-800">{formatINR(30000)}</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-blue-50 rounded border border-blue-100">
                  <span className="text-[10px] font-bold text-blue-400 uppercase">Total In Batch</span>
                  <span className="text-xs font-black text-blue-600">{formatINR(1330197)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-black text-slate-900 tracking-tight">SOA Versions</h2>
              <button className="text-slate-300 hover:text-slate-600"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 5v.01M12 12v.01M12 19v.01" /></svg></button>
            </div>
            <div className="divide-y divide-slate-50">
              {versions.map(v => (
                <div key={v.id} className="p-4 hover:bg-slate-50 transition-colors cursor-pointer group">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black text-slate-800 group-hover:text-blue-600 transition-colors">{v.name}</span>
                      <Badge variant={v.status === 'FINAL' ? 'success' : 'warning'} className="text-[8px] px-1 py-0">{v.status}</Badge>
                    </div>
                    {v.id === activeVersion && (
                      <svg className="w-3.5 h-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                    )}
                  </div>
                  <p className="text-[10px] font-bold text-slate-400">{v.date}</p>
                </div>
              ))}
            </div>
            <div className="p-4 bg-slate-50 border-t border-slate-100">
              <p className="text-[10px] font-medium text-slate-400 leading-relaxed italic">
                Export help, or live versions at yasparn in live version
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
