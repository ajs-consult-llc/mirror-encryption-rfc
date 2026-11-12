# Latency budget

Encryption costs the answer well under a second: the mirror's whole share is targeted at 0.4 seconds, inside a 1-second budget, so most of the 10 seconds belongs to the AI.

<!-- diagram: latency budget · targets at the 95th percentile, not measurements -->
```mermaid
---
title: "Encryption adds well under a second, and the answer lands inside the 10 s budget"
---
flowchart TB
  accTitle: Encryption adds well under a second, and the answer lands inside the 10-second budget
  accDescr: Question to first response is 7.4 seconds at the 95th percentile, of which the mirror is 0.405 seconds. These are targets, not measurements. The AI provider reads the question and calls the mirror in an assumed 3 seconds. The mirror then takes 0.405 seconds of its 1-second budget: 0.2 seconds for the request to the server and back over the network, 0.005 seconds on the server to find the token and unlock the key, 0.1 seconds in the database to look up the query's tags, and 0.1 seconds on the server to decrypt and check 200 candidates. The AI provider then writes the first words from the results in an assumed 4 seconds, so the first response arrives at 7.4 seconds, inside the 10-second budget.
  Q(["The user asks a question · 0 s"]) --> A["AI provider reads the question<br/>and calls the mirror<br/>3 s, assumed"]
  A --> M
  subgraph M["The mirror · 0.405 s of its 1 s budget"]
    direction TB
    M1["Request to the server and back<br/>network · 0.2 s"] --> M2["Find the token and unlock the key<br/>server · 0.005 s"] --> M3["Look up the query's tags<br/>database · 0.1 s"] --> M4["Decrypt and check 200 candidates<br/>server · 0.1 s"]
  end
  M --> W["AI provider writes the first<br/>words from the results<br/>4 s, assumed"]
  W --> F(["First response at 7.4 s,<br/>inside the 10 s budget"])
  F ~~~ N["Targets at the 95th percentile,<br/>not measurements."]:::note
  classDef mirror stroke:#2f5f86,fill:#e8eff6,color:#1f2933
  class M1,M2,M3,M4 mirror
  classDef note fill:none,stroke:none,color:#5f7183
```

These are targets, not measurements. Before launch they are measured on a synthetic account the size of the largest real one, about 1.6 million messages. A new message is searchable once its upload completes; the target is under 2 seconds from arriving on the desktop.
