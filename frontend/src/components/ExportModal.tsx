import React from 'react';
import { Download, ShieldCheck, FileCheck2, X } from 'lucide-react';
import { api } from '../api/client';
import type { VaultStats } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  stats?: VaultStats;
}

export const ExportModal: React.FC<Props> = ({ isOpen, onClose, stats }) => {
  if (!isOpen) return null;

  const handleDownload = () => {
    window.location.href = api.getExportUrl();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 text-slate-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-700/50 rounded-lg transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
            <FileCheck2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100">Ready to Export Cleaned Vault</h3>
            <p className="text-xs text-slate-400">Download your deduplicated Bitwarden JSON and import it with peace of mind</p>
          </div>
        </div>

        {/* Stats Summary Grid */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/60 text-center">
            <span className="text-xs text-slate-400 block mb-0.5">Active Items</span>
            <span className="text-lg font-bold text-slate-100">{stats?.totalItems ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/60 text-center">
            <span className="text-xs text-slate-400 block mb-0.5">Duplicates Cleaned</span>
            <span className="text-lg font-bold text-emerald-400">{stats?.deletedCount ?? 0}</span>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/60 text-center">
            <span className="text-xs text-slate-400 block mb-0.5">Passkeys Preserved</span>
            <span className="text-lg font-bold text-indigo-400">{stats?.passkeyTotalCount ?? 0}</span>
          </div>
        </div>

        {/* Download Button */}
        <div className="mb-6">
          <button
            onClick={handleDownload}
            className="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 text-base"
          >
            <Download className="w-5 h-5" /> Download Cleaned Bitwarden JSON
          </button>
        </div>

        {/* Step by step import instructions */}
        <div className="space-y-3 bg-slate-900/60 p-4 rounded-xl border border-slate-700/50 text-sm">
          <h4 className="font-semibold text-slate-100 flex items-center gap-2 text-sm">
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> How to Safely Import Back into Bitwarden:
          </h4>
          <ol className="list-decimal list-inside space-y-2 text-slate-300 text-xs leading-relaxed">
            <li>
              <strong>Your original backup is already safe:</strong> We automatically saved a copy of your original vault file before cleaning in your local <code className="bg-slate-800 px-1 py-0.5 rounded text-indigo-300">backups/</code> folder.
            </li>
            <li>
              <strong>Log in to Bitwarden Web Vault:</strong> Navigate to <span className="text-slate-200">Tools &rarr; Import Data</span>.
            </li>
            <li>
              <strong>Select Format:</strong> Choose <strong className="text-slate-100">Bitwarden (JSON)</strong>.
            </li>
            <li>
              <strong>Select File:</strong> Choose the downloaded <code className="text-emerald-300">bitwarden_cleaned_export.json</code>.
            </li>
            <li>
              <span className="text-amber-300 font-medium">Important Note:</span> Bitwarden imports <em>append</em> to your existing vault by default. To avoid having both old and new items side-by-side, you can either:
              <ul className="list-disc list-inside pl-4 mt-1 space-y-1 text-slate-400">
                <li>Purge your vault (<span className="text-slate-300">Settings &rarr; My Account &rarr; Purge Vault</span>) after verifying your backup, then import.</li>
                <li>Or import into a specific subfolder or test organization first.</li>
              </ul>
            </li>
          </ol>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-xl transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
