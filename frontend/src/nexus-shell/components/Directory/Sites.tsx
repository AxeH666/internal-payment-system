
import React, { useState } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { SITES } from '../../constants';

export const Sites: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase">Sites</h1>
        <Button size="sm" onClick={() => setIsModalOpen(true)} className="rounded-none bg-blue-600 h-8 font-black uppercase">Add Site</Button>
      </div>

      <div className="bg-white border border-slate-200 p-2 grid grid-cols-4 gap-2">
        <input 
          type="text" 
          placeholder="Search by site name / code..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none focus:bg-white col-span-2" 
        />
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option>All ClientCodes</option>
          <option>SGIL</option>
          <option>GD</option>
        </select>
        <Button variant="secondary" size="sm" className="rounded-none border-slate-300 uppercase font-bold text-[10px]">Filter Sites</Button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Site Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-32">ClientCode (fk)</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Location</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-32">Site Code</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter text-right w-20">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {SITES.map((site) => (
              <tr key={site.id} className="hover:bg-blue-50/50 transition-colors group">
                <td className="px-3 py-2.5 border-r border-slate-100 font-bold text-slate-800">{site.name}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <Badge variant="neutral">{site.clientCode}</Badge>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-500 font-medium italic">{site.location}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center font-mono font-black text-slate-600">{site.siteCode}</td>
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
          <div className="relative bg-white w-full max-w-md rounded-none shadow-2xl p-0 flex flex-col">
            <div className="p-6 border-b-2 border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900 uppercase">New Site Record</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">×</button>
            </div>
            <div className="p-8 space-y-4">
               <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Site Name</label>
                  <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold outline-none focus:bg-white focus:border-blue-100" />
               </div>
               <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">ClientCode (Dropdown)</label>
                  <select className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold outline-none focus:bg-white focus:border-blue-100">
                    <option>Select Client...</option>
                    <option>SGIL</option>
                    <option>GD</option>
                  </select>
               </div>
               <div className="grid grid-cols-2 gap-4">
                 <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Location</label>
                    <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold outline-none focus:bg-white focus:border-blue-100" />
                 </div>
                 <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Site Code</label>
                    <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 font-mono text-sm font-bold outline-none focus:bg-white focus:border-blue-100" placeholder="e.g. SGIL-101" />
                 </div>
               </div>
            </div>
            <div className="p-8 border-t border-slate-100 flex justify-end gap-3">
              <Button variant="secondary" size="sm" onClick={() => setIsModalOpen(false)} className="rounded-none uppercase font-black px-8">Cancel</Button>
              <Button size="sm" className="rounded-none bg-blue-600 uppercase font-black px-8 border-none">Save Site</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
