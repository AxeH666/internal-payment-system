
import React from 'react';
import { MAIN_NAV, FINANCE_NAV, DIRECTORY_NAV } from '../constants';
import { NavItem, Role } from '../types';

interface SidebarProps {
  activeId: string;
  onNavigate: (id: string) => void;
  isModuleMode?: boolean;
  moduleId?: string;
  role: Role;
  onLogout?: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeId, 
  onNavigate, 
  isModuleMode, 
  moduleId, 
  role, 
  onLogout,
  isCollapsed,
  onToggleCollapse
}) => {
  let navItems: NavItem[] = [];
  
  if (!isModuleMode) {
    navItems = [...MAIN_NAV];
  } else {
    if (moduleId === 'fin') {
      navItems = [...FINANCE_NAV];
      if (role === 'Creator' || role === 'Viewer') {
        navItems = navItems.filter(item => item.id !== 'fin-approvals');
      } else if (role === 'Approver') {
        navItems = navItems.filter(item => item.id === 'fin-approvals' || item.id === 'fin-overview' || item.id === 'fin-soa');
      }
    } else if (moduleId === 'dir') {
      navItems = [...DIRECTORY_NAV];
    }
  }

  return (
    <aside className={`${isCollapsed ? 'w-20' : 'w-64'} bg-white border-r border-slate-100 flex flex-col p-4 z-20 transition-all duration-300 relative`}>
      {/* Collapse Toggle Button */}
      <button 
        onClick={onToggleCollapse}
        className="absolute -right-3 top-6 w-6 h-6 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-600 shadow-sm z-30 transition-transform duration-300"
        style={{ transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }}
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div className="flex-1 space-y-1">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} px-4 py-2.5 rounded-lg transition-all ${
              activeId === item.id 
                ? 'bg-blue-50 text-blue-700 shadow-sm shadow-blue-900/5' 
                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
            }`}
            title={isCollapsed ? item.label : ''}
          >
            <div className="flex items-center gap-3">
              <span className={`${activeId === item.id ? 'text-blue-600' : 'text-slate-400'} shrink-0`}>
                {item.icon}
              </span>
              {!isCollapsed && (
                <span className="text-sm font-bold tracking-tight whitespace-nowrap">
                  {item.label}
                </span>
              )}
            </div>
            {!isCollapsed && item.badge && (
              <span className="bg-rose-50 text-rose-600 text-[10px] font-bold px-1.5 py-0.5 rounded border border-rose-100">
                {item.badge}
              </span>
            )}
          </button>
        ))}

        {isModuleMode && role !== 'Viewer' && (
          <button 
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-2.5 rounded-lg text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-all`}
            title={isCollapsed ? 'Settings' : ''}
          >
            <span className="text-slate-400 shrink-0">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            </span>
            {!isCollapsed && <span className="text-sm font-bold tracking-tight">Settings</span>}
          </button>
        )}
      </div>

      {isModuleMode && !isCollapsed && (
        <div className="mt-auto p-4 bg-slate-50 rounded-xl border border-slate-100">
          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">System Status</p>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-sm shadow-emerald-500/50"></span>
            <span className="text-[11px] font-bold text-slate-600">Online</span>
          </div>
        </div>
      )}

      {/* Profile & Logout Section */}
      <div className={`mt-4 pt-4 border-t border-slate-100 ${isCollapsed ? 'px-0' : ''}`}>
        <button 
          onClick={onLogout}
          className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3 p-3'} rounded-xl bg-slate-50 border border-slate-100 hover:bg-slate-100 hover:border-slate-200 transition-all group`}
          title={isCollapsed ? 'Sign Out' : ''}
        >
          <div className={`w-10 h-10 rounded-lg overflow-hidden border border-slate-200 shrink-0 ${isCollapsed ? '' : ''}`}>
            <img src="https://ui-avatars.com/api/?name=Alex+Rivera&background=f8fafc&color=1e293b&bold=true" alt="avatar" />
          </div>
          {!isCollapsed && (
            <>
              <div className="text-left overflow-hidden">
                <p className="text-xs font-black text-slate-800 truncate">Alex Rivera</p>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight group-hover:text-rose-500 transition-colors">Sign Out</p>
              </div>
              <div className="ml-auto text-slate-300 group-hover:text-rose-500 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </div>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};
