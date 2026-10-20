export interface PasskeyDetail {
  credentialId?: string;
  rpId?: string;
  userName?: string;
  userHandle?: string;
  creationDate?: string;
  keyType?: string;
}

export interface ItemSummary {
  id: string;
  name: string;
  type: number;
  folderId?: string;
  folderName?: string;
  username?: string;
  password?: string;
  totp?: string;
  notes?: string;
  uris: string[];
  passkeyCount: number;
  passkeyDetails: PasskeyDetail[];
  fieldsCount: number;
  revisionDate?: string;
  creationDate?: string;
  diffFlags: Record<string, boolean>;
}

export interface AccountGroup {
  accountId: string;
  normalizedUsername: string;
  displayUsername: string;
  itemCount: number;
  hasPasskeys: boolean;
  diffFields: string[];
  items: ItemSummary[];
}

export interface DomainGroup {
  domain: string;
  totalAccounts: number;
  totalItems: number;
  hasPasskeys: boolean;
  accounts: AccountGroup[];
}

export interface DomainSummary {
  domain: string;
  totalAccounts: number;
  totalItems: number;
  hasPasskeys: boolean;
}

export interface VaultStats {
  totalItems: number;
  duplicateCount: number;
  uniqueCount: number;
  modifiedCount: number;
  deletedCount: number;
  passkeyItemCount: number;
  passkeyTotalCount: number;
  hasWarning: boolean;
  warningMessage?: string;
  userClaimedPasskeys: boolean;
}

export interface SidebarData {
  domains: DomainSummary[];
  uniqueCount: number;
  modifiedCount: number;
  deletedCount: number;
  canUndo: boolean;
  canRedo: boolean;
}
