"use strict";

/**
 * @fileoverview AgentVault Node.js SDK
 *
 * Zero-dependency Node.js client for AgentVault — the zero-trust secret manager
 * for AI agents. Uses only the built-in `https` and `http` modules.
 *
 * @example
 * const { AgentVaultClient } = require('./agentvault');
 *
 * const vault = new AgentVaultClient(
 *   process.env.AGENTVAULT_URL,
 *   process.env.AGENTVAULT_AGENT_ID,
 *   process.env.AGENTVAULT_AGENT_SECRET,
 * );
 *
 * await vault.issueToken('my-run-001');
 * const apiKey = await vault.fetchSecret('OPENAI_API_KEY');
 * await vault.revokeToken();
 */

const http  = require("http");
const https = require("https");

// Renew the token when fewer than this many seconds remain on the TTL.
const RENEW_THRESHOLD_SECONDS = 120;

// ─────────────────────────────────────────────────────────────────────────────
// Custom error types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Base error for all AgentVault SDK errors.
 */
class AgentVaultError extends Error {
  /**
   * @param {string} message
   * @param {number|null} [statusCode]
   */
  constructor(message, statusCode = null) {
    super(message);
    this.name = "AgentVaultError";
    /** @type {number|null} HTTP status code, if applicable. */
    this.statusCode = statusCode;
  }
}

/** Raised when agent credentials are rejected or the vault token is invalid. */
class AgentVaultAuthError extends AgentVaultError {
  constructor(message, statusCode) {
    super(message, statusCode);
    this.name = "AgentVaultAuthError";
  }
}

/** Raised when the agent is not authorized to access a requested secret. */
class AgentVaultAccessError extends AgentVaultError {
  constructor(message, statusCode) {
    super(message, statusCode);
    this.name = "AgentVaultAccessError";
  }
}

/** Raised when a requested secret does not exist. */
class AgentVaultNotFoundError extends AgentVaultError {
  constructor(message, statusCode) {
    super(message, statusCode);
    this.name = "AgentVaultNotFoundError";
  }
}

/** Raised when the vault token has expired and could not be auto-renewed. */
class AgentVaultTokenExpiredError extends AgentVaultError {
  constructor(message) {
    super(message, null);
    this.name = "AgentVaultTokenExpiredError";
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AgentVaultClient
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Client for the AgentVault secret manager (agent-facing vault API).
 *
 * Handles vault token lifecycle automatically:
 * - Issues a token on first use if none is held
 * - Renews the token when fewer than 2 minutes remain
 * - Revokes the token when {@link AgentVaultClient#revokeToken} is called
 *
 * @example
 * // Recommended: issue, use, revoke in a try/finally block
 * const vault = new AgentVaultClient(url, agentId, agentSecret);
 * await vault.issueToken('run-001');
 * try {
 *   const key = await vault.fetchSecret('OPENAI_API_KEY');
 *   // ... use key
 * } finally {
 *   await vault.revokeToken();
 * }
 */
class AgentVaultClient {
  /**
   * @param {string} vaultUrl     Base URL of the AgentVault API (e.g. "http://api.agentvault.nexuslayer.eu").
   *                              Trailing slashes are stripped automatically.
   * @param {string} agentId      The agent's UUID from POST /api/v1/agents.
   * @param {string} agentSecret  The av_ag_... credential from agent registration.
   * @param {object} [options]
   * @param {number} [options.timeoutMs=10000]  Request timeout in milliseconds.
   */
  constructor(vaultUrl, agentId, agentSecret, options = {}) {
    this._vaultUrl    = vaultUrl.replace(/\/+$/, "");
    this._agentId     = agentId;
    this._agentSecret = agentSecret;
    this._timeoutMs   = options.timeoutMs ?? 10_000;

    /** @type {string|null} */
    this._token = null;
    /** @type {Date|null} */
    this._tokenExpiresAt = null;
    /** @type {string|null} */
    this._runId = null;
  }

  // ── Token management ────────────────────────────────────────────────────

  /**
   * Exchange agent credentials for a short-lived vault token (15-minute TTL).
   *
   * Called automatically by {@link AgentVaultClient#fetchSecret} and
   * {@link AgentVaultClient#listSecrets} if no token is held. Call explicitly
   * when you want the `runId` to appear in the audit log from the first request.
   *
   * @param {string|null} [runId]  Optional logical run identifier for audit correlation.
   * @returns {Promise<{token: string, expiresAt: string, ttlSeconds: number}>}
   * @throws {AgentVaultAuthError} If agent credentials are rejected.
   * @throws {AgentVaultError}     On other API errors.
   *
   * @example
   * const tokenInfo = await vault.issueToken('pipeline-run-20250115-001');
   * console.log('Token expires at:', tokenInfo.expiresAt);
   */
  async issueToken(runId = null) {
    this._runId = runId;
    const payload = { agentId: this._agentId, agentSecret: this._agentSecret };
    if (runId != null) payload.runId = runId;

    const data = await this._post("/vault/token", payload, false);
    this._token          = data.token;
    this._tokenExpiresAt = new Date(data.expiresAt);
    return data;
  }

  /**
   * Extend the current vault token's TTL by 15 minutes.
   *
   * The old token is invalidated; the SDK updates its internal reference.
   *
   * @returns {Promise<{token: string, expiresAt: string, ttlSeconds: number}>}
   * @throws {AgentVaultError} If no token is currently held or the renewal fails.
   *
   * @example
   * await vault.renewToken();
   */
  async renewToken() {
    if (!this._token) {
      throw new AgentVaultError("No vault token to renew. Call issueToken() first.");
    }
    const data = await this._post("/vault/token/renew", {});
    this._token          = data.token;
    this._tokenExpiresAt = new Date(data.expiresAt);
    return data;
  }

  /**
   * Immediately invalidate the current vault token.
   *
   * Safe to call multiple times — if no token is held, this is a no-op.
   *
   * @returns {Promise<void>}
   * @throws {AgentVaultError} If the revocation call fails.
   *
   * @example
   * await vault.revokeToken();
   */
  async revokeToken() {
    if (!this._token) return;
    await this._post("/vault/token/revoke", {});
    this._token          = null;
    this._tokenExpiresAt = null;
  }

  // ── Secret access ────────────────────────────────────────────────────────

  /**
   * Fetch and decrypt a secret value by name.
   *
   * Automatically issues a vault token if none is held. Auto-renews when fewer
   * than 2 minutes remain on the TTL.
   *
   * @param {string}      name           The secret's logical name (e.g. `"OPENAI_API_KEY"`).
   *                                     Case-sensitive; must match the name used in the admin API.
   * @param {string|null} [runId]        Run ID to use when issuing a fresh token (ignored if
   *                                     a token is already held).
   * @returns {Promise<string>}          The plaintext secret value.
   * @throws {AgentVaultAuthError}       Bad credentials or expired/invalid token.
   * @throws {AgentVaultAccessError}     Agent has no policy for this secret.
   * @throws {AgentVaultNotFoundError}   Secret does not exist.
   * @throws {AgentVaultError}           Other API errors.
   *
   * @example
   * const openaiKey = await vault.fetchSecret('OPENAI_API_KEY', 'run-001');
   * const dbUrl     = await vault.fetchSecret('PROD_DB_URL');
   */
  async fetchSecret(name, runId = null) {
    await this._ensureToken(runId);
    const data = await this._get(`/vault/secrets/${encodeURIComponent(name)}`);
    return data.value;
  }

  /**
   * List all secrets this agent is authorized to access.
   *
   * Returns names and types only — values are never included in this response.
   *
   * @returns {Promise<Array<{name: string, type: string}>>}
   * @throws {AgentVaultError} On API errors or if no token can be issued.
   *
   * @example
   * const secrets = await vault.listSecrets();
   * secrets.forEach(s => console.log(s.name, s.type));
   */
  async listSecrets() {
    await this._ensureToken();
    return this._get("/vault/secrets");
  }

  // ── Internal helpers ─────────────────────────────────────────────────────

  /** @private */
  async _ensureToken(runId = null) {
    if (!this._token) {
      await this.issueToken(runId);
      return;
    }
    if (!this._tokenExpiresAt) return;

    const remainingMs = this._tokenExpiresAt.getTime() - Date.now();
    if (remainingMs <= 0) {
      throw new AgentVaultTokenExpiredError(
        "Vault token has expired. Call issueToken() to obtain a new one."
      );
    }
    if (remainingMs < RENEW_THRESHOLD_SECONDS * 1_000) {
      await this.renewToken();
    }
  }

  /** @private */
  _buildHeaders(includeToken = true) {
    const headers = { "Content-Type": "application/json" };
    if (includeToken && this._token) {
      headers["X-Vault-Token"] = this._token;
    }
    return headers;
  }

  /**
   * Make an HTTP/HTTPS request.
   * @private
   * @param {"GET"|"POST"} method
   * @param {string} path
   * @param {object|null} [body]
   * @param {boolean} [includeToken]
   * @returns {Promise<any>}
   */
  _request(method, path, body = null, includeToken = true) {
    return new Promise((resolve, reject) => {
      const url      = new URL(this._vaultUrl + path);
      const isHttps  = url.protocol === "https:";
      const transport = isHttps ? https : http;
      const bodyData = body != null ? JSON.stringify(body) : null;

      const options = {
        hostname: url.hostname,
        port:     url.port || (isHttps ? 443 : 80),
        path:     url.pathname + url.search,
        method,
        headers:  this._buildHeaders(includeToken),
        timeout:  this._timeoutMs,
      };

      if (bodyData) {
        options.headers["Content-Length"] = Buffer.byteLength(bodyData);
      }

      const req = transport.request(options, (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf8");
          let parsed = null;
          if (raw) {
            try { parsed = JSON.parse(raw); } catch { parsed = raw; }
          }

          const status = res.statusCode;
          if (status >= 200 && status < 300) {
            resolve(parsed);
            return;
          }

          const message =
            (parsed && typeof parsed === "object" && (parsed.message || parsed.error)) ||
            (typeof parsed === "string" && parsed) ||
            `HTTP ${status}`;

          if (status === 401) reject(new AgentVaultAuthError(message, status));
          else if (status === 403) reject(new AgentVaultAccessError(message, status));
          else if (status === 404) reject(new AgentVaultNotFoundError(message, status));
          else reject(new AgentVaultError(message, status));
        });
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new AgentVaultError(`Request timed out after ${this._timeoutMs}ms`));
      });

      req.on("error", (err) => {
        reject(new AgentVaultError(`Connection error: ${err.message}`));
      });

      if (bodyData) req.write(bodyData);
      req.end();
    });
  }

  /** @private */
  _get(path) {
    return this._request("GET", path, null);
  }

  /** @private */
  _post(path, body, includeToken = true) {
    return this._request("POST", path, body, includeToken);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AgentVaultAdminClient
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Admin client for the AgentVault management API.
 *
 * Authenticates with email/password (JWT) and provides methods for managing
 * secrets, agents, and policies. Intended for provisioning scripts, CI/CD
 * pipelines, and admin tooling — not for runtime agent use.
 *
 * @example
 * const admin = new AgentVaultAdminClient('http://api.agentvault.nexuslayer.eu', 'admin@corp.com', 'pass');
 * await admin.login();
 * const secret = await admin.createSecret('NEW_KEY', 'API_KEY', 'sk-abc...', 'My key');
 * const agent  = await admin.registerAgent('my-agent', 'Does useful things');
 * console.log('Save this secret:', agent.agentSecret);
 * await admin.grantAccess(agent.id, secret.id);
 */
class AgentVaultAdminClient {
  /**
   * @param {string} vaultUrl  Base URL of the AgentVault API.
   * @param {string} email     Admin email address.
   * @param {string} password  Admin password.
   * @param {object} [options]
   * @param {number} [options.timeoutMs=10000]  Request timeout in milliseconds.
   */
  constructor(vaultUrl, email, password, options = {}) {
    this._vaultUrl  = vaultUrl.replace(/\/+$/, "");
    this._email     = email;
    this._password  = password;
    this._timeoutMs = options.timeoutMs ?? 10_000;
    /** @type {string|null} */
    this._jwt = null;
  }

  /**
   * Authenticate and store the JWT for subsequent calls.
   * @returns {Promise<void>}
   */
  async login() {
    const data = await this._post("/api/v1/auth/login", { email: this._email, password: this._password }, false);
    this._jwt = data.accessToken;
  }

  /**
   * Create a new encrypted secret.
   *
   * @param {string} name        Logical name (e.g. `"OPENAI_API_KEY"`).
   * @param {string} type        `"API_KEY"` | `"USERNAME_PASSWORD"` | `"SSH_KEY"` |
   *                             `"CERTIFICATE"` | `"JSON"` | `"CONNECTION_STRING"`
   * @param {string} value       Plaintext secret value.
   * @param {string} [description]  Optional human-readable description.
   * @returns {Promise<object>}  Secret metadata (no value).
   */
  async createSecret(name, type, value, description = "") {
    return this._post("/api/v1/secrets", { name, type, value, description });
  }

  /**
   * List all secrets in the workspace (metadata only, no values).
   * @returns {Promise<Array<object>>}
   */
  async listSecrets() {
    return this._get("/api/v1/secrets");
  }

  /**
   * Rotate a secret to a new value.
   *
   * @param {string} secretId   The secret's UUID.
   * @param {string} newValue   The new plaintext value.
   * @returns {Promise<object>} Updated secret metadata.
   */
  async rotateSecret(secretId, newValue) {
    return this._post(`/api/v1/secrets/${secretId}/rotate`, { newValue });
  }

  /**
   * Register a new agent identity.
   *
   * @param {string} name         Human-readable agent name.
   * @param {string} [description]
   * @returns {Promise<object>}   Agent dict including the one-time `agentSecret`.
   *
   * @warning The `agentSecret` is returned only once. Store it immediately.
   */
  async registerAgent(name, description = "") {
    return this._post("/api/v1/agents", { name, description });
  }

  /**
   * List all registered agent identities.
   * @returns {Promise<Array<object>>}
   */
  async listAgents() {
    return this._get("/api/v1/agents");
  }

  /**
   * Grant an agent access to a secret (create a policy).
   *
   * @param {string} agentIdentityId  The agent's UUID.
   * @param {string} secretId         The secret's UUID.
   * @returns {Promise<object>}       The created policy.
   */
  async grantAccess(agentIdentityId, secretId) {
    return this._post("/api/v1/policies", { agentIdentityId, secretId });
  }

  /**
   * List all access policies.
   * @returns {Promise<Array<object>>}
   */
  async listPolicies() {
    return this._get("/api/v1/policies");
  }

  /**
   * Retrieve the paginated audit log.
   *
   * @param {number} [limit=50]   Records per page.
   * @param {number} [offset=0]   Pagination offset.
   * @returns {Promise<{total: number, entries: Array<object>}>}
   */
  async auditLog(limit = 50, offset = 0) {
    return this._get(`/api/v1/audit?limit=${limit}&offset=${offset}`);
  }

  // ── Internal helpers ─────────────────────────────────────────────────────

  /** @private */
  _buildHeaders(includeAuth = true) {
    const headers = { "Content-Type": "application/json" };
    if (includeAuth && this._jwt) {
      headers["Authorization"] = `Bearer ${this._jwt}`;
    }
    return headers;
  }

  /** @private */
  _request(method, path, body = null, includeAuth = true) {
    return new Promise((resolve, reject) => {
      const url       = new URL(this._vaultUrl + path);
      const isHttps   = url.protocol === "https:";
      const transport = isHttps ? https : http;
      const bodyData  = body != null ? JSON.stringify(body) : null;

      const options = {
        hostname: url.hostname,
        port:     url.port || (isHttps ? 443 : 80),
        path:     url.pathname + url.search,
        method,
        headers:  this._buildHeaders(includeAuth),
        timeout:  this._timeoutMs,
      };

      if (bodyData) {
        options.headers["Content-Length"] = Buffer.byteLength(bodyData);
      }

      const req = transport.request(options, (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf8");
          let parsed = null;
          if (raw) {
            try { parsed = JSON.parse(raw); } catch { parsed = raw; }
          }

          const status = res.statusCode;
          if (status >= 200 && status < 300) {
            resolve(parsed);
            return;
          }

          const message =
            (parsed && typeof parsed === "object" && (parsed.message || parsed.error)) ||
            (typeof parsed === "string" && parsed) ||
            `HTTP ${status}`;

          if (status === 401) reject(new AgentVaultAuthError(message, status));
          else if (status === 403) reject(new AgentVaultAccessError(message, status));
          else if (status === 404) reject(new AgentVaultNotFoundError(message, status));
          else reject(new AgentVaultError(message, status));
        });
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new AgentVaultError(`Request timed out after ${this._timeoutMs}ms`));
      });

      req.on("error", (err) => {
        reject(new AgentVaultError(`Connection error: ${err.message}`));
      });

      if (bodyData) req.write(bodyData);
      req.end();
    });
  }

  /** @private */
  _get(path) {
    return this._request("GET", path, null);
  }

  /** @private */
  _post(path, body, includeAuth = true) {
    return this._request("POST", path, body, includeAuth);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Exports
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  AgentVaultClient,
  AgentVaultAdminClient,
  AgentVaultError,
  AgentVaultAuthError,
  AgentVaultAccessError,
  AgentVaultNotFoundError,
  AgentVaultTokenExpiredError,
};

// ─────────────────────────────────────────────────────────────────────────────
// Demo (node agentvault.js)
// ─────────────────────────────────────────────────────────────────────────────

if (require.main === module) {
  const VAULT_URL    = process.env.AGENTVAULT_URL            || "http://api.agentvault.nexuslayer.eu";
  const AGENT_ID     = process.env.AGENTVAULT_AGENT_ID        || "your-agent-uuid";
  const AGENT_SECRET = process.env.AGENTVAULT_AGENT_SECRET    || "av_ag_...";
  const ADMIN_EMAIL  = process.env.AGENTVAULT_EMAIL           || "admin@corp.com";
  const ADMIN_PASS   = process.env.AGENTVAULT_PASSWORD        || "changeme";

  (async () => {
    // ── Demo 1: Fetch a secret ──────────────────────────────────────────
    console.log("=== Demo 1: Fetch a secret ===");
    const vault = new AgentVaultClient(VAULT_URL, AGENT_ID, AGENT_SECRET);
    await vault.issueToken("demo-run-001");
    try {
      const secrets = await vault.listSecrets();
      console.log("Authorized secrets:", secrets.map(s => s.name).join(", ") || "(none)");

      if (secrets.length > 0) {
        const value = await vault.fetchSecret(secrets[0].name);
        console.log(`Fetched ${secrets[0].name}: ${String(value).slice(0, 8)}...`);
      }
    } catch (err) {
      console.error("Error:", err.name, err.message);
    } finally {
      await vault.revokeToken();
      console.log("Token revoked");
    }

    // ── Demo 2: Admin API ───────────────────────────────────────────────
    console.log("\n=== Demo 2: Admin API ===");
    const admin = new AgentVaultAdminClient(VAULT_URL, ADMIN_EMAIL, ADMIN_PASS);
    try {
      await admin.login();
      console.log("Admin login successful");

      const secrets = await admin.listSecrets();
      console.log(`Workspace has ${secrets.length} secret(s)`);

      const agents = await admin.listAgents();
      console.log(`Workspace has ${agents.length} agent(s)`);

      const log = await admin.auditLog(5, 0);
      const entries = log.entries || [];
      console.log(`Last ${entries.length} audit entries:`);
      entries.forEach(e =>
        console.log(`  [${e.timestamp || ""}] ${e.agentName || ""} → ${e.secretName || ""}`)
      );
    } catch (err) {
      console.error("Admin error:", err.name, err.message);
    }
  })();
}
