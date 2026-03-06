
import React from 'react';
import { Button } from './UI/Primitives';

interface LoginProps {
  onLogin: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md">
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50 p-10 space-y-8 text-center">
          <div className="space-y-3">
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-white font-black text-3xl shadow-lg shadow-slate-900/20 overflow-hidden">
                <img src="https://raw.githubusercontent.com/seven-labs/assets/main/logo-77-white.png" alt="logo" className="w-10 h-10 object-contain" />
              </div>
            </div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">SEVEN Labs</h1>
            <p className="text-slate-500 font-medium">Enterprise Resource Planning System</p>
          </div>

          <div className="p-1 bg-slate-50 rounded-xl">
             <Button className="w-full h-14 text-lg font-bold bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-600/20 border-none rounded-lg" onClick={onLogin}>
               LOGIN TO SYSTEM
             </Button>
          </div>

          <div className="pt-4">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">
              Internal Corporate Network Access Only<br/>
              All sessions are monitored and recorded.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
