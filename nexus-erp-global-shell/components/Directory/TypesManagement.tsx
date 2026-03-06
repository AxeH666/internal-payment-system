
import React from 'react';
import { Button, Badge } from '../UI/Primitives';

interface TypesManagementProps {
  scopes: { name: string; count: number }[];
  onAddScope: (name: string) => void;
  vendorTypes: { name: string; count: number }[];
  onAddVendorType: (name: string) => void;
}

export const TypesManagement: React.FC<TypesManagementProps> = ({ 
  scopes, 
  onAddScope, 
  vendorTypes, 
  onAddVendorType 
}) => {
  const handleAddScope = () => {
    const name = window.prompt('Enter new ScScope (fk) category:');
    if (name) onAddScope(name);
  };

  const handleAddVendorType = () => {
    const name = window.prompt('Enter new VendorType (fk) category:');
    if (name) onAddVendorType(name);
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-400">
      <div className="space-y-1">
        <h1 className="text-2xl font-black text-slate-900 tracking-tight uppercase">Types Management</h1>
        <p className="text-slate-500 font-medium text-sm italic">Define global categories used in master records. Changes are reflected in dropdowns ERP-wide.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
           <div className="flex items-center justify-between">
              <h3 className="text-xs font-black text-slate-800 uppercase tracking-[0.2em] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-400"></span>
                ScScope (fk) Types
              </h3>
              <Button size="sm" variant="ghost" onClick={handleAddScope} className="text-blue-600 font-black">+ Add Scope</Button>
           </div>
           <div className="bg-white border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead className="bg-slate-100 border-b border-slate-300">
                  <tr>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter">Category Name</th>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter text-center w-24">Usage Count</th>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter text-right w-16">Act.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {scopes.map((s, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2 font-bold text-slate-800">{s.name}</td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="neutral">{s.count}</Badge>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <button className="text-slate-300 hover:text-rose-600 transition-colors">×</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
           </div>
        </div>

        <div className="space-y-4">
           <div className="flex items-center justify-between">
              <h3 className="text-xs font-black text-slate-800 uppercase tracking-[0.2em] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                VendorType (fk) Types
              </h3>
              <Button size="sm" variant="ghost" onClick={handleAddVendorType} className="text-blue-600 font-black">+ Add Type</Button>
           </div>
           <div className="bg-white border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead className="bg-slate-100 border-b border-slate-300">
                  <tr>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter">Category Name</th>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter text-center w-24">Usage Count</th>
                    <th className="px-3 py-2 font-bold text-slate-600 uppercase tracking-tighter text-right w-16">Act.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {vendorTypes.map((v, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2 font-bold text-slate-800">{v.name}</td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="neutral">{v.count}</Badge>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <button className="text-slate-300 hover:text-rose-600 transition-colors">×</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
           </div>
        </div>
      </div>
    </div>
  );
};
