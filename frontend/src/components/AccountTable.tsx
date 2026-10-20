import React, { useState, useMemo } from 'react';
import {
  KeyRound,
  Edit2,
  Check,
  X,
  Trash2,
  ArrowRightLeft,
  Sparkles,
  Copy,
  ShieldCheck,
  Globe,
  Unlink,
} from 'lucide-react';
import type { AccountGroup, ItemSummary } from '../types';

interface Props {
  domain: string;
  account: AccountGroup;
  onMerge: (domain: string, accountId: string, survivorId: string) => Promise<void>;
  onEditCell: (itemId: string, field: string, value: any) => Promise<void>;
  onPushValue: (domain: string, accountId: string, field: string, sourceItemId: string) => Promise<void>;
  onDeleteItem: (itemId: string) => Promise<void>;
  onSeparateItem: (itemId: string) => Promise<void>;
  onSetItemDomain: (itemId: string, domain: string) => Promise<void>;
  onMoveItemsDomain: (itemIds: string[], domain: string) => Promise<void>;
}

export const AccountTable: React.FC<Props> = ({
  domain,
  account,
  onMerge,
  onEditCell,
  onPushValue,
  onDeleteItem,
  onSeparateItem,
  onSetItemDomain,
  onMoveItemsDomain,
}) => {
  // Default survivor is the first item or the one with passkeys/most fields
  const [survivorId, setSurvivorId] = useState<string>(() => {
    const withPasskeys = account.items.find((it) => it.passkeyCount > 0);
    return withPasskeys ? withPasskeys.id : account.items[0]?.id || '';
  });

  const [editingRowId, setEditingRowId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Partial<ItemSummary>>({});
  const [merging, setMerging] = useState(false);
  const [, setCopiedId] = useState<string | null>(null);

  // Multi-selection state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Move Modal State
  const [moveModal, setMoveModal] = useState<{
    itemIds: string[];
    title: string;
  } | null>(null);
  const [targetDomainInput, setTargetDomainInput] = useState('');
  const [suggestedDomains, setSuggestedDomains] = useState<string[]>([]);
  const [isMoving, setIsMoving] = useState(false);

  // Dynamic column detection: A column is only rendered if at least one duplicate row has data for it
  const hasColumn = useMemo(() => {
    return {
      name: true, // Always show Name column
      username: account.items.some((i) => i.username && i.username.trim() !== ''),
      password: account.items.some((i) => i.password && i.password.trim() !== ''),
      totp: account.items.some((i) => i.totp && i.totp.trim() !== ''),
      passkeys: account.items.some((i) => i.passkeyCount > 0),
      notes: account.items.some((i) => i.notes && i.notes.trim() !== ''),
      folder: account.items.some((i) => i.folderName && i.folderName.trim() !== ''),
      uris: account.items.some((i) => i.uris && i.uris.length > 0),
    };
  }, [account.items]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const startEditing = (item: ItemSummary) => {
    setEditingRowId(item.id);
    setEditValues({
      name: item.name,
      username: item.username || '',
      password: item.password || '',
      totp: item.totp || '',
      notes: item.notes || '',
    });
  };

  const cancelEditing = () => {
    setEditingRowId(null);
    setEditValues({});
  };

  const saveEditing = async (itemId: string) => {
    try {
      const original = account.items.find((i) => i.id === itemId);
      if (!original) return;

      if (editValues.name !== undefined && editValues.name !== original.name) {
        await onEditCell(itemId, 'name', editValues.name);
      }
      if (editValues.username !== undefined && editValues.username !== original.username) {
        await onEditCell(itemId, 'username', editValues.username);
      }
      if (editValues.password !== undefined && editValues.password !== original.password) {
        await onEditCell(itemId, 'password', editValues.password);
      }
      if (editValues.totp !== undefined && editValues.totp !== original.totp) {
        await onEditCell(itemId, 'totp', editValues.totp);
      }
      if (editValues.notes !== undefined && editValues.notes !== original.notes) {
        await onEditCell(itemId, 'notes', editValues.notes);
      }
      setEditingRowId(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMerge = async () => {
    if (!survivorId) return;
    setMerging(true);
    try {
      await onMerge(domain, account.accountId, survivorId);
    } finally {
      setMerging(false);
    }
  };

  const isDiff = (field: string) => account.diffFields.includes(field);

  // Multi-select helpers
  const toggleSelectItem = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === account.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(account.items.map((i) => i.id));
    }
  };

  const extractSuggestedDomains = (items: ItemSummary[]): string[] => {
    const set = new Set<string>();
    for (const it of items) {
      for (const uri of it.uris || []) {
        const u = uri.toLowerCase();
        if (u.startsWith('androidapp://')) {
          const pkg = u.replace('androidapp://', '').split('/')[0];
          const parts = pkg.split('.');
          if (parts.length >= 2) {
            if (['com', 'org', 'net', 'io', 'edu', 'app'].includes(parts[0])) {
              set.add(`${parts[1]}.${parts[0]}`);
            } else if (['com', 'org', 'net', 'io', 'edu', 'app'].includes(parts[parts.length - 1])) {
              set.add(`${parts[parts.length - 2]}.${parts[parts.length - 1]}`);
            } else {
              set.add(parts.slice(-2).join('.'));
            }
          }
        } else {
          try {
            const host = new URL(u.startsWith('http') ? u : `https://${u}`).hostname;
            const hParts = host.split('.');
            if (hParts.length >= 2) {
              set.add(hParts.slice(-2).join('.'));
            }
          } catch {
            // Ignore
          }
        }
      }
      // If name matches clean pattern
      const cleanName = it.name.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
      if (cleanName && cleanName.length > 2 && !set.has(`${cleanName}.com`)) {
        set.add(`${cleanName}.com`);
      }
    }
    // Remove current domain if in suggestion set
    set.delete(domain.toLowerCase());
    return Array.from(set).slice(0, 4);
  };

  const openMoveModal = (itemIds: string[], title: string) => {
    const targetItems = account.items.filter((i) => itemIds.includes(i.id));
    const suggestions = extractSuggestedDomains(targetItems);
    setSuggestedDomains(suggestions);
    setTargetDomainInput(suggestions[0] || '');
    setMoveModal({ itemIds, title });
  };

  const handleConfirmMove = async () => {
    if (!moveModal || !targetDomainInput.trim()) return;
    setIsMoving(true);
    try {
      if (moveModal.itemIds.length === 1) {
        await onSetItemDomain(moveModal.itemIds[0], targetDomainInput.trim());
      } else {
        await onMoveItemsDomain(moveModal.itemIds, targetDomainInput.trim());
      }
      setMoveModal(null);
      setSelectedIds([]);
    } finally {
      setIsMoving(false);
    }
  };

  const handleSeparateSelected = async () => {
    for (const id of selectedIds) {
      await onSeparateItem(id);
    }
    setSelectedIds([]);
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl mb-6">
      {/* Account Header */}
      <div className="px-5 py-3.5 bg-slate-800/90 border-b border-slate-700/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/15 border border-indigo-500/25 text-indigo-400 rounded-xl">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-100 text-sm">{account.displayUsername}</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-700/80 text-slate-300">
                norm: {account.normalizedUsername}
              </span>
              {account.hasPasskeys && (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                  <KeyRound className="w-3 h-3" /> Has Passkeys
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              {account.itemCount} duplicate entries found for this account
            </p>
          </div>
        </div>

        {/* Diff Tags */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] uppercase font-semibold text-slate-400 mr-1">Diffs:</span>
          {account.diffFields.length === 0 ? (
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
              Identical Duplicates
            </span>
          ) : (
            account.diffFields.map((f) => (
              <span
                key={f}
                className="text-[10px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold"
              >
                {f}
              </span>
            ))
          )}
        </div>
      </div>

      {/* Bulk Action Ribbon when rows are selected */}
      {selectedIds.length > 0 && (
        <div className="px-5 py-2.5 bg-indigo-950/70 border-b border-indigo-700/50 flex flex-wrap items-center justify-between gap-2 animate-in fade-in">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-200">
              {selectedIds.length} of {account.items.length} row{selectedIds.length > 1 ? 's' : ''} selected
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => openMoveModal(selectedIds, `${selectedIds.length} Logins`)}
              className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition flex items-center gap-1.5 shadow-sm"
              title="Move and group selected rows under a chosen website domain"
            >
              <Globe className="w-3.5 h-3.5" /> Move to Website...
            </button>
            <button
              onClick={handleSeparateSelected}
              className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-amber-200 text-xs font-medium rounded-lg transition flex items-center gap-1.5 shadow-sm"
              title="Mark selected logins as separate/unique"
            >
              <Unlink className="w-3.5 h-3.5 text-amber-400" /> Separate as Unique
            </button>
            <button
              onClick={() => setSelectedIds([])}
              className="px-2 py-1 text-slate-400 hover:text-slate-200 text-xs"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-200">
          <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] tracking-wider font-semibold">
            <tr>
              <th className="py-2.5 px-2 text-center w-8">
                <input
                  type="checkbox"
                  checked={selectedIds.length === account.items.length && account.items.length > 0}
                  onChange={toggleSelectAll}
                  className="w-3.5 h-3.5 text-indigo-600 rounded bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                  title="Select all rows"
                />
              </th>
              <th className="py-2.5 px-3 text-center w-14">Survivor</th>
              {hasColumn.name && (
                <th className={`py-2.5 px-3 ${isDiff('name') ? 'text-amber-400' : ''}`}>Name</th>
              )}
              {hasColumn.username && (
                <th className={`py-2.5 px-3 ${isDiff('username') ? 'text-amber-400' : ''}`}>Username</th>
              )}
              {hasColumn.password && (
                <th className={`py-2.5 px-3 ${isDiff('password') ? 'text-amber-400' : ''}`}>Password</th>
              )}
              {hasColumn.totp && (
                <th className={`py-2.5 px-3 ${isDiff('totp') ? 'text-amber-400' : ''}`}>TOTP</th>
              )}
              {hasColumn.passkeys && (
                <th className={`py-2.5 px-3 ${isDiff('passkeys') ? 'text-amber-400' : ''}`}>Passkeys</th>
              )}
              {hasColumn.notes && (
                <th className={`py-2.5 px-3 ${isDiff('notes') ? 'text-amber-400' : ''}`}>Notes</th>
              )}
              {hasColumn.folder && <th className="py-2.5 px-3">Folder</th>}
              {hasColumn.uris && (
                <th className={`py-2.5 px-3 ${isDiff('uris') ? 'text-amber-400' : ''}`}>URIs</th>
              )}
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {account.items.map((item) => {
              const isSurvivor = survivorId === item.id;
              const isEditing = editingRowId === item.id;
              const isSelected = selectedIds.includes(item.id);

              return (
                <tr
                  key={item.id}
                  className={`transition ${
                    isSelected
                      ? 'bg-indigo-950/40'
                      : isSurvivor
                      ? 'bg-indigo-600/10 hover:bg-indigo-600/15'
                      : 'hover:bg-slate-700/30'
                  }`}
                >
                  {/* Select Checkbox */}
                  <td className="py-3 px-2 text-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelectItem(item.id)}
                      className="w-3.5 h-3.5 text-indigo-600 rounded bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                    />
                  </td>

                  {/* Survivor Radio */}
                  <td className="py-3 px-3 text-center">
                    <input
                      type="radio"
                      name={`survivor-${account.accountId}`}
                      checked={isSurvivor}
                      onChange={() => setSurvivorId(item.id)}
                      className="w-4 h-4 text-indigo-600 bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                      title="Set as survivor for merge"
                    />
                  </td>

                  {/* Name Cell */}
                  {hasColumn.name && (
                    <td className="py-3 px-3 font-medium text-slate-100 group/cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.name || ''}
                          onChange={(e) => setEditValues({ ...editValues, name: e.target.value })}
                          className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-1">
                          <span className="truncate max-w-[140px]" title={item.name}>
                            {item.name}
                          </span>
                          {isDiff('name') && (
                            <button
                              title="Push this name to all duplicates"
                              onClick={() =>
                                onPushValue(domain, account.accountId, 'name', item.id)
                              }
                              className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-700 text-slate-400 hover:text-amber-300 rounded transition"
                            >
                              <ArrowRightLeft className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}

                  {/* Username Cell */}
                  {hasColumn.username && (
                    <td className="py-3 px-3 text-slate-300 font-mono text-[11px] group/cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.username || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, username: e.target.value })
                          }
                          className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-1">
                          <span
                            className="truncate max-w-[140px]"
                            title={item.username || '(None)'}
                          >
                            {item.username || '—'}
                          </span>
                          {isDiff('username') && item.username && (
                            <button
                              title="Push this username to all duplicates"
                              onClick={() =>
                                onPushValue(domain, account.accountId, 'username', item.id)
                              }
                              className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-700 text-slate-400 hover:text-amber-300 rounded transition"
                            >
                              <ArrowRightLeft className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}

                  {/* Password Cell (Plain Text by default, hover tooltip for full text) */}
                  {hasColumn.password && (
                    <td className="py-3 px-3 text-slate-300 font-mono text-[11px] group/cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.password || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, password: e.target.value })
                          }
                          className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-1">
                          <span
                            className="truncate max-w-[130px] font-mono text-slate-200 select-all cursor-text"
                            title={item.password || 'No password'}
                          >
                            {item.password || '—'}
                          </span>
                          <div className="flex items-center opacity-0 group-hover/cell:opacity-100 transition">
                            {item.password && (
                              <button
                                onClick={() => copyToClipboard(item.password!, `pw-${item.id}`)}
                                className="p-1 hover:bg-slate-700 text-slate-400 hover:text-slate-200 rounded"
                                title="Copy password"
                              >
                                <Copy className="w-3 h-3" />
                              </button>
                            )}
                            {isDiff('password') && item.password && (
                              <button
                                title="Push this password to all duplicates"
                                onClick={() =>
                                  onPushValue(domain, account.accountId, 'password', item.id)
                                }
                                className="p-1 hover:bg-slate-700 text-slate-400 hover:text-amber-300 rounded"
                              >
                                <ArrowRightLeft className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </td>
                  )}

                  {/* TOTP Cell */}
                  {hasColumn.totp && (
                    <td className="py-3 px-3 text-slate-300 font-mono text-[11px] group/cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.totp || ''}
                          onChange={(e) => setEditValues({ ...editValues, totp: e.target.value })}
                          className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-1">
                          <span
                            className="truncate max-w-[100px]"
                            title={item.totp || 'No TOTP secret'}
                          >
                            {item.totp ? 'otpauth://...' : '—'}
                          </span>
                          {isDiff('totp') && item.totp && (
                            <button
                              title="Push this TOTP secret to all duplicates"
                              onClick={() =>
                                onPushValue(domain, account.accountId, 'totp', item.id)
                              }
                              className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-700 text-slate-400 hover:text-amber-300 rounded transition"
                            >
                              <ArrowRightLeft className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}

                  {/* Passkeys Cell */}
                  {hasColumn.passkeys && (
                    <td className="py-3 px-3 text-slate-300">
                      {item.passkeyCount > 0 ? (
                        <div className="flex flex-col gap-1">
                          <span
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 w-fit"
                            title={item.passkeyDetails?.map((p) => `RP ID: ${p.rpId || 'N/A'}, UserHandle: ${p.userHandle || 'N/A'}`).join('\n')}
                          >
                            <KeyRound className="w-3 h-3" />
                            {item.passkeyCount} Passkey{item.passkeyCount > 1 ? 's' : ''}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {item.passkeyDetails?.[0]?.rpId || domain}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px]">—</span>
                      )}
                    </td>
                  )}

                  {/* Notes Cell */}
                  {hasColumn.notes && (
                    <td className="py-3 px-3 text-slate-300 text-[11px] group/cell">
                      {isEditing ? (
                        <textarea
                          rows={2}
                          value={editValues.notes || ''}
                          onChange={(e) => setEditValues({ ...editValues, notes: e.target.value })}
                          className="w-full bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-1">
                          <span
                            className="truncate max-w-[130px]"
                            title={item.notes || 'No notes'}
                          >
                            {item.notes || '—'}
                          </span>
                          {item.notes && (
                            <button
                              onClick={() => copyToClipboard(item.notes!, `nt-${item.id}`)}
                              className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-700 text-slate-400 hover:text-slate-200 rounded transition"
                              title="Copy notes"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          )}
                          {isDiff('notes') && item.notes && (
                            <button
                              title="Push these notes to all duplicates"
                              onClick={() =>
                                onPushValue(domain, account.accountId, 'notes', item.id)
                              }
                              className="opacity-0 group-hover/cell:opacity-100 p-1 hover:bg-slate-700 text-slate-400 hover:text-amber-300 rounded transition"
                            >
                              <ArrowRightLeft className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}

                  {/* Folder Cell */}
                  {hasColumn.folder && (
                    <td
                      className="py-3 px-3 text-slate-400 text-[11px] truncate max-w-[100px]"
                      title={item.folderName || '(None)'}
                    >
                      {item.folderName || '(None)'}
                    </td>
                  )}

                  {/* URIs Cell */}
                  {hasColumn.uris && (
                    <td
                      className="py-3 px-3 text-slate-400 text-[11px] truncate max-w-[140px]"
                      title={item.uris.join(', ') || 'No URIs'}
                    >
                      {item.uris.join(', ') || '—'}
                    </td>
                  )}

                  {/* Actions Cell */}
                  <td className="py-3 px-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => saveEditing(item.id)}
                            className="p-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded transition"
                            title="Save edits"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="p-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition"
                            title="Cancel edits"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => onSeparateItem(item.id)}
                            className="p-1 text-slate-400 hover:text-amber-300 hover:bg-slate-700 rounded transition"
                            title="Separate as Unique Login (remove from this duplicate table)"
                          >
                            <Unlink className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => openMoveModal([item.id], item.name)}
                            className="p-1 text-slate-400 hover:text-indigo-300 hover:bg-slate-700 rounded transition"
                            title="Move to another website/domain..."
                          >
                            <Globe className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => startEditing(item)}
                            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded transition"
                            title="Edit row"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onDeleteItem(item.id)}
                            className="p-1 text-slate-400 hover:text-rose-400 hover:bg-slate-700 rounded transition"
                            title="Delete this row"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Action Footer */}
      <div className="px-5 py-3 bg-slate-900/60 border-t border-slate-700/60 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            Survivor keeps all passkeys, archives differing passwords to{' '}
            <code className="text-slate-300">passwordHistory</code>, appends URIs, and moves redundant rows to Trash.
          </span>
        </div>

        <button
          disabled={merging}
          onClick={handleMerge}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-200" />
          {merging ? 'Consolidating...' : 'Consolidate into Survivor'}
        </button>
      </div>

      {/* Move / Re-group Modal */}
      {moveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-800 border border-slate-700/80 rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100">
                    {moveModal.itemIds.length > 1
                      ? `Move ${moveModal.itemIds.length} Logins to Website`
                      : `Move "${moveModal.title}" to Website`}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Re-group under a specific website or domain.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setMoveModal(null)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">
                Target Website Domain (e.g. instagram.com)
              </label>
              <input
                type="text"
                autoFocus
                value={targetDomainInput}
                onChange={(e) => setTargetDomainInput(e.target.value)}
                placeholder="e.g. instagram.com, coursera.org, linkedin.com"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleConfirmMove();
                }}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
              />
              {suggestedDomains.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[10px] text-slate-400">Suggestions:</span>
                  {suggestedDomains.map((dom) => (
                    <button
                      key={dom}
                      type="button"
                      onClick={() => setTargetDomainInput(dom)}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 hover:bg-slate-600 text-indigo-300 transition"
                    >
                      {dom}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setMoveModal(null)}
                className="px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!targetDomainInput.trim() || isMoving}
                onClick={handleConfirmMove}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
              >
                <Check className="w-3.5 h-3.5" />
                {isMoving ? 'Moving...' : 'Move & Re-group'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
