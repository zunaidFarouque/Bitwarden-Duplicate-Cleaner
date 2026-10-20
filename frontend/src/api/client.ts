import type {
  VaultStats,
  SidebarData,
  DomainGroup,
  ItemSummary,
} from '../types';

const BASE_URL = '/api';

export const api = {
  async uploadVault(file: File, hasPasskeys: boolean): Promise<{ success: boolean; stats: VaultStats; backupPath: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('hasPasskeys', String(hasPasskeys));

    const res = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to upload vault');
    }
    return res.json();
  },

  async getStats(): Promise<{ initialized: boolean; stats?: VaultStats; canUndo: boolean; canRedo: boolean }> {
    const res = await fetch(`${BASE_URL}/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },

  async getSidebar(): Promise<SidebarData> {
    const res = await fetch(`${BASE_URL}/sidebar`);
    if (!res.ok) throw new Error('Failed to fetch sidebar');
    return res.json();
  },

  async getDomainDuplicates(domain: string): Promise<DomainGroup> {
    const res = await fetch(`${BASE_URL}/duplicates/${encodeURIComponent(domain)}`);
    if (!res.ok) throw new Error('Failed to fetch duplicates');
    return res.json();
  },

  async getUniqueItems(): Promise<{ items: ItemSummary[] }> {
    const res = await fetch(`${BASE_URL}/unique`);
    if (!res.ok) throw new Error('Failed to fetch unique items');
    return res.json();
  },

  async getModifiedItems(): Promise<{ items: ItemSummary[] }> {
    const res = await fetch(`${BASE_URL}/modified`);
    if (!res.ok) throw new Error('Failed to fetch modified items');
    return res.json();
  },

  async getDeletedItems(): Promise<{ items: ItemSummary[] }> {
    const res = await fetch(`${BASE_URL}/deleted`);
    if (!res.ok) throw new Error('Failed to fetch deleted items');
    return res.json();
  },

  async mergeAccount(domain: string, accountId: string, survivorId: string): Promise<{ success: boolean; stats: VaultStats }> {
    const res = await fetch(`${BASE_URL}/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, accountId, survivorId }),
    });
    if (!res.ok) throw new Error('Failed to merge account');
    return res.json();
  },

  async editCell(itemId: string, field: string, value: any): Promise<{ success: boolean }> {
    const res = await fetch(`${BASE_URL}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ itemId, field, value }),
    });
    if (!res.ok) throw new Error('Failed to edit cell');
    return res.json();
  },

  async pushValue(domain: string, accountId: string, field: string, sourceItemId: string): Promise<{ success: boolean }> {
    const res = await fetch(`${BASE_URL}/push`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, accountId, field, sourceItemId }),
    });
    if (!res.ok) throw new Error('Failed to push value');
    return res.json();
  },

  async deleteItem(itemId: string): Promise<{ success: boolean; stats: VaultStats }> {
    const res = await fetch(`${BASE_URL}/delete/${encodeURIComponent(itemId)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to delete item');
    return res.json();
  },

  async restoreItem(itemId: string): Promise<{ success: boolean; stats: VaultStats }> {
    const res = await fetch(`${BASE_URL}/restore/${encodeURIComponent(itemId)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to restore item');
    return res.json();
  },

  async undo(): Promise<{ success: boolean; stats: VaultStats }> {
    const res = await fetch(`${BASE_URL}/undo`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to undo');
    return res.json();
  },

  async redo(): Promise<{ success: boolean; stats: VaultStats }> {
    const res = await fetch(`${BASE_URL}/redo`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to redo');
    return res.json();
  },

  getExportUrl(): string {
    return `${BASE_URL}/export`;
  },
};
