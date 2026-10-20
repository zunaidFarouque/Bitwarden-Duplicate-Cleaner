import React, { useState } from 'react';
import {
  Globe,
  CheckCircle2,
  Trash2,
  RotateCcw,
  KeyRound,
  Edit3,
  Search,
} from 'lucide-react';
import type { DomainGroup, ItemSummary } from '../types';
import { AccountTable } from './AccountTable';

// --- Domain Duplicate Detail View ---
interface DomainViewProps {
  domainGroup: DomainGroup;
  onMerge: (domain: string, accountId: string, survivorId: string) => Promise<void>;
  onEditCell: (itemId: string, field: string, value: any) => Promise<void>;
  onPushValue: (domain: string, accountId: string, field: string, sourceItemId: string) => Promise<void>;
  onDeleteItem: (itemId: string) => Promise<void>;
}

export const DomainView: React.FC<DomainViewProps> = ({
  domainGroup,
  onMerge,
  onEditCell,
  onPushValue,
  onDeleteItem,
}) => {
  return (
    <div className="space-y-6">
      {/* Domain Header Banner */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100">{domainGroup.domain}</h2>
              {domainGroup.hasPasskeys && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-medium">
                  <KeyRound className="w-3.5 h-3.5" /> Contains Passkeys
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              {domainGroup.totalAccounts} unique account{domainGroup.totalAccounts > 1 ? 's' : ''} •{' '}
              {domainGroup.totalItems} duplicate logins
            </p>
          </div>
        </div>
      </div>

      {/* Account Tables */}
      <div className="space-y-6">
        {domainGroup.accounts.map((account) => (
          <AccountTable
            key={account.accountId}
            domain={domainGroup.domain}
            account={account}
            onMerge={onMerge}
            onEditCell={onEditCell}
            onPushValue={onPushValue}
            onDeleteItem={onDeleteItem}
          />
        ))}
      </div>
    </div>
  );
};

// --- Unique Items View ---
interface UniqueViewProps {
  items: ItemSummary[];
}

export const UniqueView: React.FC<UniqueViewProps> = ({ items }) => {
  const [filter, setFilter] = useState('');
  const filtered = items.filter(
    (i) =>
      i.name.toLowerCase().includes(filter.toLowerCase()) ||
      (i.username && i.username.toLowerCase().includes(filter.toLowerCase()))
  );

  return (
    <div className="space-y-5">
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Unique Logins</h2>
            <p className="text-xs text-slate-400">
              {items.length} items have zero duplicates. These remain safe and untouched in your vault.
            </p>
          </div>
        </div>

        <div className="relative w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search unique items..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-xs text-slate-200">
          <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold">
            <tr>
              <th className="py-2.5 px-4">Name</th>
              <th className="py-2.5 px-4">Username</th>
              <th className="py-2.5 px-4">Passkeys</th>
              <th className="py-2.5 px-4">Folder</th>
              <th className="py-2.5 px-4">URIs</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {filtered.map((item) => (
              <tr key={item.id} className="hover:bg-slate-700/30 transition">
                <td className="py-3 px-4 font-medium">{item.name}</td>
                <td className="py-3 px-4 font-mono text-slate-300">{item.username || '(None)'}</td>
                <td className="py-3 px-4">
                  {item.passkeyCount > 0 ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold">
                      <KeyRound className="w-3 h-3 text-amber-400" /> {item.passkeyCount} Passkey
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </td>
                <td className="py-3 px-4 text-slate-400">{item.folderName || '(None)'}</td>
                <td className="py-3 px-4 text-slate-400 truncate max-w-xs">{item.uris.join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Deleted / Trash View with Restore ---
interface DeletedViewProps {
  items: ItemSummary[];
  onRestore: (itemId: string) => Promise<void>;
}

export const DeletedView: React.FC<DeletedViewProps> = ({ items, onRestore }) => {
  return (
    <div className="space-y-5">
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl">
            <Trash2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Deleted Items (Trash)</h2>
            <p className="text-xs text-slate-400">
              {items.length} items will be excluded from the final export. You can restore any item at any time before export.
            </p>
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="p-12 text-center text-slate-500 bg-slate-800/40 rounded-2xl border border-slate-800 text-xs">
          Trash is currently empty. Redundant items removed during merges will appear here.
        </div>
      ) : (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold">
              <tr>
                <th className="py-2.5 px-4">Name</th>
                <th className="py-2.5 px-4">Username</th>
                <th className="py-2.5 px-4">Folder</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/30 transition">
                  <td className="py-3 px-4 font-medium line-through text-slate-400">{item.name}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{item.username || '(None)'}</td>
                  <td className="py-3 px-4 text-slate-500">{item.folderName || '(None)'}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onRestore(item.id)}
                      className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition inline-flex items-center gap-1.5 text-xs"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-emerald-400" /> Restore
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// --- Modified / Merged View ---
interface ModifiedViewProps {
  items: ItemSummary[];
}

export const ModifiedView: React.FC<ModifiedViewProps> = ({ items }) => {
  return (
    <div className="space-y-5">
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="p-3 bg-sky-500/10 border border-sky-500/20 text-sky-400 rounded-xl">
            <Edit3 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Modified & Merged Items</h2>
            <p className="text-xs text-slate-400">
              {items.length} items have been updated or consolidated in this session.
            </p>
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="p-12 text-center text-slate-500 bg-slate-800/40 rounded-2xl border border-slate-800 text-xs">
          No items modified yet in this session.
        </div>
      ) : (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold">
              <tr>
                <th className="py-2.5 px-4">Name</th>
                <th className="py-2.5 px-4">Username</th>
                <th className="py-2.5 px-4">Passkeys</th>
                <th className="py-2.5 px-4">Folder</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/30 transition">
                  <td className="py-3 px-4 font-medium text-sky-200">{item.name}</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{item.username || '(None)'}</td>
                  <td className="py-3 px-4">
                    {item.passkeyCount > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold">
                        <KeyRound className="w-3 h-3 text-amber-400" /> {item.passkeyCount} Passkey
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{item.folderName || '(None)'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
