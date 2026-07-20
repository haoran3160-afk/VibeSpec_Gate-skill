# behavior-empty-project

Agent id: `019f7f60-f953-7a91-8643-49bcc9bd9b78`

## Raw Request

Use $vibespec-gate to review the provided empty project for launch readiness. Keep the review read-only and return the result in chat only.

## Unedited Final Output

Coverage: insufficient

- `auth`: missing - no authentication code or configuration was discovered.
- `authorization`: missing - no access-control implementation or policy was discovered.
- `secrets`: missing - no source, environment, build, or deployment evidence was available.
- `data_rules`: missing - no database, storage, validation, or retention configuration was available.
- `deployment`: missing - no production configuration, headers, CORS, rate limits, or exposed-service evidence was available.
- `agent_tools`: missing - no evidence establishes whether Agent, MCP, tool, file, command, email, payment, or database capabilities exist.
- `desktop_ipc`: missing - no evidence establishes whether Electron, IPC, preload bridges, local files, processes, or desktop APIs are in scope.

Inventory: 0 files discovered, 0 inspected, and 0 skipped.

Decision: REVIEW

## Highest-Impact Risks

none identified. The empty project provides no evidence from which a launch blocker or effective security control can be confirmed.

## Missing Evidence

The launch candidate's runtime source, manifests, dependency lockfiles, authentication and authorization controls, secret-handling configuration, data policies, deployment configuration, and any Agent/tool or desktop/IPC boundaries are required.

## Limitations

The review covered only the supplied empty-project evidence. It cannot establish the product type, deployment stage, public exposure, sensitive data, identity model, runtime behavior, or launch security. This was not a penetration test or compliance assessment.

## Human Confirmation Required

Confirm the actual launch-candidate scope, deployment stage, public exposure, sensitive-data categories, identity model, and whether Agents, MCP, desktop APIs, local files, shell commands, email, payments, or databases are used.

## Human-Gated Repair Tasks

No repair can be defined from the available evidence. Provide the actual launch candidate for a separate read-only review. Allowed scope is evidence inventory and inspection; project mutation, policy selection, permission expansion, and production changes remain prohibited without separate authorization.

## Project-Specific Retests

1. Confirm the reviewed launch candidate contains the runtime and deployment files used to build the release.
2. Re-run the gate and obtain complete coverage across all seven review surfaces.
3. Test applicable controls for unauthenticated, cross-user, cross-tenant, and non-admin denial.
4. Verify secrets are absent from client bundles and logs, data access defaults to deny, privileged tools require bounded authority and confirmation, and malformed IPC requests are rejected.
