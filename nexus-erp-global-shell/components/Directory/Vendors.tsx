
import React, { useState, useMemo } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Vendor } from '../../types';

interface VendorsProps {
  vendors: Vendor[];
  vendorTypes: string[];
  onAddVendorType: (name: string) => void;
}

export const Vendors: React.FC<VendorsProps> = ({ vendors, vendorTypes, onAddVendorType }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const filtered = useMemo(() => {
    return vendors.filter(v => v.name.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [vendors, searchTerm]);

  const handleInlineAddType = () => {
    const name = window.prompt('Enter new VendorType (fk) category:');
    if (name) onAddVendorType(name);
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase">Vendors</h1>
        <Button size="sm" onClick={() => setIsModalOpen(true)} className="rounded-none bg-blue-600 h-8 font-black uppercase">Add Vendor</Button>
      </div>

      <div className="bg-white border border-slate-200 p-2 grid grid-cols-4 gap-2">
        <input 
          type="text" 
          placeholder="Search by vendor name / GSTIN..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none focus:bg-white flex-1 col-span-2" 
        />
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option>All Types</option>
          {vendorTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <Button variant="secondary" size="sm" className="rounded-none border-slate-300 uppercase font-bold text-[10px]">Filter Results</Button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">V/NAME</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-32 text-center">VendorType (fk)</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">POC Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-32 text-center">POC Contact</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">GSTIN</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-16">Cheque</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter text-right w-20">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filtered.map((v) => (
              <tr key={v.id} onClick={() => setSelectedVendor(v)} className="hover:bg-blue-50/50 transition-colors group cursor-pointer">
                <td className="px-3 py-2.5 border-r border-slate-100 font-bold text-slate-800">{v.name}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <Badge variant="blue">{v.type}</Badge>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-700 font-medium">{v.pocName}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center text-slate-600 font-bold">{v.pocContact}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 font-mono text-slate-500 font-bold tracking-tight">{v.gstin}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <div className={`mx-auto w-6 h-6 flex items-center justify-center rounded border ${v.hasCheque ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : 'bg-slate-50 border-slate-100 text-slate-300'}`}>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" strokeLinecap="round" strokeLinejoin="round" strokeWidth={3}/></svg>
                  </div>
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
          <div className="relative bg-white w-full max-w-lg rounded-none shadow-2xl p-0 overflow-hidden flex flex-col">
            <div className="p-6 border-b-2 border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900 tracking-tight uppercase">Add Vendor</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
              </button>
            </div>
            
            <div className="p-8 space-y-6">
               <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Vendor Name</label>
                    <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" placeholder="..." />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">VendorType</label>
                      <div className="flex gap-2">
                        <select className="flex-1 bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all">
                          <option value="">Select Type...</option>
                          {vendorTypes.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                        <button 
                          onClick={handleInlineAddType}
                          className="px-3 bg-slate-100 text-slate-600 font-black text-lg hover:bg-slate-200 transition-colors"
                        >+</button>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">GSTIN</label>
                      <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 font-mono text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" placeholder="07XXXXX..." />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">POC Name</label>
                      <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" placeholder="Contact person..." />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">POC Contact No</label>
                      <input type="text" className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" placeholder="999..." />
                    </div>
                  </div>
               </div>
            </div>

            <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setIsModalOpen(false)} className="rounded-none px-10 h-12 uppercase font-black text-xs">Discard</Button>
              <Button className="rounded-none bg-blue-600 px-10 h-12 uppercase font-black text-xs border-none">Save Vendor</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
