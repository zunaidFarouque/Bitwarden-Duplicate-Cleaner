import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api/client';
import type {
  VaultStats,
  SidebarData,
  DomainGroup,
  ItemSummary,
} from './types';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import type { ActiveView } from './components/Sidebar';
import { DomainView, UniqueView, DeletedView, ModifiedView } from './components/Views';
import { ImportModal } from './components/ImportModal';
import { ExportModal } from './components/ExportModal';
import { PasskeyHelpModal } from './components/PasskeyHelpModal';
import { Sparkles, Upload } from 'lucide-react';

export const App: React.FC = () => {
  const [stats, setStats] = useState<VaultStats | undefined>();
  const [sidebar, setSidebar] = useState<SidebarData>({
    domains: [],
    uniqueCount: 0,
    modifiedCount: 0,
    deletedCount: 0,
    canUndo: false,
    canRedo: false,
  });

  const [activeView, setActiveView] = useState<ActiveView>({ type: 'unique' });
  const [currentDomainGroup, setCurrentDomainGroup] = useState<DomainGroup | null>(null);
  const [uniqueList, setUniqueList] = useState<ItemSummary[]>([]);
  const [modifiedList, setModifiedList] = useState<ItemSummary[]>([]);
  const [deletedList, setDeletedList] = useState<ItemSummary[]>([]);

  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Refresh all state
  const refreshAll = useCallback(async (viewOverride?: ActiveView) => {
    try {
      const statsRes = await api.getStats();
      if (!statsRes.initialized) {
        setIsImportOpen(true);
        return;
      }
      setStats(statsRes.stats);

      const side = await api.getSidebar();
      setSidebar(side);

      const targetView = viewOverride || activeView;

      if (targetView.type === 'domain') {
        const exists = side.domains.some((d) => d.domain === targetView.domain);
        if (exists) {
          const dg = await api.getDomainDuplicates(targetView.domain);
          setCurrentDomainGroup(dg);
        } else if (side.domains.length > 0) {
          const nextDom = side.domains[0].domain;
          setActiveView({ type: 'domain', domain: nextDom });
          const dg = await api.getDomainDuplicates(nextDom);
          setCurrentDomainGroup(dg);
        } else {
          setActiveView({ type: 'unique' });
          const u = await api.getUniqueItems();
          setUniqueList(u.items);
        }
      } else if (targetView.type === 'unique') {
        const u = await api.getUniqueItems();
        setUniqueList(u.items);
      } else if (targetView.type === 'modified') {
        const m = await api.getModifiedItems();
        setModifiedList(m.items);
      } else if (targetView.type === 'deleted') {
        const d = await api.getDeletedItems();
        setDeletedList(d.items);
      }
    } catch (err) {
      console.error('Error refreshing vault state:', err);
    }
  }, [activeView]);

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        const statsRes = await api.getStats();
        if (!statsRes.initialized) {
          setIsImportOpen(true);
        } else {
          setStats(statsRes.stats);
          const side = await api.getSidebar();
          setSidebar(side);
          if (side.domains.length > 0) {
            const firstDom = side.domains[0].domain;
            setActiveView({ type: 'domain', domain: firstDom });
            const dg = await api.getDomainDuplicates(firstDom);
            setCurrentDomainGroup(dg);
          } else {
            setActiveView({ type: 'unique' });
            const u = await api.getUniqueItems();
            setUniqueList(u.items);
          }
        }
      } catch (err) {
        setIsImportOpen(true);
      }
    };
    init();
  }, []);

  // View switch handler
  const handleSelectView = async (view: ActiveView) => {
    setActiveView(view);
    if (view.type === 'domain') {
      const dg = await api.getDomainDuplicates(view.domain);
      setCurrentDomainGroup(dg);
    } else if (view.type === 'unique') {
      const u = await api.getUniqueItems();
      setUniqueList(u.items);
    } else if (view.type === 'modified') {
      const m = await api.getModifiedItems();
      setModifiedList(m.items);
    } else if (view.type === 'deleted') {
      const d = await api.getDeletedItems();
      setDeletedList(d.items);
    }
  };

  // Actions
  const handleMerge = async (domain: string, accountId: string, survivorId: string) => {
    await api.mergeAccount(domain, accountId, survivorId);
    await refreshAll();
  };

  const handleEditCell = async (itemId: string, field: string, value: any) => {
    await api.editCell(itemId, field, value);
    await refreshAll();
  };

  const handlePushValue = async (
    domain: string,
    accountId: string,
    field: string,
    sourceItemId: string
  ) => {
    await api.pushValue(domain, accountId, field, sourceItemId);
    await refreshAll();
  };

  const handleDeleteItem = async (itemId: string) => {
    await api.deleteItem(itemId);
    await refreshAll();
  };

  const handleRestoreItem = async (itemId: string) => {
    await api.restoreItem(itemId);
    await refreshAll();
  };

  const handleUndo = async () => {
    await api.undo();
    await refreshAll();
  };

  const handleRedo = async () => {
    await api.redo();
    await refreshAll();
  };

  // Global Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        if (e.shiftKey) {
          if (sidebar.canRedo) handleRedo();
        } else {
          if (sidebar.canUndo) handleUndo();
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') {
        if (sidebar.canRedo) handleRedo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebar.canUndo, sidebar.canRedo]);

  const onImportSuccess = (newStats: VaultStats) => {
    setStats(newStats);
    refreshAll();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar
        stats={stats}
        canUndo={sidebar.canUndo}
        canRedo={sidebar.canRedo}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onOpenImport={() => setIsImportOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar
          domains={sidebar.domains}
          uniqueCount={sidebar.uniqueCount}
          modifiedCount={sidebar.modifiedCount}
          deletedCount={sidebar.deletedCount}
          activeView={activeView}
          onSelectView={handleSelectView}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {!stats ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl mb-4">
                <Sparkles className="w-10 h-10" />
              </div>
              <h2 className="text-xl font-bold text-slate-100 mb-2">No Vault Loaded</h2>
              <p className="text-xs text-slate-400 max-w-sm mb-6">
                Import your Bitwarden JSON export to start comparing, resolving differences, and safely consolidating duplicates.
              </p>
              <button
                onClick={() => setIsImportOpen(true)}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-indigo-600/25 flex items-center gap-2"
              >
                <Upload className="w-4 h-4" /> Import Bitwarden Vault
              </button>
            </div>
          ) : (
            <>
              {activeView.type === 'domain' && currentDomainGroup && (
                <DomainView
                  domainGroup={currentDomainGroup}
                  onMerge={handleMerge}
                  onEditCell={handleEditCell}
                  onPushValue={handlePushValue}
                  onDeleteItem={handleDeleteItem}
                />
              )}
              {activeView.type === 'unique' && <UniqueView items={uniqueList} />}
              {activeView.type === 'modified' && <ModifiedView items={modifiedList} />}
              {activeView.type === 'deleted' && (
                <DeletedView items={deletedList} onRestore={handleRestoreItem} />
              )}
            </>
          )}
        </main>
      </div>

      {/* Modals */}
      <ImportModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onImportSuccess={onImportSuccess}
        onOpenHelp={() => setIsHelpOpen(true)}
      />

      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        stats={stats}
      />

      <PasskeyHelpModal
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
      />
    </div>
  );
};

export default App;
