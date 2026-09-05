"""
AgentVault Python SDK
=====================
A zero-dependency Python client for AgentVault — the zero-trust secret manager
for AI agents.

Usage:
    from agentvault_sdk import AgentVaultClient

    # As a context manager (recommended — auto-revokes token on exit)
    with AgentVaultClient(vault_url, agent_id, agent_secret) as vault:
        api_key = vault.fetch_secret("OPENAI_API_KEY", run_id="run-001")

    # Manual usage
    vault = AgentVaultClient(vault_url, agent_id, agent_secret)
    vault.issue_token(run_id="run-001")
    secrets = vault.list_authorized_secrets()
    api_key = vault.fetch_secret("OPENAI_API_KEY")
    vault.revoke_token()
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional


class AgentVaultError(Exception):
    """Base exception for all AgentVault SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AgentVaultAuthError(AgentVaultError):
    """Raised when agent credentials are rejected or the vault token is invalid."""


class AgentVaultAccessError(AgentVaultError):
    """Raised when the agent is not authorized to access a requested secret."""


class AgentVaultNotFoundError(AgentVaultError):
    """Raised when a requested secret does not exist."""


class AgentVaultTokenExpiredError(AgentVaultError):
    """Raised when the vault token has expired and could not be auto-renewed."""


# Renew the token when fewer than this many seconds remain on the TTL.
_RENEW_THRESHOLD_SECONDS = 120


class AgentVaultClient:
    """
    Client for the AgentVault secret manager.

    Handles vault token lifecycle (issue, auto-renew, revoke) and provides
    simple methods for fetching secrets at runtime.

    Args:
        vault_url:    Base URL of the AgentVault API (e.g. "https://vault.nexuslayer.eu").
                      Trailing slashes are stripped automatically.
        agent_id:     The agent's UUID as returned by POST /api/v1/agents.
        agent_secret: The ``av_ag_...`` secret shown once at agent registration.
        timeout:      HTTP request timeout in seconds (default: 10).

    Example::

        with AgentVaultClient(
            vault_url="https://vault.nexuslayer.eu",
            agent_id="550e8400-e29b-41d4-a716-446655440000",
            agent_secret="av_ag_k8x2mN9pQrTvWzYb...",
        ) as vault:
            api_key = vault.fetch_secret("OPENAI_API_KEY", run_id="my-run-001")
    """

    def __init__(
        self,
        vault_url: str,
        agent_id: str,
        agent_secret: str,
        timeout: int = 10,
    ) -> None:
        self._vault_url = vault_url.rstrip("/")
        self._agent_id = agent_id
        self._agent_secret = agent_secret
        self._timeout = timeout

        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._run_id: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Context manager support                                             #
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "AgentVaultClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Revoke the vault token on context exit, even if an exception occurred."""
        if self._token:
            try:
                self.revoke_token()
            except AgentVaultError:
                # Best-effort revocation — do not mask the original exception.
                pass

    # ------------------------------------------------------------------ #
    # Token management                                                    #
    # ------------------------------------------------------------------ #

    def issue_token(self, run_id: Optional[str] = None) -> dict:
        """
        Exchange agent credentials for a short-lived vault token (15-minute TTL).

        This is called automatically by :meth:`fetch_secret` if no token is
        currently held. Call this explicitly when you want the ``runId`` to
        appear in the audit log from the very first request.

        Args:
            run_id: Optional logical run identifier. Appears in the audit log,
                    making it easy to correlate all secret accesses within a
                    single pipeline run or task execution.

        Returns:
            dict with keys ``token``, ``expiresAt``, ``ttlSeconds``.

        Raises:
            AgentVaultAuthError: If the agent credentials are rejected.
            AgentVaultError:     On unexpected API errors.

        Example::

            token_info = vault.issue_token(run_id="pipeline-run-20250115-001")
            print(f"Token expires at: {token_info['expiresAt']}")
        """
        self._run_id = run_id
        payload = {
            "agentId": self._agent_id,
            "agentSecret": self._agent_secret,
        }
        if run_id is not None:
            payload["runId"] = run_id

        data = self._post("/vault/token", payload)
        self._token = data["token"]
        self._token_expires_at = datetime.fromisoformat(
            data["expiresAt"].replace("Z", "+00:00")
        )
        return data

    def renew_token(self) -> dict:
        """
        Extend the current vault token's TTL by 15 minutes.

        Returns a new token value; the old token is invalidated. The SDK
        updates its internal token reference automatically.

        Returns:
            dict with keys ``token``, ``expiresAt``, ``ttlSeconds``.

        Raises:
            AgentVaultError: If no token is currently held or the renewal fails.

        Example::

            # Renew before a long-running operation
            vault.renew_token()
        """
        if not self._token:
            raise AgentVaultError("No vault token to renew. Call issue_token() first.")

        data = self._post("/vault/token/renew", {})
        self._token = data["token"]
        self._token_expires_at = datetime.fromisoformat(
            data["expiresAt"].replace("Z", "+00:00")
        )
        return data

    def revoke_token(self) -> None:
        """
        Immediately invalidate the current vault token.

        Called automatically on context manager exit. Safe to call multiple
        times — if no token is held, this is a no-op.

        Raises:
            AgentVaultError: If the revocation API call fails.

        Example::

            vault.revoke_token()
        """
        if not self._token:
            return
        self._post("/vault/token/revoke", {})
        self._token = None
        self._token_expires_at = None

    # ------------------------------------------------------------------ #
    # Secret access                                                       #
    # ------------------------------------------------------------------ #

    def fetch_secret(self, name: str, run_id: Optional[str] = None) -> str:
        """
        Fetch and decrypt a secret value by name.

        Automatically issues a vault token if none is held. Renews the token
        if fewer than 2 minutes remain on the TTL (configurable via the
        ``_RENEW_THRESHOLD_SECONDS`` module constant).

        Args:
            name:   The secret's logical name (e.g. ``"OPENAI_API_KEY"``).
                    Case-sensitive; must match the name used when the secret
                    was created via the admin API.
            run_id: Optional run identifier to use when issuing a fresh token.
                    Ignored if a token is already held.

        Returns:
            The plaintext secret value as a string.

        Raises:
            AgentVaultAuthError:    If credentials are invalid.
            AgentVaultAccessError:  If the agent has no policy granting access
                                    to this secret.
            AgentVaultNotFoundError: If no secret with ``name`` exists.
            AgentVaultError:        On other API errors.

        Example::

            openai_key    = vault.fetch_secret("OPENAI_API_KEY", run_id="run-001")
            anthropic_key = vault.fetch_secret("ANTHROPIC_API_KEY")
            db_url        = vault.fetch_secret("PROD_DB_URL")
        """
        self._ensure_token(run_id=run_id)
        data = self._get(f"/vault/secrets/{name}")
        return data["value"]

    def list_authorized_secrets(self) -> list[dict]:
        """
        List all secrets this agent is authorized to access.

        Returns names and types only — values are not included.

        Returns:
            List of dicts, each with at minimum ``name`` and ``type`` keys.

        Raises:
            AgentVaultError: On API errors or if no token is held.

        Example::

            for secret in vault.list_authorized_secrets():
                print(f"{secret['name']} ({secret['type']})")
        """
        self._ensure_token()
        return self._get("/vault/secrets")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _ensure_token(self, run_id: Optional[str] = None) -> None:
        """Issue or renew the vault token as needed."""
        if self._token is None:
            self.issue_token(run_id=run_id)
            return

        if self._token_expires_at is None:
            return

        now = datetime.now(tz=timezone.utc)
        remaining = (self._token_expires_at - now).total_seconds()

        if remaining <= 0:
            raise AgentVaultTokenExpiredError(
                "Vault token has expired. Call issue_token() to obtain a new one."
            )

        if remaining < _RENEW_THRESHOLD_SECONDS:
            self.renew_token()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["X-Vault-Token"] = self._token
        return headers

    def _request(self, method: str, path: str, payload: Optional[dict]) -> Any:
        url = self._vault_url + path
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                body_obj = json.loads(raw)
                message = body_obj.get("message") or body_obj.get("error") or str(body_obj)
            except Exception:
                message = raw.decode(errors="replace") or exc.reason
            status = exc.code
            if status == 401:
                raise AgentVaultAuthError(message, status_code=status) from exc
            if status == 403:
                raise AgentVaultAccessError(message, status_code=status) from exc
            if status == 404:
                raise AgentVaultNotFoundError(message, status_code=status) from exc
            raise AgentVaultError(message, status_code=status) from exc
        except urllib.error.URLError as exc:
            raise AgentVaultError(f"Connection error to {url}: {exc.reason}") from exc

    def _get(self, path: str) -> Any:
        return self._request("GET", path, None)

    def _post(self, path: str, payload: dict) -> Any:
        return self._request("POST", path, payload)


# ------------------------------------------------------------------ #
# Admin client (for orchestrators / CI pipelines)                     #
# ------------------------------------------------------------------ #

class AgentVaultAdminClient:
    """
    Admin client for the AgentVault management API.

    Authenticates with email/password and provides methods for managing
    secrets, agents, and policies. Intended for use in CI/CD pipelines,
    provisioning scripts, and admin tooling — not for runtime agent use
    (use :class:`AgentVaultClient` for that).

    Args:
        vault_url: Base URL of the AgentVault API.
        email:     Admin email address.
        password:  Admin password.
        timeout:   HTTP request timeout in seconds (default: 10).

    Example::

        admin = AgentVaultAdminClient("https://vault.nexuslayer.eu", "admin@corp.com", "pass")
        admin.login()
        admin.create_secret("NEW_SECRET", "API_KEY", "sk-abc123", "My new key")
    """

    def __init__(
        self,
        vault_url: str,
        email: str,
        password: str,
        timeout: int = 10,
    ) -> None:
        self._vault_url = vault_url.rstrip("/")
        self._email = email
        self._password = password
        self._timeout = timeout
        self._jwt: Optional[str] = None

    def login(self) -> None:
        """Authenticate and store the JWT for subsequent calls."""
        data = self._post("/api/v1/auth/login", {"email": self._email, "password": self._password})
        self._jwt = data["accessToken"]

    def create_secret(
        self,
        name: str,
        secret_type: str,
        value: str,
        description: str = "",
    ) -> dict:
        """
        Create a new encrypted secret.

        Args:
            name:        Logical name (e.g. ``"OPENAI_API_KEY"``).
            secret_type: One of ``API_KEY``, ``USERNAME_PASSWORD``, ``SSH_KEY``,
                         ``CERTIFICATE``, ``JSON``, ``CONNECTION_STRING``.
            value:       Plaintext secret value.
            description: Optional human-readable description.

        Returns:
            Secret metadata dict (no value included).
        """
        return self._post("/api/v1/secrets", {
            "name": name,
            "type": secret_type,
            "value": value,
            "description": description,
        })

    def list_secrets(self) -> list[dict]:
        """Return all secrets in the workspace (metadata only, no values)."""
        return self._get("/api/v1/secrets")

    def rotate_secret(self, secret_id: str, new_value: str) -> dict:
        """
        Rotate a secret to a new value.

        Args:
            secret_id: The secret's UUID.
            new_value: The new plaintext value.

        Returns:
            Updated secret metadata dict.
        """
        return self._post(f"/api/v1/secrets/{secret_id}/rotate", {"newValue": new_value})

    def register_agent(self, name: str, description: str = "") -> dict:
        """
        Register a new agent identity.

        Args:
            name:        Human-readable agent name.
            description: Optional description.

        Returns:
            Agent dict including the one-time ``agentSecret``.

        Warning:
            The ``agentSecret`` is returned only once. Store it immediately.
        """
        return self._post("/api/v1/agents", {"name": name, "description": description})

    def list_agents(self) -> list[dict]:
        """Return all registered agent identities."""
        return self._get("/api/v1/agents")

    def grant_access(self, agent_identity_id: str, secret_id: str) -> dict:
        """
        Grant an agent access to a secret.

        Args:
            agent_identity_id: The agent's UUID.
            secret_id:         The secret's UUID.

        Returns:
            The created policy dict.
        """
        return self._post("/api/v1/policies", {
            "agentIdentityId": agent_identity_id,
            "secretId": secret_id,
        })

    def list_policies(self) -> list[dict]:
        """Return all access policies."""
        return self._get("/api/v1/policies")

    def audit_log(self, limit: int = 50, offset: int = 0) -> dict:
        """
        Retrieve the paginated audit log.

        Args:
            limit:  Records per page (default: 50).
            offset: Pagination offset (default: 0).

        Returns:
            dict with ``total``, ``offset``, ``limit``, and ``entries`` keys.
        """
        return self._get(f"/api/v1/audit?limit={limit}&offset={offset}")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._jwt:
            headers["Authorization"] = f"Bearer {self._jwt}"
        return headers

    def _request(self, method: str, path: str, payload: Optional[dict]) -> Any:
        url = self._vault_url + path
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                message = json.loads(raw).get("message", exc.reason)
            except Exception:
                message = raw.decode(errors="replace") or exc.reason
            raise AgentVaultError(message, status_code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise AgentVaultError(f"Connection error: {exc.reason}") from exc

    def _get(self, path: str) -> Any:
        return self._request("GET", path, None)

    def _post(self, path: str, payload: dict) -> Any:
        return self._request("POST", path, payload)


# ------------------------------------------------------------------ #
# Usage examples                                                       #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import os

    VAULT_URL    = os.environ.get("AGENTVAULT_URL",    "https://vault.nexuslayer.eu")
    AGENT_ID     = os.environ.get("AGENTVAULT_AGENT_ID",    "your-agent-uuid")
    AGENT_SECRET = os.environ.get("AGENTVAULT_AGENT_SECRET", "av_ag_...")

    # ── Example 1: Simple secret fetch ────────────────────────────────
    print("=== Example 1: Fetch a secret ===")
    with AgentVaultClient(VAULT_URL, AGENT_ID, AGENT_SECRET) as vault:
        try:
            api_key = vault.fetch_secret("OPENAI_API_KEY", run_id="demo-run-001")
            print(f"Fetched OPENAI_API_KEY: {api_key[:8]}...")
        except AgentVaultNotFoundError:
            print("Secret OPENAI_API_KEY not found")
        except AgentVaultAccessError:
            print("Agent not authorized to access OPENAI_API_KEY")

    # ── Example 2: List authorized secrets ────────────────────────────
    print("\n=== Example 2: List authorized secrets ===")
    with AgentVaultClient(VAULT_URL, AGENT_ID, AGENT_SECRET) as vault:
        secrets = vault.list_authorized_secrets()
        for s in secrets:
            print(f"  {s['name']} ({s['type']})")

    # ── Example 3: Manual token management ────────────────────────────
    print("\n=== Example 3: Manual token management ===")
    vault = AgentVaultClient(VAULT_URL, AGENT_ID, AGENT_SECRET)
    try:
        token_info = vault.issue_token(run_id="manual-run-001")
        print(f"Token issued, expires at: {token_info['expiresAt']}")

        db_url = vault.fetch_secret("PROD_DB_URL")
        print(f"DB URL: {db_url[:20]}...")

        # Renew before a long operation
        renewed = vault.renew_token()
        print(f"Token renewed, new expiry: {renewed['expiresAt']}")
    finally:
        vault.revoke_token()
        print("Token revoked")

    # ── Example 4: Admin API — provision secrets and policies ─────────
    print("\n=== Example 4: Admin API — provisioning ===")
    ADMIN_EMAIL    = os.environ.get("AGENTVAULT_EMAIL",    "admin@corp.com")
    ADMIN_PASSWORD = os.environ.get("AGENTVAULT_PASSWORD", "changeme")

    admin = AgentVaultAdminClient(VAULT_URL, ADMIN_EMAIL, ADMIN_PASSWORD)
    try:
        admin.login()
        print("Admin login successful")

        # Create a secret
        secret = admin.create_secret(
            "DEMO_API_KEY",
            "API_KEY",
            "sk-demo-12345",
            "Demo API key for SDK example",
        )
        print(f"Created secret: {secret['id']} ({secret['name']})")

        # Register a new agent
        agent = admin.register_agent("sdk-demo-agent", "Created by SDK demo")
        print(f"Registered agent: {agent['id']}")
        print(f"Agent secret (save this!): {agent.get('agentSecret', 'N/A')}")

        # Grant access
        policy = admin.grant_access(agent["id"], secret["id"])
        print(f"Policy created: {policy.get('id', 'created')}")

        # Tail the audit log
        log = admin.audit_log(limit=5)
        print(f"\nLast {min(5, len(log.get('entries', [])))} audit entries:")
        for entry in log.get("entries", []):
            print(f"  [{entry.get('timestamp', '')}] {entry.get('agentName', '')} → {entry.get('secretName', '')}")

    except AgentVaultError as exc:
        print(f"Admin API error: {exc}")
