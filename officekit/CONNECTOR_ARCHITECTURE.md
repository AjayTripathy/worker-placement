# Connectors across local and hosted offices

Decision: 2026-09-18. One office UI and one ingestion/reconciliation contract.
Where a connector executes is separate from where the user opens the office.

## Current behavior

Adapters declare `runtimes` in the registry. The default is `("local",)`;
Alpaca and IBKR Flex explicitly support `("local", "hosted")`. Discovery and both
fetch entry points enforce this metadata before invoking a connector factory.
Adding a UI button must never grant a new execution capability.

The shared onboarding, Settings and Imports pages offer **Install the local app**
for TWS / IB Gateway, the Client Portal gateway, desktop file scans and other
local integrations. The guide distinguishes starting a new office from exporting
an existing hosted office and opening that same identity locally. The user signs
in and explicitly enables sync. Broker credentials and sessions stay local; the
existing validated office records and retained documents are what sync transfers.
No cloud-to-local tunnel or public broker socket is needed.

The website retains the last imported snapshot and its source dates while the
local app or broker is offline. Do not infer that a desktop source is connected
because it has historical imported rows. Cloud refresh controls must not attempt
to call a desktop connector. IBKR Flex and statement upload remain alternatives
for users who want to stay online.

## Future hosted authorization

OAuth is an authorization method, not a guarantee of read-only permissions or a
reason to change the office UI. A hosted connector must declare and enforce:

- Its approved execution runtime and authorization method.
- The requested scopes and actual broker-granted permissions; restrict ingestion
  to an explicit endpoint allowlist for accounts, balances, positions and lots.
- Tenant-scoped encrypted token storage, refresh, expiry, revocation and reconnect.
- Last successful import, source as-of, errors and freshness, using the current
  staging ledger and reconciliation gates.

No order or money-movement routes belong in this connector. Provider approval,
available scopes, and the endpoint permissions for the required data must be
verified before offering **Connect with IBKR**. Application-level read-only code
must not be described as a provider-enforced read-only grant unless verified.

IBKR's [OAuth 2.0 introduction](https://www.interactivebrokers.com/docs/web-api/authentication/oauth-2/introduction)
currently describes registration-gated access for eligible organizations, advisors
and brokers. Its [session documentation](https://www.interactivebrokers.com/docs/web-api/authentication/sessions)
also distinguishes a read-only outer session from brokerage sessions. Do not
assume Google-style self-service OAuth or universal read-only tokens.

## Switching an existing feed

A future local-to-OAuth change replaces the transport for an explicitly linked
source; it must not silently add a second copy of the same account. Preserve the
office identity, source history and `(feed, asset)` keys. Map broker account/source
identity with user review, keep the previous history, and stop the prior refresh
path before enabling the replacement. Independent feeds with the same label must
not be merged based on labels alone. Use the existing reconciliation model for
snapshots and overlapping data; do not introduce a second holdings store.
