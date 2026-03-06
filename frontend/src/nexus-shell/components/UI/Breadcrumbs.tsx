
import React from 'react';
import { Module, NavItem } from '../../types';
import { FINANCE_NAV, DIRECTORY_NAV } from '../../constants';

interface BreadcrumbItem {
  label: string;
  id: string;
}

interface BreadcrumbsProps {
  currentModule: Module;
  activeTab: string;
  selectedBatchId: string | null;
  onNavigate: (id: string) => void;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ 
  currentModule, 
  activeTab, 
  selectedBatchId, 
  onNavigate 
}) => {
  if (activeTab === 'home') return null;

  const crumbs: BreadcrumbItem[] = [
    { label: 'Nexus Home', id: 'home' }
  ];

  // Add Module
  crumbs.push({ label: currentModule.name, id: currentModule.id });

  // Add Tab
  const allNavItems = [...FINANCE_NAV, ...DIRECTORY_NAV];
  const currentNavItem = allNavItems.find(item => item.id === activeTab);

  if (currentNavItem) {
    crumbs.push({ label: currentNavItem.label, id: currentNavItem.id });
  } else if (activeTab === 'fin-batch-detail' && selectedBatchId) {
    crumbs.push({ label: 'Payment Batches', id: 'fin-batches' });
    crumbs.push({ label: selectedBatchId, id: 'fin-batch-detail' });
  } else if (activeTab === 'fin-batches-new') {
    crumbs.push({ label: 'Payment Batches', id: 'fin-batches' });
    crumbs.push({ label: 'New Batch', id: 'fin-batches-new' });
  }

  return (
    <nav className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-6 overflow-x-auto whitespace-nowrap pb-2 md:pb-0">
      {crumbs.map((crumb, index) => (
        <React.Fragment key={crumb.id + index}>
          {index > 0 && (
            <svg className="w-3 h-3 text-slate-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M9 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} />
            </svg>
          )}
          <button
            onClick={() => onNavigate(crumb.id)}
            className={`transition-colors flex-shrink-0 ${
              index === crumbs.length - 1 
                ? 'text-slate-900 font-bold cursor-default' 
                : 'hover:text-slate-600 cursor-pointer'
            }`}
            disabled={index === crumbs.length - 1}
          >
            {crumb.label}
          </button>
        </React.Fragment>
      ))}
    </nav>
  );
};
