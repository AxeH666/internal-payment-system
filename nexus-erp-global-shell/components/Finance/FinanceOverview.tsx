
import React from 'react';
import { Badge, Button } from '../UI/Primitives';
import { Role } from '../../types';

interface FinanceOverviewProps {
  role: Role;
  onCreateNew?: () => void;
}

export const FinanceOverview: React.FC<FinanceOverviewProps> = ({ role, onCreateNew }) => {
  const canCreate = role === 'Admin' || role === 'Creator';

  const stats = [
    { title: 'Open Batches', value: '12', tag: 'Current', tagVariant: 'neutral' as const, iconColor: 'bg-slate-100 text-slate-600', icon: <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10v2h2V6a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" /></svg> },
    { title: 'Pending Approvals', value: '8', tag: 'Action Required', tagVariant: 'warning' as const, iconColor: 'bg-orange-50 text-orange-500', icon: <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM6 8a2 2 0 11-4 0 2 2 0 014 0zM11 18a4.993 4.993 0 00-1-3.048V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303a1.5 1.5 0 01-3 0V13a1 1 0 112 0v2.303" /></svg> },
    { title: 'Total Disbursed (Month)', value: '₹ 1.2M', tag: '+14% vs LY', tagVariant: 'success' as const, iconColor: 'bg-blue-50 text-blue-600', icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg> },
    { title: 'Outstanding Amount', value: '₹ 450k', tag: 'Aging 30d+', tagVariant: 'neutral' as const, iconColor: 'bg-slate-100 text-slate-600', icon: <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6h4v4H6v-4z" clipRule="evenodd" /></svg> },
  ];

  const activities = [
    { type: 'Batch Creation', icon: <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" /></svg>, iconBg: 'bg-blue-600', details: 'Batch #942 created with 14 transactions', user: 'System Admin', time: 'Today, 10:45 AM', status: 'COMPLETED', statusVariant: 'success' as const },
    { type: 'Approval Request', icon: <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" /></svg>, iconBg: 'bg-orange-500', details: 'Approval pending for Batch #938 ($142,500)', user: 'Finance Lead', time: 'Today, 09:12 AM', status: 'PENDING', statusVariant: 'warning' as const },
    { type: 'SOA Generation', icon: <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" /></svg>, iconBg: 'bg-slate-500', details: 'New SOA Version v2.4 generated for Q3', user: 'Controller Bot', time: 'Yesterday, 04:30 PM', status: 'ARCHIVED', statusVariant: 'neutral' as const },
    { type: 'Payment Processed', icon: <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>, iconBg: 'bg-emerald-600', details: 'Batch #930 disbursed successfully', user: 'System Admin', time: 'Yesterday, 02:15 PM', status: 'SUCCESS', statusVariant: 'success' as const },
    { type: 'Settings Update', icon: <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" /></svg>, iconBg: 'bg-blue-500', details: 'Threshold for Batch Approval updated to $50,000', user: 'Operations Dir.', time: 'Oct 24, 11:00 AM', status: 'OPEN', statusVariant: 'blue' as const },
  ];

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-400">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-1">
        <div>
          <h1 className="text-xl font-black text-slate-800 tracking-tight">Finance Overview</h1>
          <p className="text-slate-400 text-[10px] font-medium mt-0 opacity-80">Monitor and manage your organization's financial health and pending workflows.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" className="bg-white px-3 border-slate-200 text-slate-700 h-8 text-[10px] font-bold">
            <svg className="w-3 h-3 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            View Approvals
          </Button>
          {canCreate && (
            <Button onClick={onCreateNew} className="bg-blue-600 hover:bg-blue-700 text-white px-3 h-8 text-[10px] font-bold border-none shadow-md shadow-blue-600/20">
              <svg className="w-3.5 h-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
              Create New Batch
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white p-3 rounded-lg border border-slate-100 shadow-sm shadow-slate-900/5 relative overflow-hidden group flex flex-col justify-between h-24">
            <div className="flex justify-between items-center">
              <div className={`p-1.5 rounded-lg ${stat.iconColor} transition-transform group-hover:scale-110 duration-300`}>
                {React.cloneElement(stat.icon as React.ReactElement, { className: 'w-3.5 h-3.5' })}
              </div>
              <Badge variant={stat.tagVariant} className="text-[8px] px-1.5 py-0 leading-tight h-4 flex items-center">{stat.tag}</Badge>
            </div>
            <div className="mt-auto">
              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0">{stat.title}</p>
              <h2 className="text-xl font-black text-slate-800 tracking-tight leading-none">{stat.value}</h2>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Table */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-black text-slate-800 tracking-tight">Recent Financial Activity</h3>
          <button className="text-blue-600 font-bold text-[10px] hover:underline uppercase tracking-wider">View All Activity</button>
        </div>
        
        <div className="bg-white border border-slate-100 rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="border-b border-slate-100 bg-slate-50/50">
              <tr>
                <th className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-widest">Action Type</th>
                <th className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-widest">Details</th>
                <th className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-widest">User</th>
                <th className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-widest">Timestamp</th>
                <th className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-widest text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {activities.map((item, i) => (
                <tr key={i} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-md ${item.iconBg} flex items-center justify-center shrink-0`}>
                        {React.cloneElement(item.icon as React.ReactElement, { className: 'w-3 h-3' })}
                      </div>
                      <span className="text-[11px] font-black text-slate-800 truncate">{item.type}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-[11px] font-medium text-slate-500 max-w-xs truncate">{item.details}</td>
                  <td className="px-3 py-2 text-[11px] font-bold text-slate-600">{item.user}</td>
                  <td className="px-3 py-2 text-[11px] font-medium text-slate-400">{item.time}</td>
                  <td className="px-3 py-2 text-right">
                    <Badge variant={item.statusVariant} className="text-[8px] px-1.5 py-0 leading-tight h-4 flex items-center justify-center ml-auto">{item.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
