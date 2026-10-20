import React, { useState, useRef } from 'react';
import { UploadCloud, KeyRound, AlertTriangle, HelpCircle, FileText, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import type { VaultStats } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (stats: VaultStats) => void;
  onOpenHelp: () => void;
}

export const ImportModal: React.FC<Props> = ({ isOpen, onClose, onImportSuccess, onOpenHelp }) => {
  const [file, setFile] = useState<File | null>(null);
  const [hasPasskeys, setHasPasskeys] = useState<boolean>(true);
  const [demoLoading, setDemoLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [pendingStats, setPendingStats] = useState<VaultStats | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setWarning(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setWarning(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a Bitwarden export file (.json)');
      return;
    }

    setLoading(true);
    setError(null);
    setWarning(null);

    try {
      const res = await api.uploadVault(file, hasPasskeys);
      if (res.stats.hasWarning && res.stats.warningMessage) {
        setWarning(res.stats.warningMessage);
        setPendingStats(res.stats);
      } else {
        onImportSuccess(res.stats);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload and parse vault');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemo = async () => {
    setDemoLoading(true);
    setError(null);
    setWarning(null);

    try {
      const res = await api.loadDemo();
      onImportSuccess(res.stats);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to load demo vault');
    } finally {
      setDemoLoading(false);
    }
  };

  const handleProceedWithWarning = () => {
    if (pendingStats) {
      onImportSuccess(pendingStats);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 text-slate-200">
        <h3 className="text-xl font-bold text-slate-100 mb-1">Import Bitwarden Vault</h3>
        <p className="text-xs text-slate-400 mb-5">
          Load your exported <code className="text-indigo-400 font-mono">.json</code> file to scan and clean duplicates locally.
        </p>

        {/* Warning Dialog if Passkeys claimed but none found */}
        {warning ? (
          <div className="space-y-4">
            <div className="p-4 bg-amber-500/15 border border-amber-500/30 rounded-xl text-amber-200">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-2 text-sm">
                  <h4 className="font-bold text-amber-300">No Passkeys Found in Export</h4>
                  <p className="text-slate-300">{warning}</p>
                  <p className="text-xs text-slate-400">
                    If you do not use passkeys, you can safely continue. If you do use passkeys, re-export from the Bitwarden Web Vault as unencrypted JSON so passkeys are included.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setWarning(null);
                  setPendingStats(null);
                  setFile(null);
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-xl transition"
              >
                Choose Another File
              </button>
              <button
                type="button"
                onClick={handleProceedWithWarning}
                className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-amber-600/20"
              >
                Proceed Without Passkeys
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Dropzone */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
                file
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-slate-600 hover:border-indigo-500/60 hover:bg-slate-700/30'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="flex flex-col items-center justify-center gap-2">
                {file ? (
                  <>
                    <FileText className="w-10 h-10 text-emerald-400" />
                    <span className="font-medium text-emerald-300 text-sm">{file.name}</span>
                    <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB • Click to change file</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-10 h-10 text-indigo-400" />
                    <span className="font-semibold text-slate-200 text-sm">
                      Drag & drop your Bitwarden <code className="text-indigo-400">.json</code> file here
                    </span>
                    <span className="text-xs text-slate-400">or click to browse your local files</span>
                  </>
                )}
              </div>
            </div>

            {/* Passkey Checkbox & Help Link */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 space-y-2">
              <label className="flex items-start gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={hasPasskeys}
                  onChange={(e) => setHasPasskeys(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded text-indigo-600 bg-slate-800 border-slate-600 focus:ring-indigo-500"
                />
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <KeyRound className="w-4 h-4 text-amber-400" />
                    <span className="font-medium text-slate-200 text-sm">I use passkeys in my Bitwarden vault</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    When enabled, the cleaner verifies hardware passkeys are present and warns you if they were omitted in the export.
                  </p>
                </div>
              </label>

              <button
                type="button"
                onClick={onOpenHelp}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 pt-1 pl-7 font-medium hover:underline"
              >
                <HelpCircle className="w-3.5 h-3.5" /> How do I export properly with passkeys?
              </button>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/15 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Try with Demo Data Banner */}
            <div className="flex items-center justify-between p-3.5 bg-indigo-950/40 border border-indigo-500/30 rounded-xl">
              <div className="flex items-center gap-2.5">
                <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                <div>
                  <div className="text-xs font-semibold text-slate-200">Try with Demo Data</div>
                  <div className="text-[11px] text-slate-400">Load realistic sample logins (Google, GitHub, Amazon duplicates + Passkeys).</div>
                </div>
              </div>
              <button
                type="button"
                disabled={loading || demoLoading}
                onClick={handleLoadDemo}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition whitespace-nowrap shadow-sm shadow-indigo-600/30"
              >
                {demoLoading ? 'Loading...' : 'Try Demo Vault'}
              </button>
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                disabled={loading || demoLoading}
                onClick={handleLoadDemo}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                {demoLoading ? 'Loading Demo...' : 'Try with Demo Data'}
              </button>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-slate-700/70 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!file || loading || demoLoading}
                  onClick={handleUpload}
                  className={`px-5 py-2 text-sm font-semibold rounded-xl transition shadow-lg ${
                    !file || loading || demoLoading
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed shadow-none'
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
                  }`}
                >
                  {loading ? 'Analyzing Vault...' : 'Load & Scan Vault'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
