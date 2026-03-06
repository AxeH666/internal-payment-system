
import React, { useState } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Client } from '../../types';

export const Clients: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const data: Client[] = [
    { id: 'C-01', name: 'SIGNATURE GLOBAL', location: 'Gurgaon', clientCode: 'SGIL' },
    { id: 'C-02', name: 'Godrej Properties', location: 'Gurgaon', clientCode: 'GD' },
    { id: 'C-03', name: 'EMAAR India Limited', location: 'Gurgaon', clientCode: 'EMR' },
    { id: 'C-04', name: 'Shapoorji Pallonji', location: 'Gurgaon', clientCode: 'SP' },
    { id: 'C-05', name: 'Hines India', location: 'Gurgaon', clientCode: 'HN' },
    { id: 'C-06', name: 'DLF Ltd', location: 'Gurgaon', clientCode: 'DLF' },
  ];

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase">Clients</h1>
        <Button size="sm" onClick={() => setIsModalOpen(true)} className="rounded-none bg-blue-600 h-8 font-black uppercase">Add Client</Button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Client Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Location</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-32">ClientCode</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter text-right w-20">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {data.map((client) => (
              <tr key={client.id} className="hover:bg-blue-50/50 transition-colors group">
                <td className="px-3 py-2.5 border-r border-slate-100 font-bold text-slate-800">{client.name}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-500 font-medium italic">{client.location}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <Badge variant="blue">{client.clientCode}</Badge>
                </td>
                <td className="px-3 py-2.5 text-right">
                   <button className="text-[10px] font-black uppercase text-blue-600 hover:text-blue-800 tracking-wider underline">Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
          <div className="relative bg-white w-full max-w-xs rounded-none shadow-2xl p-0 flex flex-col">
            <div className="p-6 border-b-2 border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900 uppercase">New Client</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">×</button>
            </div>
            <div className="p-8 space-y-4 text-left">
               <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Client Name</label>
                  <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold outline-none focus:bg-white" />
               </div>
               <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Location</label>
                  <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold outline-none focus:bg-white" />
               </div>
               <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">ClientCode (Short Unique)</label>
                  <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 font-mono text-sm font-bold outline-none focus:bg-white" placeholder="e.g. SGIL" />
               </div>
            </div>
            <div className="p-8 border-t border-slate-100 flex justify-end gap-2">
              <Button variant="secondary" size="sm" onClick={() => setIsModalOpen(false)} className="rounded-none uppercase font-black px-8">Discard</Button>
              <Button size="sm" className="rounded-none bg-blue-600 uppercase font-black px-8 border-none text-white">Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
