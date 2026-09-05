'use strict';

/**
 * WatchGrid Node.js SDK
 * =====================
 * Production-quality SDK for ingesting agent observability events into WatchGrid.
 *
 * Features:
 * - Sync-style API (all async under the hood via native https)
 * - Auto-batching: flush every 1 second or after 50 events
 * - `track(fn)` wrapper for automatic run lifecycle management
 * - Full JSDoc for IDE autocompletion
 *
 * No external dependencies — uses Node.js built-in `https` and `http` modules.
 *
 * @example
 * const WatchGridClient = require('./watchgrid');
 * const wg = new WatchGridClient('http://api.watchgrid.nexuslayer.eu', 'wg_sdk_...');
 *
 * const result = await wg.track('my-run', async () => {
 *   await wg.logLlmCall('my-run', 'gpt-4o', 400, 100, 0.003, 1200);
 *   return 'done';
 * });
 *
 * await wg.flush();
 */

const http = require('http');
const https = require('https');
const { randomUUID } = require('crypto');

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Returns current UTC timestamp in ISO 8601 format.
 * @returns {string}
 */
function utcNow() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

/**
 * HTTP POST using Node.js built-in http/https.
 *
 * @param {string} url        - Full URL including path
 * @param {Record<string,string>} headers - Request headers
 * @param {object} body       - JSON-serialisable payload
 * @param {number} timeoutMs  - Request timeout in milliseconds
 * @returns {Promise<number>} HTTP status code, or 0 on network error
 */
function httpPost(url, headers, body, timeoutMs = 10_000) {
  return new Promise((resolve) => {
    const parsed = new URL(url);
    const transport = parsed.protocol === 'https:' ? https : http;
    const data = JSON.stringify(body);

    const options = {
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname + (parsed.search || ''),
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
      },
      timeout: timeoutMs,
    };

    const req = transport.request(options, (res) => {
      res.resume(); // consume body to free socket
      resolve(res.statusCode || 0);
    });

    req.on('timeout', () => {
      req.destroy();
      resolve(0);
    });

    req.on('error', () => resolve(0));
    req.write(data);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// WatchGridClient
// ---------------------------------------------------------------------------

class WatchGridClient {
  /**
   * Create a new WatchGrid client.
   *
   * @param {string} baseUrl        - WatchGrid API base URL, e.g. "http://api.watchgrid.nexuslayer.eu"
   * @param {string} sdkKey         - Agent SDK key starting with "wg_sdk_"
   * @param {object} [options]
   * @param {number} [options.batchSize=50]        - Flush after this many buffered events
   * @param {number} [options.flushIntervalMs=1000] - Auto-flush interval in milliseconds
   * @param {number} [options.timeoutMs=10000]      - HTTP request timeout in milliseconds
   */
  constructor(baseUrl, sdkKey, options = {}) {
    this._baseUrl = baseUrl.replace(/\/$/, '');
    this._sdkKey = sdkKey;
    this._batchSize = options.batchSize ?? 50;
    this._flushIntervalMs = options.flushIntervalMs ?? 1_000;
    this._timeoutMs = options.timeoutMs ?? 10_000;

    /** @type {object[]} */
    this._buffer = [];

    /** @type {boolean} */
    this._flushing = false;

    this._headers = {
      'X-SDK-Key': sdkKey,
    };

    this._timer = setInterval(() => this.flush(), this._flushIntervalMs);
    // Allow process to exit naturally even if timer is still alive
    if (this._timer.unref) this._timer.unref();
  }

  // ------------------------------------------------------------------
  // Core event methods
  // ------------------------------------------------------------------

  /**
   * Enqueue a RUN_START event.
   *
   * @param {string} [runId] - Run identifier. Defaults to a new UUID v4.
   * @returns {string} The run ID used.
   */
  async startRun(runId) {
    runId = runId || randomUUID();
    this._enqueue({ type: 'RUN_START', runId, timestamp: utcNow() });
    return runId;
  }

  /**
   * Enqueue a RUN_END event.
   *
   * @param {string} runId
   * @param {'SUCCESS'|'FAILURE'|'TIMEOUT'} [status='SUCCESS']
   * @param {string|null} [error=null] - If provided, also logs an ERROR event and sets status to FAILURE
   * @returns {Promise<void>}
   */
  async endRun(runId, status = 'SUCCESS', error = null) {
    if (error) {
      await this.logError(runId, error);
      status = 'FAILURE';
    }
    this._enqueue({ type: 'RUN_END', runId, status, timestamp: utcNow() });
  }

  /**
   * Enqueue an LLM_CALL event.
   *
   * @param {string} runId
   * @param {string} model          - Model name, e.g. "gpt-4o" or "openai/gpt-4o"
   * @param {number} inputTokens    - Prompt token count
   * @param {number} outputTokens   - Completion token count
   * @param {number} costUsd        - Cost of this call in USD
   * @param {number} latencyMs      - End-to-end latency in milliseconds
   * @returns {Promise<void>}
   */
  async logLlmCall(runId, model, inputTokens, outputTokens, costUsd, latencyMs) {
    this._enqueue({
      type: 'LLM_CALL',
      runId,
      model,
      inputTokens,
      outputTokens,
      costUsd: Math.round(costUsd * 1e8) / 1e8,
      latencyMs,
      timestamp: utcNow(),
    });
  }

  /**
   * Enqueue a TOOL_CALL event.
   *
   * @param {string} runId
   * @param {string} toolName   - Name of the tool/function called
   * @param {number} durationMs - Execution time in milliseconds
   * @returns {Promise<void>}
   */
  async logToolCall(runId, toolName, durationMs) {
    this._enqueue({ type: 'TOOL_CALL', runId, toolName, durationMs, timestamp: utcNow() });
  }

  /**
   * Enqueue an ERROR event.
   *
   * @param {string} runId
   * @param {string} message - Error message or exception text
   * @returns {Promise<void>}
   */
  async logError(runId, message) {
    this._enqueue({ type: 'ERROR', runId, message, timestamp: utcNow() });
  }

  // ------------------------------------------------------------------
  // track() wrapper
  // ------------------------------------------------------------------

  /**
   * Wrap an async function with automatic WatchGrid run lifecycle tracking.
   * A RUN_START is emitted before `fn`, RUN_END (SUCCESS or FAILURE) after.
   *
   * @template T
   * @param {string|null} runId - Run ID; pass null to auto-generate
   * @param {() => Promise<T>} fn - Async function to wrap
   * @returns {Promise<T>} The return value of `fn`
   *
   * @example
   * const output = await wg.track(null, async () => {
   *   await wg.logLlmCall(currentRunId, 'gpt-4o', 400, 100, 0.003, 1200);
   *   return callMyAgent(input);
   * });
   */
  async track(runId, fn) {
    runId = await this.startRun(runId || undefined);
    try {
      const result = await fn(runId);
      await this.endRun(runId, 'SUCCESS');
      return result;
    } catch (err) {
      await this.endRun(runId, 'FAILURE', err instanceof Error ? err.message : String(err));
      throw err;
    } finally {
      await this.flush();
    }
  }

  // ------------------------------------------------------------------
  // Buffer management
  // ------------------------------------------------------------------

  /**
   * @param {object} event
   * @private
   */
  _enqueue(event) {
    this._buffer.push(event);
    if (this._buffer.length >= this._batchSize) {
      // Fire-and-forget; flush handles concurrency internally
      this.flush().catch(() => {});
    }
  }

  /**
   * Flush all buffered events to WatchGrid immediately.
   *
   * @returns {Promise<void>}
   */
  async flush() {
    if (this._flushing || this._buffer.length === 0) return;
    this._flushing = true;
    const batch = this._buffer.splice(0);
    try {
      const status = await httpPost(
        `${this._baseUrl}/ingest/events`,
        this._headers,
        { events: batch },
        this._timeoutMs,
      );
      if (status !== 200 && status !== 202) {
        // Re-insert on failure (best-effort, prepend so order is preserved)
        this._buffer.unshift(...batch);
      }
    } catch {
      this._buffer.unshift(...batch);
    } finally {
      this._flushing = false;
    }
  }

  /**
   * Stop the auto-flush timer. Call when shutting down.
   *
   * @returns {Promise<void>}
   */
  async shutdown() {
    clearInterval(this._timer);
    await this.flush();
  }
}

module.exports = WatchGridClient;

// ---------------------------------------------------------------------------
// Usage example (run with: node watchgrid.js)
// ---------------------------------------------------------------------------

if (require.main === module) {
  const WATCHGRID_URL = 'http://api.watchgrid.nexuslayer.eu';
  const SDK_KEY = 'wg_sdk_replace_with_your_key';

  const wg = new WatchGridClient(WATCHGRID_URL, SDK_KEY);

  async function main() {
    // ---- Example 1: track() wrapper ----
    console.log('Example 1: track() wrapper');
    await wg.track(null, async (runId) => {
      console.log(`  Run ID: ${runId}`);
      await wg.logLlmCall(runId, 'gpt-4o', 412, 95, 0.0031, 1130);
      await wg.logToolCall(runId, 'web_search', 320);
      await wg.logLlmCall(runId, 'gpt-4o', 580, 210, 0.0072, 1840);
    });
    console.log('  Done.\n');

    // ---- Example 2: Manual tracking ----
    console.log('Example 2: Manual tracking');
    const runId = await wg.startRun();
    console.log(`  Run ID: ${runId}`);
    try {
      await wg.logLlmCall(runId, 'claude-3-5-sonnet', 300, 80, 0.0025, 950);
      await wg.logToolCall(runId, 'database_query', 45);
      await wg.endRun(runId, 'SUCCESS');
    } catch (err) {
      await wg.endRun(runId, 'FAILURE', err.message);
    }
    await wg.flush();
    console.log('  Done.\n');

    // ---- Example 3: Error handling ----
    console.log('Example 3: Error handling');
    await wg.track(null, async (runId) => {
      await wg.logLlmCall(runId, 'gpt-4o-mini', 200, 0, 0.0, 450);
      // Simulate a tool call that fails
      await wg.logError(runId, 'Tool timeout: web_scraper exceeded 30s limit');
      throw new Error('Tool timeout');
    }).catch(() => {});
    console.log('  Done.\n');

    await wg.shutdown();
    console.log('Check your WatchGrid dashboard at http://watchgrid.nexuslayer.eu');
  }

  main().catch(console.error);
}
