
import React from 'react';

// Added 'disabled' prop to Button component to support button state management
export const Button: React.FC<{
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
}> = ({ children, variant = 'primary', size = 'md', className = '', onClick, type = 'button', disabled }) => {
  const base = "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  
  const variants = {
    primary: "bg-slate-900 text-white hover:bg-slate-800",
    secondary: "bg-white border border-slate-200 text-slate-900 hover:bg-slate-50",
    ghost: "bg-transparent hover:bg-slate-100 text-slate-600",
    danger: "bg-red-600 text-white hover:bg-red-700"
  };

  const sizes = {
    sm: "h-7 px-2 text-[10px]",
    md: "h-9 px-4 text-xs",
    lg: "h-11 px-6 text-sm"
  };

  return (
    <button 
      type={type} 
      onClick={onClick} 
      disabled={disabled}
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </button>
  );
};

export const Badge: React.FC<{
  children: React.ReactNode;
  variant?: 'neutral' | 'success' | 'warning' | 'error' | 'blue' | 'partial' | 'paid';
}> = ({ children, variant = 'neutral' }) => {
  const styles = {
    neutral: "bg-slate-100 text-slate-500 border-slate-200 uppercase text-[9px] tracking-wider",
    success: "bg-emerald-50 text-emerald-600 border-emerald-100 uppercase text-[9px] tracking-wider",
    warning: "bg-orange-50 text-orange-600 border-orange-100 uppercase text-[9px] tracking-wider",
    error: "bg-rose-50 text-rose-700 border-rose-100 uppercase text-[9px] tracking-wider",
    blue: "bg-blue-50 text-blue-700 border-blue-100 uppercase text-[9px] tracking-wider",
    partial: "bg-purple-50 text-purple-700 border-purple-100 uppercase text-[9px] tracking-wider",
    paid: "bg-emerald-900 text-emerald-50 border-emerald-800 uppercase text-[9px] tracking-wider"
  };

  return (
    <span className={`inline-flex items-center px-1 py-0 rounded font-bold border ${styles[variant]}`}>
      {children}
    </span>
  );
};

export const Card: React.FC<{
  title?: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}> = ({ title, children, className = '', actions }) => (
  <div className={`bg-white border border-slate-200 rounded shadow-sm ${className}`}>
    {(title || actions) && (
      <div className="px-3 py-2 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        {title && <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">{title}</h3>}
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
    )}
    <div className="p-3">{children}</div>
  </div>
);

export const Table: React.FC<{
  headers: string[];
  rows: React.ReactNode[][];
}> = ({ headers, rows }) => (
  <div className="w-full overflow-hidden border border-slate-200">
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[11px] border-collapse">
        <thead className="bg-slate-100 border-b border-slate-300">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2.5 font-bold text-slate-600 border-r border-slate-200 last:border-r-0 uppercase tracking-tight">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-blue-50/30 transition-colors">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2.5 text-slate-600 whitespace-nowrap border-r border-slate-100 last:border-r-0">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);
