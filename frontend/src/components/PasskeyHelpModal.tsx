import React from 'react';
import { X, KeyRound, ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const PasskeyHelpModal: React.FC<Props> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 text-slate-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-700/50 rounded-lg transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <KeyRound className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-100">How to Export Bitwarden with Passkeys</h3>
            <p className="text-xs text-slate-400">Step-by-step guide to ensure hardware security credentials are preserved</p>
          </div>
        </div>

        <div className="space-y-4 text-sm">
          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-200">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
              <div>
                <strong className="font-semibold block text-amber-300">Crucial: Never Export as CSV for Passkeys</strong>
                CSV exports from Bitwarden <strong>strip all passkeys (FIDO2 credentials)</strong>, password histories, and custom field structures. Always export as <strong>JSON</strong>.
              </div>
            </div>
          </div>

          <div className="space-y-3 bg-slate-900/60 p-4 rounded-xl border border-slate-700/50">
            <h4 className="font-semibold text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Recommended Steps in Bitwarden Web Vault:
            </h4>
            <ol className="list-decimal list-inside space-y-2 text-slate-300 pl-1">
              <li>Log in to your <strong>Bitwarden Web Vault</strong> (<span className="text-slate-400">vault.bitwarden.com</span> or self-hosted).</li>
              <li>Click on the <strong>Tools</strong> tab in the top navigation bar.</li>
              <li>Select <strong>Export Vault</strong> from the left menu.</li>
              <li>Under <strong>File Format</strong>, choose either:
                <ul className="list-disc list-inside pl-5 mt-1 text-slate-400 space-y-1">
                  <li><strong className="text-slate-200">.json</strong> (Unencrypted - recommended for local processing)</li>
                  <li>Or <strong className="text-slate-200">.json (Password-Protected)</strong></li>
                </ul>
              </li>
              <li>Enter your master password and click <strong>Export Vault</strong> to save the file.</li>
            </ol>
          </div>

          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-200 text-xs flex items-center gap-2.5">
            <ShieldAlert className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>
              <strong>100% Offline Peace of Mind:</strong> This application runs entirely on your local machine (<code className="bg-emerald-950/60 px-1 py-0.5 rounded text-emerald-300">127.0.0.1</code>) and never transmits any vault data over the internet.
            </span>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition shadow-lg shadow-indigo-600/20"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};
