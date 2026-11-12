# Appendix A. Single or multi-tenant

For stored data the choice barely matters, because each user's rows are locked under that user's own key. It matters for the server's memory, for cost, and for who can see metadata.

|  | One shared database | One database per user |
| --- | --- | --- |
| Stored data | Isolated by each user's key: another user's rows, served by mistake, do not decrypt | The same, plus physical separation |
| A compromised server | Sees what every active user's requests decrypt while it is compromised | Sees one user's |
| Metadata: counts, sizes, times | Visible to the operator. Per-user tag keys stop matching across users. | Visible to whoever runs it |
| Deleting a user | Delete their copies of the account key and their rows | Delete the database |
| Cost and operations | One database to run | One per user |

<!-- diagram: shared vs dedicated · 3 users -->
```mermaid
---
title: "Keys isolate stored data either way, and separate instances contain a breach"
---
flowchart TB
  accTitle: Keys isolate stored data either way, and separate instances contain a breach
  accDescr: Each user's key stays on their desktop in both designs, and colours mark whose key locks which rows. With one shared database, users A, B and C, holding keys A, B and C, all use one shared server, which opens key A, B or C inside each user's request, and one shared database with row-level security, where user A's rows are locked under key A, user B's under key B and user C's under key C. A server breach sees every active user's requests. There is one system to run, and metadata is visible to the operator. With one instance per user, user A uses server A, which holds key A only, and database A, which holds user A's rows under key A, and the same for users B and C. A server breach sees one user's requests. There is one system per user to run and pay for.
  subgraph shared["One shared database"]
    direction TB
    SA["User A<br/>holds key A"]:::a
    SB["User B<br/>holds key B"]:::b
    SC["User C<br/>holds key C"]:::c
    SA & SB & SC --> SS["One shared server<br/>opens key A, B or C<br/>inside each user's request"]
    SS --> SD[("One shared database,<br/>with row-level security<br/>A's rows under key A<br/>B's rows under key B<br/>C's rows under key C")]
  end
  subgraph dedicated["One instance per user"]
    direction TB
    UA["User A<br/>holds key A"]:::a --> VA["Server A<br/>key A only"] --> BA[("Database A<br/>A's rows<br/>under key A")]:::a
    UB["User B<br/>holds key B"]:::b --> VB["Server B<br/>key B only"] --> BB[("Database B<br/>B's rows<br/>under key B")]:::b
    UC["User C<br/>holds key C"]:::c --> VC["Server C<br/>key C only"] --> BC[("Database C<br/>C's rows<br/>under key C")]:::c
  end
  shared ~~~ dedicated
  classDef a stroke:#2f6fd0,fill:#e3edfb,color:#1f2933
  classDef b stroke:#e0663a,fill:#fbe9e2,color:#1f2933
  classDef c stroke:#2a9d6f,fill:#e0f3ea,color:#1f2933
```

The recommendation is one codebase that runs either way. Shared by default, with row-level security in the database as a second line behind the keys. A dedicated instance, run by the operator or by the user, for anyone who wants the smaller blast radius. The keys stay with the user in both.
