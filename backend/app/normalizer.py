import re
from urllib.parse import urlparse
from typing import Optional, List

# Common second-level domains for basic eTLD+1 parsing without external web lookup
COMMON_DOUBLE_TLDS = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "me.uk", "net.uk",
    "co.nz", "org.nz", "net.nz", "govt.nz",
    "com.au", "net.au", "org.au", "edu.au", "gov.au",
    "co.jp", "ne.jp", "or.jp", "go.jp", "ac.jp",
    "co.in", "net.in", "org.in", "gen.in", "firm.in",
    "com.br", "org.br", "net.br",
    "co.za", "org.za", "net.za",
    "com.sg", "edu.sg", "gov.sg",
    "com.tw", "org.tw", "club.tw",
    "com.tr", "edu.tr", "gov.tr",
    "com.mx", "org.mx", "edu.mx",
}

def extract_domain_from_uri(uri_str: Optional[str]) -> Optional[str]:
    """
    Extracts the root domain (eTLD+1) from a URI string.
    e.g. 'https://accounts.google.com/signin' -> 'google.com'
         'androidapp://com.google.android.youtube' -> 'youtube (app)' or 'google.com'
         'https://sub.amazon.co.uk' -> 'amazon.co.uk'
    """
    if not uri_str:
        return None
    
    uri_str = uri_str.strip()
    if not uri_str:
        return None

    # Handle android/iOS app URIs
    if uri_str.startswith("androidapp://"):
        pkg = uri_str.replace("androidapp://", "").split("/")[0]
        # Common packages
        if "google" in pkg:
            return "google.com"
        parts = pkg.split(".")
        if len(parts) >= 2:
            return f"{parts[-1]}.com"
        return pkg

    # Ensure URI has scheme for urlparse
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", uri_str):
        uri_str = "http://" + uri_str

    try:
        parsed = urlparse(uri_str)
        host = parsed.hostname
        if not host:
            return None
        
        host = host.lower().strip()
        # Remove trailing dots
        host = host.rstrip(".")

        # If IP address or localhost, return as is
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host) or host == "localhost":
            return host

        parts = host.split(".")
        if len(parts) <= 1:
            return host

        # Check for 2-level TLDs (e.g. example.co.uk)
        if len(parts) >= 3:
            last_two = f"{parts[-2]}.{parts[-1]}"
            if last_two in COMMON_DOUBLE_TLDS:
                return f"{parts[-3]}.{last_two}"

        # Standard eTLD+1 (e.g. accounts.google.com -> google.com)
        return f"{parts[-2]}.{parts[-1]}"
    except Exception:
        return None


def get_item_primary_domain(item_uris: Optional[List[str]], item_name: str) -> str:
    """
    Determines the primary domain group for a Bitwarden item.
    """
    if item_uris:
        for u in item_uris:
            dom = extract_domain_from_uri(u)
            if dom:
                return dom
    
    # Fallback to name heuristic or uncategorized
    clean_name = item_name.strip()
    # If name looks like a domain (e.g. "github.com")
    if "." in clean_name and " " not in clean_name:
        dom = extract_domain_from_uri(clean_name)
        if dom:
            return dom

    if clean_name:
        return f"{clean_name} (No Website)"
    return "Uncategorized Logins"


def normalize_username(username: Optional[str], domain: str) -> str:
    """
    Normalizes username taking into account service-specific rules.
    For Google:
      - 'user' -> 'user@gmail.com'
      - 'User.Name+alias@gmail.com' -> 'username@gmail.com'
      - 'user@googlemail.com' -> 'user@gmail.com'
    For all:
      - Strips whitespace
      - Lowercase
    """
    if not username:
        return ""
    
    u = username.strip().lower()
    if not u:
        return ""

    is_google = "google.com" in domain.lower()

    if is_google:
        # Check if already has @gmail.com or @googlemail.com
        if "@" in u:
            handle, host = u.split("@", 1)
            if host in ("gmail.com", "googlemail.com"):
                # Strip +alias
                handle = handle.split("+", 1)[0]
                # Strip dots in handle for gmail
                handle = handle.replace(".", "")
                return f"{handle}@gmail.com"
            else:
                # Custom domain google workspace
                handle = handle.split("+", 1)[0]
                return f"{handle}@{host}"
        else:
            # Bare username on Google (e.g. 'abc123')
            handle = u.split("+", 1)[0].replace(".", "")
            return f"{handle}@gmail.com"

    # General email normalization
    if "@" in u:
        parts = u.split("@", 1)
        handle = parts[0]
        host = parts[1]
        # We preserve + tag for general services since some treat it distinctly,
        # but normalize whitespace & casing
        return f"{handle.strip()}@{host.strip()}"

    return u
