import React, { useState } from 'react';
import {
  Search,
  Globe,
  Layers,
  CheckCircle,
  Trash2,
  Edit3,
  KeyRound,
} from 'lucide-react';
import type { DomainSummary } from '../types';

export type ActiveView =
  | { type: 'domain'; domain: string }
  | { type: 'unique' }
  | { type: 'modified' }
  | { type: 'deleted' };

interface Props {
  domains: DomainSummary[];
  uniqueCount: number;
  modifiedCount: number;
  deletedCount: number;
  activeView: ActiveView;
  onSelectView: (view: ActiveView) => void;
}

export const Sidebar: React.FC<Props> = ({
  domains,
  uniqueCount,
  modifiedCount,
  deletedCount,
  activeView,
  onSelectView,
}) => {
  const [search, setSearch] = useState('');

  const filteredDomains = domains.filter((d) =>
    d.domain.toLowerCase().includes(search.toLowerCase())
  );

  const totalDuplicates = domains.reduce((sum, d) => sum + d.totalItems, 0);

  return (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/50 flex flex-col h-[calc(100vh-4rem)] select-none">
      {/* Category Folders / High-Level Views */}
      <div className="p-3 border-b border-slate-800 space-y-1">
        <button
          onClick={() => {
            if (domains.length > 0) {
              onSelectView({ type: 'domain', domain: domains[0].domain });
            }
          }}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
            activeView.type === 'domain'
              ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-300 hover:bg-slate-800/60'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Duplicate Groups</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-500/20 text-amber-300 font-bold">
            {totalDuplicates}
          </span>
        </button>

        <button
          onClick={() => onSelectView({ type: 'unique' })}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
            activeView.type === 'unique'
              ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-300 hover:bg-slate-800/60'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>Unique Logins</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-medium">
            {uniqueCount}
          </span>
        </button>

        <button
          onClick={() => onSelectView({ type: 'modified' })}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
            activeView.type === 'modified'
              ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-300 hover:bg-slate-800/60'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Edit3 className="w-4 h-4 text-sky-400" />
            <span>Modified & Merged</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-sky-500/20 text-sky-300 font-medium">
            {modifiedCount}
          </span>
        </button>

        <button
          onClick={() => onSelectView({ type: 'deleted' })}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
            activeView.type === 'deleted'
              ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
              : 'text-slate-300 hover:bg-slate-800/60'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <Trash2 className="w-4 h-4 text-rose-400" />
            <span>Deleted (Trash)</span>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-500/20 text-rose-300 font-medium">
            {deletedCount}
          </span>
        </button>
      </div>

      {/* Domain Search */}
      <div className="p-3 border-b border-slate-800/80">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Filter duplicate websites..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Domain List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredDomains.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">
            {domains.length === 0 ? 'No duplicate websites found! 🎉' : 'No matching websites'}
          </div>
        ) : (
          filteredDomains.map((d) => {
            const isSelected = activeView.type === 'domain' && activeView.domain === d.domain;
            return (
              <button
                key={d.domain}
                onClick={() => onSelectView({ type: 'domain', domain: d.domain })}
                className={`w-full text-left p-2.5 rounded-xl transition flex items-center justify-between group ${
                  isSelected
                    ? 'bg-indigo-600 text-white font-medium shadow-md shadow-indigo-600/20'
                    : 'text-slate-300 hover:bg-slate-800/70'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Globe
                    className={`w-4 h-4 shrink-0 ${
                      isSelected ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  <div className="truncate">
                    <span className="text-xs truncate block">{d.domain}</span>
                    <span
                      className={`text-[10px] block ${
                        isSelected ? 'text-indigo-200' : 'text-slate-400'
                      }`}
                    >
                      {d.totalAccounts} {d.totalAccounts === 1 ? 'account' : 'accounts'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  {d.hasPasskeys && (
                    <span title="Contains passkeys">
                      <KeyRound
                        className={`w-3 h-3 ${isSelected ? 'text-amber-300' : 'text-amber-400'}`}
                      />
                    </span>
                  )}
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      isSelected
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-800 text-slate-300 group-hover:bg-slate-700'
                    }`}
                  >
                    {d.totalItems}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
};
