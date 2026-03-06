
import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Login } from './components/Login';
import { AppLauncher } from './components/AppLauncher';
import { FinanceOverview } from './components/Finance/FinanceOverview';
import { FinancePaymentBatches } from './components/Finance/FinancePaymentBatches';
import { CreateBatch } from './components/Finance/CreateBatch';
import { BatchDetail } from './components/Finance/BatchDetail';
import { FinanceApprovals } from './components/Finance/FinanceApprovals';
import { SOAView } from './components/Finance/SOAView';
import { DirectoryLanding } from './components/Directory/DirectoryLanding';
import { Subcontractors } from './components/Directory/Subcontractors';
import { Vendors } from './components/Directory/Vendors';
import { Sites } from './components/Directory/Sites';
import { Clients } from './components/Directory/Clients';
import { TypesManagement } from './components/Directory/TypesManagement';
import { Breadcrumbs } from './components/UI/Breadcrumbs';
import { MODULES, SITES, SUBCONTRACTORS as INITIAL_SUBCONTRACTORS, VENDORS as INITIAL_VENDORS } from './constants';
import { Module, Site, Role, Subcontractor, Vendor } from './types';
import { Button } from './components/UI/Primitives';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentModule, setCurrentModule] = useState<Module>(MODULES[0]);
  const [currentSite, setCurrentSite] = useState<Site>(SITES[1]);
  const [activeTab, setActiveTab] = useState('home');
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [currentRole, setCurrentRole] = useState<Role>('Admin');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newBatchAutoName, setNewBatchAutoName] = useState('');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Global Master Data State
  const [subcontractors, setSubcontractors] = useState<Subcontractor[]>(INITIAL_SUBCONTRACTORS);
  const [vendors, setVendors] = useState<Vendor[]>(INITIAL_VENDORS);
  const [scopes, setScopes] = useState([
    { name: 'Gypsum Work', count: 12 },
    { name: 'Blockwork', count: 8 },
    { name: 'Paints', count: 5 },
    { name: 'Tilework', count: 4 },
    { name: 'GSB Works', count: 2 },
  ]);

  const [vendorTypes, setVendorTypes] = useState([
    { name: 'Building Material', count: 45 },
    { name: 'RMC / Cement', count: 24 },
    { name: 'Hardware', count: 18 },
    { name: 'Steel (MS)', count: 12 },
  ]);

  const addSubcontractor = (sc: Subcontractor) => {
    setSubcontractors(prev => [sc, ...prev]);
  };

  const addScope = (name: string) => {
    if (!name.trim()) return;
    if (scopes.find(s => s.name.toLowerCase() === name.toLowerCase())) return;
    setScopes(prev => [{ name, count: 0 }, ...prev]);
  };

  const addVendorType = (name: string) => {
    if (!name.trim()) return;
    if (vendorTypes.find(v => v.name.toLowerCase() === name.toLowerCase())) return;
    setVendorTypes(prev => [{ name, count: 0 }, ...prev]);
  };

  // Define derivation variables before they are used in effects
  const isModuleMode = activeTab !== 'home';

  useEffect(() => {
    const handleHomeNav = () => {
      setActiveTab('home');
      setSelectedBatchId(null);
    };
    window.addEventListener('navigate-home', handleHomeNav);
    return () => window.removeEventListener('navigate-home', handleHomeNav);
  }, []);

  // Handle Role-based redirection
  useEffect(() => {
    if (isModuleMode && currentModule.id === 'fin') {
      if (currentRole === 'Approver' && activeTab !== 'fin-approvals' && activeTab !== 'fin-batch-detail') {
        setActiveTab('fin-approvals');
      }
    }
  }, [currentRole, currentModule.id, isModuleMode, activeTab]);

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  const generateBatchName = (type: 'K' | 'P') => {
    const now = new Date();
    const d = String(now.getDate()).padStart(2, '0');
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const y = String(now.getFullYear()).slice(-2);
    return `#${type}_${d}${m}${y}`;
  };

  const handleCreateBatchSelect = (type: 'K' | 'P') => {
    const name = generateBatchName(type);
    setNewBatchAutoName(name);
    setIsCreateModalOpen(false);
    setActiveTab('fin-batches-new');
  };

  const handleAppSelect = (moduleId: string) => {
    const mod = MODULES.find(m => m.id === moduleId);
    if (mod) {
      setCurrentModule(mod);
      if (mod.id === 'fin') {
        if (currentRole === 'Approver') {
          setActiveTab('fin-approvals');
        } else {
          setActiveTab('fin-overview');
        }
      } else if (mod.id === 'dir') {
        setActiveTab('dir-landing');
      } else {
        setActiveTab(mod.id);
      }
    }
  };

  const handleBreadcrumbNavigate = (id: string) => {
    if (id === 'home') {
      setActiveTab('home');
      setSelectedBatchId(null);
    } else if (MODULES.some(m => m.id === id)) {
      handleAppSelect(id);
    } else {
      setActiveTab(id);
      if (id !== 'fin-batch-detail') {
        setSelectedBatchId(null);
      }
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <AppLauncher onSelect={handleAppSelect} />;
      
      // Finance Tabs
      case 'fin-overview':
        return <FinanceOverview role={currentRole} onCreateNew={() => setIsCreateModalOpen(true)} />;
      case 'fin-batches':
        return (
          <FinancePaymentBatches 
            role={currentRole}
            onCreateNew={() => setIsCreateModalOpen(true)}
            onSelectBatch={(id) => {
              setSelectedBatchId(id);
              setActiveTab('fin-batch-detail');
            }}
          />
        );
      case 'fin-batch-detail':
        return (
          <BatchDetail 
            batchId={selectedBatchId || 'KHARCHI_24-10-2025'} 
            role={currentRole}
            onBack={() => {
              setSelectedBatchId(null);
              setActiveTab(currentRole === 'Approver' ? 'fin-approvals' : 'fin-batches');
            }}
          />
        );
      case 'fin-batches-new':
        return (
          <CreateBatch 
            role={currentRole}
            batchId={newBatchAutoName}
            subcontractors={subcontractors}
            vendors={vendors}
            onCancel={() => setActiveTab('fin-batches')} 
            onSave={() => setActiveTab('fin-batches')} 
            isSidebarCollapsed={isSidebarCollapsed}
          />
        );
      case 'fin-approvals':
        return (
          <FinanceApprovals 
            role={currentRole}
            onSelectBatch={(id) => {
              setSelectedBatchId(id);
              setActiveTab('fin-batch-detail');
            }}
          />
        );
      case 'fin-soa':
        return <SOAView />;

      // Directory Tabs
      case 'dir-landing':
        return <DirectoryLanding onNavigate={setActiveTab} />;
      case 'dir-sc':
        return (
          <Subcontractors 
            subcontractors={subcontractors}
            onAddSubcontractor={addSubcontractor}
            scopes={scopes.map(s => s.name)} 
            onAddScope={addScope} 
          />
        );
      case 'dir-vendors':
        return <Vendors vendors={vendors} vendorTypes={vendorTypes.map(v => v.name)} onAddVendorType={addVendorType} />;
      case 'dir-sites':
        return <Sites />;
      case 'dir-clients':
        return <Clients />;
      case 'dir-types':
        return (
          <TypesManagement 
            scopes={scopes} 
            onAddScope={addScope} 
            vendorTypes={vendorTypes} 
            onAddVendorType={addVendorType} 
          />
        );

      default:
        return (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 pb-6">
              <div>
                <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">{currentModule.name}</h2>
                <p className="text-slate-500 mt-1 max-w-2xl">{currentModule.description}</p>
              </div>
            </div>
            <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl h-96 flex flex-col items-center justify-center text-slate-400">
              <div className="p-4 bg-slate-50 rounded-full mb-4">
                {currentModule.icon}
              </div>
              <p className="text-sm font-bold uppercase tracking-widest text-slate-500">{currentModule.name} Module Content</p>
              <p className="text-xs font-medium mt-1 italic">Module screens pending design.</p>
            </div>
          </div>
        );
    }
  };

  const getActiveSidebarId = () => {
    if (activeTab === 'fin-batches-new' || activeTab === 'fin-batches-view' || activeTab === 'fin-batch-detail') {
      return 'fin-batches';
    }
    return activeTab;
  };

  const roles: Role[] = ['Admin', 'Creator', 'Approver', 'Viewer'];

  return (
    <div className="flex flex-col h-screen w-full bg-[#f8fafc] overflow-hidden">
      {/* Simulation View Switcher Bar */}
      <div className="h-10 bg-slate-900 flex items-center justify-center px-6 border-b border-slate-800 z-[120]">
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Simulation View:</span>
          <div className="flex bg-slate-800 p-0.5 rounded-lg border border-slate-700">
            {roles.map(role => (
              <button
                key={role}
                onClick={() => setCurrentRole(role)}
                className={`px-3 py-1 text-[10px] font-bold rounded-md transition-all ${
                  currentRole === role 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {role}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Header 
        currentModule={currentModule}
        onModuleChange={(mod) => {
          setCurrentModule(mod);
          // When switching module via header, adjust active tab
          if (mod.id === 'fin' && currentRole === 'Approver') {
             setActiveTab('fin-approvals');
          } else if (mod.id === 'fin') {
             setActiveTab('fin-overview');
          } else if (mod.id === 'dir') {
             setActiveTab('dir-landing');
          } else {
             setActiveTab(mod.id);
          }
        }}
        currentSite={currentSite}
        onSiteChange={setCurrentSite}
        isModuleMode={isModuleMode}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          role={currentRole}
          activeId={getActiveSidebarId()} 
          onNavigate={(id) => {
            setSelectedBatchId(null);
            setActiveTab(id);
          }} 
          isModuleMode={isModuleMode}
          moduleId={currentModule.id}
          onLogout={() => setIsLoggedIn(false)}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />

        <main className="flex-1 overflow-y-auto bg-slate-50 p-6 md:p-10">
          <div className="max-w-7xl mx-auto">
            <Breadcrumbs 
              currentModule={currentModule}
              activeTab={activeTab}
              selectedBatchId={selectedBatchId}
              onNavigate={handleBreadcrumbNavigate}
            />
            {renderContent()}
          </div>
        </main>
      </div>
      
      {/* Batch Type Selection Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" onClick={() => setIsCreateModalOpen(false)} />
          <div className="relative bg-white w-full max-w-md rounded-[2.5rem] shadow-2xl p-10 animate-in zoom-in-95 duration-200">
            <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-2 text-center">Create New Batch</h3>
            <p className="text-slate-500 font-medium text-sm mb-8 text-center px-4">
              Select the type of financial batch you wish to initialize.
            </p>
            <div className="grid grid-cols-1 gap-4">
              <button 
                onClick={() => handleCreateBatchSelect('K')}
                className="group flex items-center justify-between p-5 bg-slate-50 border border-slate-200 rounded-2xl hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
              >
                <div>
                  <p className="font-black text-slate-800 tracking-tight text-lg">Kharchi Request</p>
                  <p className="text-xs font-medium text-slate-500 mt-1">Petty cash and site maintenance</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
              </button>
              <button 
                onClick={() => handleCreateBatchSelect('P')}
                className="group flex items-center justify-between p-5 bg-slate-50 border border-slate-200 rounded-2xl hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
              >
                <div>
                  <p className="font-black text-slate-800 tracking-tight text-lg">Monthly Payment</p>
                  <p className="text-xs font-medium text-slate-500 mt-1">Vendor payouts and salary batches</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-10V4m-5 0V4h5M9 21h6" /></svg>
                </div>
              </button>
            </div>
            <button 
              onClick={() => setIsCreateModalOpen(false)}
              className="mt-6 w-full py-3 text-sm font-bold text-slate-400 hover:text-slate-600 transition-colors uppercase tracking-widest"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Floating Status Indicator */}
      <div className="fixed bottom-8 right-8 z-50 pointer-events-none">
        <div className="bg-slate-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-500 border border-slate-800">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-lg shadow-emerald-400/50" />
          <p className="text-sm font-bold tracking-tight">Active Persona: <span className="text-blue-400">{currentRole}</span></p>
        </div>
      </div>
    </div>
  );
};

export default App;
