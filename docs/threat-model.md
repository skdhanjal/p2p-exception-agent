# Threat model: Procure-to-Pay Exception Agent
 
Version 1, 2026-10-12. Reviewed by: <you>
 
## 1. What we protect (assets)
A1  Money: a payment request for an invoice that should not be paid.
A2  Approval integrity: that a recorded approval is real, specific,
    unexpired, and used once.
A3  Vendor data: bank-account tails, payment terms.
A4  Credentials and identities: service accounts, CI identities.
A5  Availability and cost: ability to process invoices; model spend.
 
## 2. Who attacks (actors)
T1  External vendor or fraudster who controls document content.
T2  Insider approver acting outside policy (single bad approval).
T3  Compromised dependency or build (supply chain).
T4  Compromised workload: the workflow or one MCP server.
T5  Curious or careless internal user (over-sharing, mistakes).
 
## 3. Trust boundaries
B1  Internet -> agent (documents and chat messages)
B2  Agent -> model (prompts, documents, responses)
B3  Agent -> MCP servers and executor (Cloud Run, ID tokens)
B4  Human -> approvals service (verified identity)
B5  Executor -> payments server -> BigQuery (writes)
B6  Build -> deploy (CI, WIF)
 
## 4. Attack paths and controls (goal: unauthorized payment)
P1  Injected text makes the model alter fields
    Controls: layers 1-6 of Figure 1; validation; PO bound
    Residual: low
P2  Model leaks instructions or account data
    Controls: minimized summary input; output redaction
    Residual: low
P3  Forged or guessed approval id
    Controls: approvals table, lookup, bound to invoice and amount
    Residual: low
P4  Replay of a real approval
    Controls: single-use consumption table
    Residual: low
P5  Workflow calls the payments server directly
    Controls: no invoker grant; audited
    Residual: low
P6  Large amount through a policy approval
    Controls: server-side cap
    Residual: low
P7  Duplicate evasion by altering the invoice number
    Controls: number-only duplicate check
    Residual: MEDIUM, open
P8  A single insider approves a bad invoice
    Controls: recorded identity; audit trail
    Residual: MEDIUM, accepted
P9  Oversized or malformed uploads exhaust cost
    Controls: admission control; limits
    Residual: low
P10 Poisoned dependency
    Controls: lockfile; audit; scanning
    Residual: medium
P11 Leaked key
    Controls: no long-lived keys; WIF; key audit
    Residual: low
 
## 5. Not covered
Real payment rails, real approver identity management, network
isolation (needs an organization), scanned or handwritten documents.
