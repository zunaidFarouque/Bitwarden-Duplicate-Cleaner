from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class URI(BaseModel):
    model_config = ConfigDict(extra="allow")
    match: Optional[int] = None
    uri: Optional[str] = None


class Fido2Credential(BaseModel):
    model_config = ConfigDict(extra="allow")
    credentialId: Optional[str] = None
    keyType: Optional[str] = None
    algorithm: Optional[str] = None
    curve: Optional[str] = None
    rpId: Optional[str] = None
    userHandle: Optional[str] = None
    userName: Optional[str] = None
    counter: Optional[int] = None
    rpName: Optional[str] = None
    creationDate: Optional[str] = None


class PasswordHistoryItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    lastUsedDate: Optional[str] = None
    password: Optional[str] = None


class CustomField(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    value: Optional[str] = None
    type: Optional[int] = 0
    linkedId: Optional[Any] = None


class LoginInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    uris: Optional[List[URI]] = None
    username: Optional[str] = None
    password: Optional[str] = None
    totp: Optional[str] = None
    passwordHistory: Optional[List[PasswordHistoryItem]] = None
    fido2Credentials: Optional[List[Fido2Credential]] = None
    autofillOnPageLoad: Optional[bool] = None


class BitwardenFolder(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    name: Optional[str] = None


class BitwardenItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    organizationId: Optional[str] = None
    folderId: Optional[str] = None
    type: int = 1  # 1 = Login, 2 = Secure Note, 3 = Card, 4 = Identity
    reprompt: Optional[int] = 0
    name: str = ""
    notes: Optional[str] = None
    favorite: Optional[bool] = False
    login: Optional[LoginInfo] = None
    fields: Optional[List[CustomField]] = None
    collectionIds: Optional[List[str]] = None
    revisionDate: Optional[str] = None
    creationDate: Optional[str] = None
    deletedDate: Optional[str] = None


class BitwardenVault(BaseModel):
    model_config = ConfigDict(extra="allow")
    encrypted: bool = False
    folders: List[BitwardenFolder] = Field(default_factory=list)
    items: List[BitwardenItem] = Field(default_factory=list)


# --- DTOs for UI ---

class ItemSummary(BaseModel):
    id: str
    name: str
    type: int
    folderId: Optional[str] = None
    folderName: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    totp: Optional[str] = None
    notes: Optional[str] = None
    uris: List[str] = Field(default_factory=list)
    passkeyCount: int = 0
    passkeyDetails: List[Dict[str, Any]] = Field(default_factory=list)
    fieldsCount: int = 0
    revisionDate: Optional[str] = None
    creationDate: Optional[str] = None
    diffFlags: Dict[str, bool] = Field(default_factory=dict)


class AccountGroup(BaseModel):
    accountId: str
    normalizedUsername: str
    displayUsername: str
    itemCount: int
    hasPasskeys: bool
    diffFields: List[str]
    items: List[ItemSummary]


class DomainGroup(BaseModel):
    domain: str
    totalAccounts: int
    totalItems: int
    hasPasskeys: bool
    accounts: List[AccountGroup]


class DomainSummary(BaseModel):
    domain: str
    totalAccounts: int
    totalItems: int
    hasPasskeys: bool


class VaultStats(BaseModel):
    totalItems: int
    duplicateCount: int
    uniqueCount: int
    modifiedCount: int
    deletedCount: int
    passkeyItemCount: int
    passkeyTotalCount: int
    hasWarning: bool = False
    warningMessage: Optional[str] = None
    userClaimedPasskeys: bool = False


class MergeRequest(BaseModel):
    domain: str
    accountId: str
    survivorId: str


class EditCellRequest(BaseModel):
    itemId: str
    field: str  # name, username, password, totp, notes
    value: Any


class PushValueRequest(BaseModel):
    domain: str
    accountId: str
    field: str
    sourceItemId: str
