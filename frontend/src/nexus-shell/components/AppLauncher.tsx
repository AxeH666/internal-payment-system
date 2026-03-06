
import React from 'react';
import { Badge } from './UI/Primitives';

interface LauncherItem {
  id: string;
  name: string;
  description: string;
  status: 'LIVE' | 'BETA' | 'LOCKED';
  footerText?: string;
  icon: React.ReactNode;
}

interface AppLauncherProps {
  onSelect: (moduleId: string) => void;
}

export const AppLauncher: React.FC<AppLauncherProps> = ({ onSelect }) => {
  const apps: LauncherItem[] = [
    {
      id: 'fin',
      name: 'Finance',
      description: 'Internal project payments and budget tracking.',
      status: 'LIVE',
      footerText: 'Last used: 2h ago',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10v2h2V6a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>
    },
    {
      id: 'dir',
      name: 'Directory',
      description: 'Master records for Vendors, Subcontractors, Sites, and Clients.',
      status: 'LIVE',
      footerText: 'Data Masters',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM6 8a2 2 0 11-4 0 2 2 0 014 0zM11 18a4.993 4.993 0 00-1-3.048V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303" /></svg>
    },
    {
      id: 'led',
      name: 'Ledgers',
      description: 'Unified vendor and staff ledger records.',
      status: 'LIVE',
      footerText: 'Last used: Yesterday',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" /></svg>
    },
    {
      id: 'dpr',
      name: 'DPR',
      description: 'Daily Progress Reporting for site operations.',
      status: 'BETA',
      footerText: 'Feature testing active',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
    },
    {
      id: 'proc',
      name: 'Procurement',
      description: 'Supply chain and materials sourcing management.',
      status: 'LOCKED',
      footerText: 'Coming Soon',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" /></svg>
    },
    {
      id: 'att',
      name: 'Attendance',
      description: 'Staff tracking and biometric integration.',
      status: 'LOCKED',
      footerText: 'Coming Soon',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>
    },
    {
      id: 'doc',
      name: 'Documents',
      description: 'Centralized resource and blueprint management.',
      status: 'LOCKED',
      footerText: 'Coming Soon',
      icon: <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" /></svg>
    }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-12 py-4">
      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">Apps</h2>
        <p className="text-slate-500 font-medium text-lg">Access your enterprise modules and tools for project lifecycle management.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {apps.map((app) => (
          <button
            key={app.id}
            disabled={app.status === 'LOCKED'}
            onClick={() => onSelect(app.id)}
            className={`text-left flex flex-col p-6 rounded-2xl border transition-all duration-200 group relative min-h-[220px] ${
              app.status === 'LOCKED' 
                ? 'bg-slate-50 border-slate-100 cursor-not-allowed border-dashed' 
                : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-xl hover:shadow-blue-900/5'
            }`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl ${
                app.status === 'LOCKED' ? 'bg-slate-200/50 text-slate-400' : 'bg-blue-50 text-blue-600'
              }`}>
                {app.icon}
              </div>
              <div className="flex items-center gap-2">
                {app.status === 'LOCKED' && (
                   <svg className="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                )}
                <Badge variant={app.status === 'LIVE' ? 'success' : app.status === 'BETA' ? 'warning' : 'neutral'}>
                  {app.status}
                </Badge>
              </div>
            </div>

            <div className="flex-1">
              <h3 className={`text-xl font-bold mb-2 ${app.status === 'LOCKED' ? 'text-slate-500' : 'text-slate-800'}`}>
                {app.name}
              </h3>
              <p className={`text-sm leading-relaxed ${app.status === 'LOCKED' ? 'text-slate-400' : 'text-slate-500 font-medium'}`}>
                {app.description}
              </p>
            </div>

            <div className="mt-6 flex items-center gap-2 pt-4 border-t border-slate-100/50">
              {app.status === 'LIVE' || app.status === 'BETA' ? (
                <svg className="w-3.5 h-3.5 text-slate-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" /></svg>
              ) : null}
               {app.id === 'dpr' && (
                 <svg className="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
               )}
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                {app.footerText}
              </span>
            </div>
          </button>
        ))}
      </div>

      <div className="space-y-6 pt-8 border-t border-slate-100">
        <h3 className="text-xl font-bold text-slate-800">Shared Resources</h3>
        <div className="flex flex-wrap gap-4">
          {[
            { label: 'Training Manuals', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg> },
            { label: 'System Updates', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg> },
            { label: 'Internal Directory', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> },
          ].map((resource, i) => (
            <button key={i} className="flex items-center gap-2.5 px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm">
              <span className="text-slate-400">{resource.icon}</span>
              {resource.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
