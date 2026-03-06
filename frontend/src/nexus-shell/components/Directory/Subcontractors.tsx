
import React, { useState, useMemo } from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Subcontractor, ScScope } from '../../types';
import { SITES } from '../../constants';

interface SubcontractorsProps {
  subcontractors: Subcontractor[];
  onAddSubcontractor: (sc: Subcontractor) => void;
  scopes: string[];
  onAddScope: (name: string) => void;
}

export const Subcontractors: React.FC<SubcontractorsProps> = ({ 
  subcontractors, 
  onAddSubcontractor, 
  scopes, 
  onAddScope 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSc, setSelectedSc] = useState<Subcontractor | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State for Adding Subcontractor
  const [formData, setFormData] = useState({
    name: '',
    scope: '' as ScScope,
    siteCode: '',
    contactNo: '',
  });

  const filtered = useMemo(() => {
    return subcontractors.filter(s => s.name.toLowerCase().includes(searchTerm.toLowerCase()));
  }, [subcontractors, searchTerm]);

  const handleSaveSubcontractor = () => {
    if (!formData.name || !formData.scope || !formData.siteCode || !formData.contactNo) {
      alert('Please fill all required fields.');
      return;
    }

    const newSc: Subcontractor = {
      id: `SC-${Date.now()}`,
      name: formData.name,
      scope: formData.scope,
      siteCode: formData.siteCode,
      contactNo: formData.contactNo,
      hasAadhaar: false,
      hasPan: false,
      hasCheque: false,
    };

    onAddSubcontractor(newSc);
    setIsModalOpen(false);
    setFormData({ name: '', scope: '' as ScScope, siteCode: '', contactNo: '' });
  };

  const AttachmentIcon = ({ present }: { present: boolean }) => (
    <div className={`flex items-center justify-center p-1 rounded-md border ${present ? 'bg-emerald-50 border-emerald-100 text-emerald-600' : 'bg-slate-50 border-slate-100 text-slate-300'}`}>
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
    </div>
  );

  const handleInlineAddScope = () => {
    const name = window.prompt('Enter new ScScope (fk) category:');
    if (name) onAddScope(name);
  };

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-slate-900 tracking-tight uppercase">Subcontractors</h1>
        <Button size="sm" onClick={() => setIsModalOpen(true)} className="rounded-none bg-blue-600 h-8 font-black uppercase">Add Subcontractor</Button>
      </div>

      <div className="bg-white border border-slate-200 p-2 grid grid-cols-4 gap-2">
        <input 
          type="text" 
          placeholder="Search by name..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none focus:bg-white" 
        />
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option value="">All Scopes</option>
          {scopes.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="bg-slate-50 border border-slate-200 px-3 py-1.5 text-[11px] outline-none">
          <option value="">All Sites</option>
          {SITES.map(site => <option key={site.id} value={site.siteCode}>{site.siteCode}</option>)}
        </select>
        <div className="flex gap-1">
           <Button variant="secondary" size="sm" className="flex-1 rounded-none border-slate-300 uppercase font-bold text-[10px]">Filter</Button>
           <Button variant="ghost" size="sm" className="rounded-none uppercase font-bold text-[10px]">Export</Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left text-[11px] border-collapse">
          <thead className="bg-slate-100 border-b border-slate-300">
            <tr>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">S/Name</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-32">ScScope (fk)</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter w-24 text-center">Site Code</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter">Contact No</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-16">Aadhar</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-16">PAN</th>
              <th className="px-3 py-3 font-bold text-slate-600 border-r border-slate-200 uppercase tracking-tighter text-center w-16">Cheque</th>
              <th className="px-3 py-3 font-bold text-slate-600 uppercase tracking-tighter text-right w-20">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filtered.map((sc) => (
              <tr key={sc.id} onClick={() => setSelectedSc(sc)} className="hover:bg-blue-50/50 transition-colors group cursor-pointer">
                <td className="px-3 py-2.5 border-r border-slate-100 font-bold text-slate-800">{sc.name}</td>
                <td className="px-3 py-2.5 border-r border-slate-100">
                  <Badge variant="blue">{sc.scope}</Badge>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <span className="font-mono text-slate-500 font-bold">{sc.siteCode}</span>
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-slate-700 font-medium">{sc.contactNo}</td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <AttachmentIcon present={sc.hasAadhaar} />
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <AttachmentIcon present={sc.hasPan} />
                </td>
                <td className="px-3 py-2.5 border-r border-slate-100 text-center">
                  <AttachmentIcon present={sc.hasCheque} />
                </td>
                <td className="px-3 py-2.5 text-right">
                   <button className="text-[10px] font-black uppercase text-blue-600 hover:text-blue-800 tracking-wider underline">Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Drawer */}
      {selectedSc && (
        <div className="fixed inset-0 z-[200] flex justify-end">
          <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setSelectedSc(null)} />
          <div className="relative w-full max-w-md bg-white h-full shadow-2xl animate-in slide-in-from-right duration-300 flex flex-col">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xl font-black text-slate-900 uppercase tracking-tight">SC Details</h2>
              <button onClick={() => setSelectedSc(null)} className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              <div className="space-y-4">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Full Name</span>
                  <span className="text-lg font-black text-slate-800">{selectedSc.name}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Scope</span>
                    <Badge variant="blue">{selectedSc.scope}</Badge>
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Site Code</span>
                    <span className="font-mono text-sm font-bold text-slate-600">{selectedSc.siteCode}</span>
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Contact Number</span>
                  <span className="text-sm font-bold text-slate-700">{selectedSc.contactNo}</span>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-xs font-black text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-2">Documents & Uploads</h4>
                <div className="grid grid-cols-1 gap-2">
                   {[
                     { label: 'Aadhar Card', present: selectedSc.hasAadhaar },
                     { label: 'PAN Card', present: selectedSc.hasPan },
                     { label: 'Cancelled Cheque', present: selectedSc.hasCheque }
                   ].map((doc, i) => (
                     <div key={i} className="flex items-center justify-between p-3 border border-slate-100 rounded-xl hover:bg-slate-50 transition-all cursor-pointer">
                        <span className="text-xs font-bold text-slate-600">{doc.label}</span>
                        {doc.present ? (
                          <Badge variant="success">View PDF</Badge>
                        ) : (
                          <span className="text-[10px] font-black text-slate-300 uppercase">Missing</span>
                        )}
                     </div>
                   ))}
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl space-y-2">
                <div className="flex justify-between text-[10px] font-bold">
                   <span className="text-slate-400 uppercase">Created On</span>
                   <span className="text-slate-600">12 Oct 2025</span>
                </div>
                <div className="flex justify-between text-[10px] font-bold">
                   <span className="text-slate-400 uppercase">Created By</span>
                   <span className="text-slate-600">Admin User</span>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-slate-100 flex gap-3">
              <Button variant="secondary" className="flex-1 rounded-none uppercase font-black text-xs h-12">Edit Record</Button>
              <Button className="flex-1 rounded-none bg-blue-600 uppercase font-black text-xs h-12">Close Drawer</Button>
            </div>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
          <div className="relative bg-white w-full max-w-2xl rounded-none shadow-2xl p-0 overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b-2 border-slate-100 bg-slate-50 flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900 tracking-tight uppercase">Add Subcontractor</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} /></svg>
              </button>
            </div>
            
            <div className="p-8 space-y-6 overflow-y-auto">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">SC Name (Required)</label>
                  <input 
                    type="text" 
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" 
                    placeholder="Legal name..." 
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">ScScope (fk)</label>
                  <div className="flex gap-2">
                    <select 
                      value={formData.scope}
                      onChange={(e) => setFormData(prev => ({ ...prev, scope: e.target.value as ScScope }))}
                      className="flex-1 bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all"
                    >
                      <option value="">Select Scope...</option>
                      {scopes.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <button 
                      onClick={handleInlineAddScope}
                      className="px-3 bg-slate-100 text-slate-600 font-black text-lg hover:bg-slate-200 transition-colors"
                      title="Add New Scope"
                    >+</button>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Site Code (fk)</label>
                  <select 
                    value={formData.siteCode}
                    onChange={(e) => setFormData(prev => ({ ...prev, siteCode: e.target.value }))}
                    className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all"
                  >
                    <option value="">Select Site...</option>
                    {SITES.map(site => <option key={site.id} value={site.siteCode}>{site.siteCode}</option>)}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Contact No</label>
                  <input 
                    type="text" 
                    value={formData.contactNo}
                    onChange={(e) => setFormData(prev => ({ ...prev, contactNo: e.target.value }))}
                    className="w-full bg-slate-50 border-2 border-slate-100 px-4 py-3 text-sm font-bold focus:bg-white focus:border-blue-100 outline-none transition-all" 
                    placeholder="9999999999" 
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-[10px] font-black text-slate-800 uppercase tracking-[0.2em] border-b border-slate-100 pb-2">Attachment Uploads</h4>
                <div className="grid grid-cols-3 gap-4">
                   {['Aadhar Card', 'PAN Card', 'Cancelled Cheque'].map((doc, i) => (
                     <div key={i} className="border-2 border-dashed border-slate-100 rounded-xl p-4 flex flex-col items-center justify-center gap-2 hover:bg-slate-50 transition-all cursor-pointer">
                        <svg className="w-6 h-6 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}/></svg>
                        <span className="text-[9px] font-black text-slate-400 uppercase text-center">{doc}</span>
                     </div>
                   ))}
                </div>
              </div>
            </div>

            <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setIsModalOpen(false)} className="rounded-none px-10 h-12 uppercase font-black text-xs">Discard</Button>
              <Button onClick={handleSaveSubcontractor} className="rounded-none bg-blue-600 px-10 h-12 uppercase font-black text-xs border-none">Save Subcontractor</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
