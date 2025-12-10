import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: React.ReactNode;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, icon, error, className = '', type, ...props }) => {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type;

  return (
    <div className="w-full space-y-1.5">
      <label className="text-sm font-medium text-slate-300 ml-1">
        {label}
      </label>
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-cyan-400 transition-colors duration-300">
          {icon}
        </div>
        <input
          type={inputType}
          className={`
            w-full bg-slate-900/50 text-white placeholder-slate-500
            border border-slate-700/50 rounded-xl py-3 pl-10 ${isPassword ? 'pr-12' : 'pr-4'}
            focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50
            transition-all duration-300 hover:bg-slate-900/70 hover:border-slate-600
            ${error ? 'border-red-500/50 focus:ring-red-500/20' : ''}
            ${className}
          `}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-cyan-400 transition-colors duration-300 focus:outline-none"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        )}
      </div>
      {error && (
        <p className="text-xs text-red-400 ml-1 animate-pulse">
          {error}
        </p>
      )}
    </div>
  );
};
