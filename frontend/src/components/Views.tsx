import React, { useState, useMemo } from 'react';
import {
  Globe,
  CheckCircle2,
  Trash2,
  RotateCcw,
  KeyRound,
  Edit3,
  Search,
  MoreVertical,
  Copy,
  Check,
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

// --- Unique Items View with Dynamic Column Visibility & 3-Dots Menu ---
interface UniqueViewProps {
  items: ItemSummary[];
}

export const UniqueView: React.FC<UniqueViewProps> = ({ items }) => {
  const [filter, setFilter] = useState('');
  const [showColumnMenu, setShowColumnMenu] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Determine whether any row in the dataset has content for each column
  const hasColumnData = useMemo(() => {
    return {
      name: true,
      username: items.some((i) => !!i.username),
      password: items.some((i) => !!i.password),
      totp: items.some((i) => !!i.totp),
      passkeys: items.some((i) => i.passkeyCount > 0),
      notes: items.some((i) => !!i.notes),
      folder: items.some((i) => !!i.folderName),
      uris: items.some((i) => i.uris && i.uris.length > 0),
    };
  }, [items]);

  // User-toggleable column visibility overrides
  const [columnVisibility, setColumnVisibility] = useState<Record<string, boolean>>({});

  const toggleColumn = (col: string) => {
    setColumnVisibility((prev) => ({
      ...prev,
      [col]: prev[col] !== undefined ? !prev[col] : !((hasColumnData as any)[col] ?? false),
    }));
  };

  // An active column is displayed if any row has it, unless user explicitly toggled it
  const isColVisible = (col: string) => {
    if (columnVisibility[col] !== undefined) {
      return columnVisibility[col];
    }
    return (hasColumnData as any)[col] ?? false;
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const filtered = items.filter(
    (i) =>
      i.name.toLowerCase().includes(filter.toLowerCase()) ||
      (i.username && i.username.toLowerCase().includes(filter.toLowerCase())) ||
      (i.notes && i.notes.toLowerCase().includes(filter.toLowerCase())) ||
      (i.uris && i.uris.some((u) => u.toLowerCase().includes(filter.toLowerCase())))
  );

  return (
    <div className="space-y-5">
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4">
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

        <div className="flex items-center gap-2">
          {/* Search Input */}
          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search unique items..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Three dots column customization menu */}
          <div className="relative">
            <button
              onClick={() => setShowColumnMenu((prev) => !prev)}
              className="p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 hover:text-white transition flex items-center gap-1 text-xs"
              title="Show / Hide Table Columns"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {showColumnMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl p-2 z-50 text-xs space-y-1">
                <div className="px-2 py-1 font-semibold text-slate-400 text-[10px] uppercase tracking-wider border-b border-slate-700/60 mb-1">
                  Customize Columns
                </div>
                {[
                  { key: 'name', label: 'Name' },
                  { key: 'username', label: 'Username' },
                  { key: 'password', label: 'Password' },
                  { key: 'totp', label: 'TOTP' },
                  { key: 'passkeys', label: 'Passkeys' },
                  { key: 'notes', label: 'Notes' },
                  { key: 'folder', label: 'Folder' },
                  { key: 'uris', label: 'URIs' },
                ].map(({ key, label }) => (
                  <label
                    key={key}
                    className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-700/60 rounded-lg cursor-pointer select-none text-slate-200"
                  >
                    <input
                      type="checkbox"
                      checked={isColVisible(key)}
                      onChange={() => toggleColumn(key)}
                      className="w-3.5 h-3.5 rounded text-indigo-600 bg-slate-900 border-slate-600 focus:ring-indigo-500"
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold tracking-wider">
              <tr>
                {isColVisible('name') && <th className="py-2.5 px-4">Name</th>}
                {isColVisible('username') && <th className="py-2.5 px-4">Username</th>}
                {isColVisible('password') && <th className="py-2.5 px-4">Password</th>}
                {isColVisible('totp') && <th className="py-2.5 px-4">TOTP</th>}
                {isColVisible('passkeys') && <th className="py-2.5 px-4">Passkeys</th>}
                {isColVisible('notes') && <th className="py-2.5 px-4">Notes</th>}
                {isColVisible('folder') && <th className="py-2.5 px-4">Folder</th>}
                {isColVisible('uris') && <th className="py-2.5 px-4">URIs</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {filtered.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/30 transition">
                  {/* Name */}
                  {isColVisible('name') && (
                    <td className="py-3 px-4 font-medium truncate max-w-[160px]" title={item.name}>
                      {item.name}
                    </td>
                  )}

                  {/* Username */}
                  {isColVisible('username') && (
                    <td
                      className="py-3 px-4 font-mono text-slate-300 truncate max-w-[160px]"
                      title={item.username || '(None)'}
                    >
                      {item.username || '(None)'}
                    </td>
                  )}

                  {/* Password (in plain text for immediate comparison & audit) */}
                  {isColVisible('password') && (
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="font-mono text-slate-200 truncate max-w-[140px] select-all"
                          title={item.password || '(Empty)'}
                        >
                          {item.password || '(Empty)'}
                        </span>
                        {item.password && (
                          <button
                            onClick={() => copyToClipboard(item.password || '', item.id)}
                            className="p-1 text-slate-400 hover:text-slate-200 transition"
                            title="Copy password"
                          >
                            {copiedId === item.id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                  )}

                  {/* TOTP */}
                  {isColVisible('totp') && (
                    <td className="py-3 px-4">
                      {item.totp ? (
                        <span
                          className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono font-medium"
                          title={item.totp}
                        >
                          Configured
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]" title="No TOTP configured">
                          —
                        </span>
                      )}
                    </td>
                  )}

                  {/* Passkeys */}
                  {isColVisible('passkeys') && (
                    <td className="py-3 px-4">
                      {item.passkeyCount > 0 ? (
                        <span
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold"
                          title={
                            item.passkeyDetails.length > 0
                              ? item.passkeyDetails
                                  .map((p) => `${p.rpId || 'Passkey'} (${p.userName || ''})`)
                                  .join(', ')
                              : `${item.passkeyCount} Passkey(s)`
                          }
                        >
                          <KeyRound className="w-3 h-3 text-amber-400" /> {item.passkeyCount} Passkey
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]" title="No passkeys">
                          —
                        </span>
                      )}
                    </td>
                  )}

                  {/* Notes */}
                  {isColVisible('notes') && (
                    <td
                      className="py-3 px-4 text-slate-400 text-[11px] truncate max-w-[130px]"
                      title={item.notes || '(No notes)'}
                    >
                      {item.notes || '—'}
                    </td>
                  )}

                  {/* Folder */}
                  {isColVisible('folder') && (
                    <td
                      className="py-3 px-4 text-slate-400 truncate max-w-[120px]"
                      title={item.folderName || '(None)'}
                    >
                      {item.folderName || '(None)'}
                    </td>
                  )}

                  {/* URIs */}
                  {isColVisible('uris') && (
                    <td
                      className="py-3 px-4 text-slate-400 truncate max-w-xs"
                      title={item.uris.join(', ') || 'No URIs'}
                    >
                      {item.uris.join(', ') || '—'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// --- Deleted / Trash View with Restore & Tooltips ---
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
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Name</th>
                <th className="py-2.5 px-4">Username</th>
                <th className="py-2.5 px-4">Password</th>
                <th className="py-2.5 px-4">Folder</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/30 transition">
                  <td
                    className="py-3 px-4 font-medium line-through text-slate-400 truncate max-w-[160px]"
                    title={item.name}
                  >
                    {item.name}
                  </td>
                  <td
                    className="py-3 px-4 font-mono text-slate-400 truncate max-w-[160px]"
                    title={item.username || '(None)'}
                  >
                    {item.username || '(None)'}
                  </td>
                  <td
                    className="py-3 px-4 font-mono text-slate-400 truncate max-w-[140px]"
                    title={item.password || '(Empty)'}
                  >
                    {item.password || '(Empty)'}
                  </td>
                  <td
                    className="py-3 px-4 text-slate-500 truncate max-w-[120px]"
                    title={item.folderName || '(None)'}
                  >
                    {item.folderName || '(None)'}
                  </td>
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

// --- Modified / Merged View with Tooltips ---
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
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] font-semibold tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Name</th>
                <th className="py-2.5 px-4">Username</th>
                <th className="py-2.5 px-4">Password</th>
                <th className="py-2.5 px-4">Passkeys</th>
                <th className="py-2.5 px-4">Folder</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-slate-700/30 transition">
                  <td
                    className="py-3 px-4 font-medium text-sky-200 truncate max-w-[160px]"
                    title={item.name}
                  >
                    {item.name}
                  </td>
                  <td
                    className="py-3 px-4 font-mono text-slate-300 truncate max-w-[160px]"
                    title={item.username || '(None)'}
                  >
                    {item.username || '(None)'}
                  </td>
                  <td
                    className="py-3 px-4 font-mono text-slate-200 truncate max-w-[140px]"
                    title={item.password || '(Empty)'}
                  >
                    {item.password || '(Empty)'}
                  </td>
                  <td className="py-3 px-4">
                    {item.passkeyCount > 0 ? (
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold"
                        title={
                          item.passkeyDetails.length > 0
                            ? item.passkeyDetails
                                .map((p) => `${p.rpId || 'Passkey'} (${p.userName || ''})`)
                                .join(', ')
                            : `${item.passkeyCount} Passkey(s)`
                        }
                      >
                        <KeyRound className="w-3 h-3 text-amber-400" /> {item.passkeyCount} Passkey
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td
                    className="py-3 px-4 text-slate-400 truncate max-w-[120px]"
                    title={item.folderName || '(None)'}
                  >
                    {item.folderName || '(None)'}
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
