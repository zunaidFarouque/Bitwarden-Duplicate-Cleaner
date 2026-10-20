import React from 'react';
import { ShieldCheck, Undo2, Redo2, Upload, Download, KeyRound } from 'lucide-react';
import type { VaultStats } from '../types';

interface Props {
  stats?: VaultStats;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onOpenImport: () => void;
  onOpenExport: () => void;
}

export const Navbar: React.FC<Props> = ({
  stats,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onOpenImport,
  onOpenExport,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40 select-none">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-500 rounded-xl text-white shadow-md shadow-indigo-600/30">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 text-sm tracking-tight">
            Bitwarden Duplicate Cleaner
          </h1>
          <p className="text-[11px] text-slate-400">Zero Internet • Privacy First • Passkey Safe</p>
        </div>
      </div>

      {/* Vault Badges & Metrics */}
      {stats && (
        <div className="hidden md:flex items-center gap-2">
          <div className="px-3 py-1 bg-slate-800/80 border border-slate-700/60 rounded-lg text-xs flex items-center gap-1.5">
            <span className="text-slate-400">Items:</span>
            <span className="font-semibold text-slate-200">{stats.totalItems}</span>
          </div>

          <div className={`px-3 py-1 rounded-lg text-xs flex items-center gap-1.5 border ${
            stats.duplicateCount > 0
              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
          }`}>
            <span className="text-slate-400">Duplicates:</span>
            <span className="font-bold">{stats.duplicateCount}</span>
          </div>

          {stats.passkeyTotalCount > 0 && (
            <div className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-lg text-xs flex items-center gap-1.5">
              <KeyRound className="w-3.5 h-3.5 text-amber-400" />
              <span>Passkeys:</span>
              <span className="font-bold">{stats.passkeyTotalCount}</span>
            </div>
          )}
        </div>
      )}

      {/* Action Controls */}
      <div className="flex items-center gap-2">
        {/* Undo / Redo */}
        <div className="flex items-center bg-slate-800 border border-slate-700/60 rounded-xl p-0.5 mr-2">
          <button
            title="Undo (Ctrl+Z)"
            disabled={!canUndo}
            onClick={onUndo}
            className={`p-2 rounded-lg transition ${
              canUndo
                ? 'text-slate-200 hover:text-white hover:bg-slate-700 cursor-pointer'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <div className="w-[1px] h-4 bg-slate-700 my-auto" />
          <button
            title="Redo (Ctrl+Y)"
            disabled={!canRedo}
            onClick={onRedo}
            className={`p-2 rounded-lg transition ${
              canRedo
                ? 'text-slate-200 hover:text-white hover:bg-slate-700 cursor-pointer'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <Redo2 className="w-4 h-4" />
          </button>
        </div>

        {/* Import */}
        <button
          onClick={onOpenImport}
          className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5"
        >
          <Upload className="w-3.5 h-3.5" /> Import
        </button>

        {/* Export */}
        <button
          onClick={onOpenExport}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow-md shadow-indigo-600/25"
        >
          <Download className="w-3.5 h-3.5" /> Export Clean JSON
        </button>
      </div>
    </header>
  );
};
