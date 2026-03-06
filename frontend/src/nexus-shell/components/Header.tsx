
import React, { useState, useRef, useEffect } from 'react';
import { MODULES, SITES } from '../constants';
import { Module, Site } from '../types';

interface HeaderProps {
  currentModule: Module;
  onModuleChange: (mod: Module) => void;
  currentSite: Site;
  onSiteChange: (site: Site) => void;
  isModuleMode?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ 
  currentModule, 
  onModuleChange, 
  currentSite, 
  onSiteChange,
  isModuleMode
}) => {
  const [isSiteOpen, setIsSiteOpen] = useState(false);
  const [isAppLauncherOpen, setIsAppLauncherOpen] = useState(false);
  const launcherRef = useRef<HTMLDivElement>(null);

  // Close launcher when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (launcherRef.current && !launcherRef.current.contains(event.target as Node)) {
        setIsAppLauncherOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-16 border-b border-slate-100 bg-white flex items-center justify-between px-6 sticky top-0 z-[110]">
      <div className="flex items-center gap-4">
        {/* Module Switcher / App Launcher */}
        <div className="relative" ref={launcherRef}>
          <button 
            onClick={() => setIsAppLauncherOpen(!isAppLauncherOpen)}
            className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-slate-50 transition-all border border-slate-100/60 bg-white shadow-sm group"
          >
            <div className="w-10 h-10 flex items-center justify-center bg-slate-900 rounded-xl text-white shadow-md shadow-slate-900/20 group-hover:scale-105 transition-transform overflow-hidden">
              <img src="https://raw.githubusercontent.com/seven-labs/assets/main/logo-77-white.png" alt="logo" className="w-7 h-7 object-contain" onError={(e) => {
                // Fallback if image fails
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement!.innerHTML = '<span class="text-xs font-black">77</span>';
              }} />
            </div>
            <div className="text-left leading-none flex flex-col justify-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-0.5">
                {isModuleMode ? currentModule.name : 'SEVEN'}
              </p>
              <p className="text-[13px] font-black text-slate-800 tracking-tight">
                Labs
              </p>
            </div>
            <div className="ml-1 text-slate-300">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
              </svg>
            </div>
          </button>

          {/* App Launcher Dropdown */}
          {isAppLauncherOpen && (
            <div className="absolute top-14 left-0 w-80 bg-white border border-slate-200 rounded-2xl shadow-2xl py-4 z-50 animate-in fade-in zoom-in-95 duration-200">
              <div className="px-5 mb-3">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Switch Module</p>
              </div>
              <div className="grid grid-cols-1 gap-1 px-2">
                {MODULES.map(mod => (
                  <button
                    key={mod.id}
                    onClick={() => {
                      onModuleChange(mod);
                      setIsAppLauncherOpen(false);
                    }}
                    className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all ${
                      currentModule.id === mod.id && isModuleMode
                        ? 'bg-blue-50 text-blue-700' 
                        : 'hover:bg-slate-50 text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <div className={`w-10 h-10 flex items-center justify-center rounded-xl ${
                      currentModule.id === mod.id && isModuleMode ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {mod.icon}
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-black tracking-tight">{mod.name}</p>
                      <p className="text-[11px] font-medium text-slate-400 truncate max-w-[180px]">{mod.description}</p>
                    </div>
                    {currentModule.id === mod.id && isModuleMode && (
                      <div className="ml-auto">
                        <div className="w-2 h-2 rounded-full bg-blue-600 shadow-lg shadow-blue-600/40"></div>
                      </div>
                    )}
                  </button>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100 px-2">
                <button 
                  onClick={() => {
                    // Logic to go back to home screen
                    window.dispatchEvent(new CustomEvent('navigate-home'));
                    setIsAppLauncherOpen(false);
                  }}
                  className="w-full flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 transition-all"
                >
                  <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-50 text-slate-400">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-black tracking-tight">System Home</p>
                    <p className="text-[11px] font-medium text-slate-400">Global dashboard and apps</p>
                  </div>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center Search */}
      <div className="flex-1 max-w-xl mx-8">
        <div className="relative group">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <svg className="h-4 w-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search batches, parties, work orders"
            className="w-full bg-slate-100/60 border-2 border-transparent focus:border-blue-100 focus:bg-white rounded-xl py-2.5 pl-11 pr-4 text-sm transition-all outline-none text-slate-600 placeholder:text-slate-400 font-medium"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Site Selector Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setIsSiteOpen(!isSiteOpen)}
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 hover:border-slate-300 shadow-sm transition-all"
          >
            <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            {currentSite.name}
            <svg className={`w-4 h-4 text-slate-300 transition-transform duration-200 ${isSiteOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" /></svg>
          </button>
          
          {isSiteOpen && (
            <div className="absolute top-14 right-0 w-64 bg-white border border-slate-200 rounded-2xl shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-4 py-2 mb-1 border-b border-slate-50">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Select Site Location</p>
              </div>
              {SITES.map(site => (
                <button
                  key={site.id}
                  onClick={() => {
                    onSiteChange(site);
                    setIsSiteOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 hover:bg-slate-50 flex flex-col gap-0.5 transition-colors ${currentSite.id === site.id ? 'bg-slate-50' : ''}`}
                >
                  <span className={`font-bold text-sm ${currentSite.id === site.id ? 'text-blue-600' : 'text-slate-800'}`}>{site.name}</span>
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">{site.location}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <button className="relative p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-orange-500 border-2 border-white rounded-full"></span>
        </button>
      </div>
    </header>
  );
};
