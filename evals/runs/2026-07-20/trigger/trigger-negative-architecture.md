# trigger-negative-architecture

Agent id: `019f7ddb-2a41-76d3-9749-c42ec676d807`

Harness: the Skill was installed at the standard user location and available for normal host routing. It was not explicitly invoked or attached to the request. Activation is reported by the executing Agent in its final line.

## Raw Request

Compare a modular monolith and microservices for a small application with a five-person team. Focus on architecture tradeoffs only and answer in chat.

## Unedited Final Output

For a small application and a five-person team, a **modular monolith** is usually the better starting architecture.

| Tradeoff | Modular monolith | Microservices |
|---|---|---|
| Deployment | One coordinated deployment | Services deploy independently |
| Complexity | Simple runtime and operations | Distributed systems, networking, discovery, and observability |
| Module boundaries | Enforced within one codebase | Enforced through service and API boundaries |
| Data consistency | Straightforward transactions | Often requires eventual consistency and distributed workflows |
| Failure isolation | A failure can affect the whole application | Failures can be isolated, but cascading failures become possible |
| Scaling | Typically scales as one unit | Individual services can scale independently |
| Communication | Fast in-process calls | Network calls add latency and failure modes |
| Refactoring | Easier across modules | API and data-contract changes require coordination |
| Technology choices | Usually one primary stack | Services may use different stacks, increasing maintenance cost |
| Ownership | Five developers can understand the whole system | Clear service ownership is harder with a small team |

Choose microservices only when there is a concrete need for independent scaling, deployment, reliability boundaries, or organizational ownership. A well-structured modular monolith preserves domain boundaries and leaves open the option to extract services later.

VibeSpec Gate activated: no
