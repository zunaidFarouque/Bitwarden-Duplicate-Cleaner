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
} from 'lucide-react';
import type { AccountGroup, ItemSummary } from '../types';

interface Props {
  domain: string;
  account: AccountGroup;
  onMerge: (domain: string, accountId: string, survivorId: string) => Promise<void>;
  onEditCell: (itemId: string, field: string, value: any) => Promise<void>;
  onPushValue: (domain: string, accountId: string, field: string, sourceItemId: string) => Promise<void>;
  onDeleteItem: (itemId: string) => Promise<void>;
}

export const AccountTable: React.FC<Props> = ({
  domain,
  account,
  onMerge,
  onEditCell,
  onPushValue,
  onDeleteItem,
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

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-200">
          <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-700/60 uppercase text-[10px] tracking-wider font-semibold">
            <tr>
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

              return (
                <tr
                  key={item.id}
                  className={`transition ${
                    isSurvivor
                      ? 'bg-indigo-600/10 hover:bg-indigo-600/15'
                      : 'hover:bg-slate-700/30'
                  }`}
                >
                  {/* Survivor Radio */}
                  <td className="py-3 px-3 text-center">
                    <input
                      type="radio"
                      name={`survivor-${account.accountId}`}
                      checked={isSurvivor}
                      onChange={() => setSurvivorId(item.id)}
                      className="w-4 h-4 text-indigo-600 bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                      title="Select as master survivor"
                    />
                  </td>

                  {/* Name Cell */}
                  {hasColumn.name && (
                    <td className="py-3 px-3 font-medium">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.name || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, name: e.target.value })
                          }
                          className="w-full px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white"
                        />
                      ) : (
                        <div className="flex items-center gap-1.5 group/cell">
                          <span className="truncate max-w-[140px]" title={item.name}>
                            {item.name}
                          </span>
                          {isDiff('name') && (
                            <button
                              title="Push this name to all duplicates"
                              onClick={() => onPushValue(domain, account.accountId, 'name', item.id)}
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
                    <td className="py-3 px-3">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.username || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, username: e.target.value })
                          }
                          className="w-full px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white font-mono"
                        />
                      ) : (
                        <div className="flex items-center gap-1.5 group/cell">
                          <span
                            className="font-mono text-slate-300 truncate max-w-[160px]"
                            title={item.username || '(None)'}
                          >
                            {item.username || '(None)'}
                          </span>
                          {isDiff('username') && (
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

                  {/* Password Cell */}
                  {hasColumn.password && (
                    <td className="py-3 px-3">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValues.password || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, password: e.target.value })
                          }
                          className="w-full px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white font-mono"
                        />
                      ) : (
                        <div className="flex items-center gap-1.5 group/cell">
                          <span
                            className="font-mono text-xs text-slate-200 truncate max-w-[150px] select-all"
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
                              <Copy className="w-3 h-3" />
                            </button>
                          )}
                          {isDiff('password') && (
                            <button
                              title="Push this password to all duplicates"
                              onClick={() =>
                                onPushValue(domain, account.accountId, 'password', item.id)
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

                  {/* TOTP Cell */}
                  {hasColumn.totp && (
                    <td className="py-3 px-3">
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

                  {/* Passkeys Cell */}
                  {hasColumn.passkeys && (
                    <td className="py-3 px-3">
                      {item.passkeyCount > 0 ? (
                        <div
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-semibold"
                          title={
                            item.passkeyDetails.length > 0
                              ? item.passkeyDetails
                                  .map((p) => `${p.rpId || 'Passkey'} (${p.userName || ''})`)
                                  .join(', ')
                              : `${item.passkeyCount} Passkey(s)`
                          }
                        >
                          <KeyRound className="w-3 h-3 text-amber-400" />
                          <span>{item.passkeyCount} Passkey</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px]" title="No passkeys">
                          —
                        </span>
                      )}
                    </td>
                  )}

                  {/* Notes Cell */}
                  {hasColumn.notes && (
                    <td className="py-3 px-3">
                      {isEditing ? (
                        <textarea
                          rows={2}
                          value={editValues.notes || ''}
                          onChange={(e) =>
                            setEditValues({ ...editValues, notes: e.target.value })
                          }
                          className="w-full px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white"
                        />
                      ) : (
                        <div className="flex items-center gap-1.5 group/cell">
                          {item.notes ? (
                            <span
                              className="truncate max-w-[120px] text-slate-400 text-[11px]"
                              title={item.notes}
                            >
                              {item.notes}
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[11px]" title="No notes">
                              —
                            </span>
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
    </div>
  );
};
