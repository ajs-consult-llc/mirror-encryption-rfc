# Figures

| Figure | Caption | Section |
| --- | --- | --- |
| 4.1 | The whole design: one account key, one kind of token, a database and a blob store | 4 |
| 5.1 | The chain of joins: who can read at each join point, and what sets each hop's guarantee | 5 |
| 5.2 | Where the account key lives in the clear, and where only locked copies exist | 5.1 |
| 5.3 | Two ways to collect: the desktop node and the hosted bridge write into one mirror | 5.1 |
| 5.4 | Create: the desktop makes the account key and uploads only a locked copy | 5.1.1.1 |
| 5.5 | Read: a token opens its copy of the account key for one request | 5.1.1.2 |
| 5.6 | Update: a new reader or writer gets its own token and its own locked copy | 5.1.1.3 |
| 5.7 | Expire: an expired token is refused and its copy is deleted | 5.1.1.4 |
| 5.8 | Delete: access ends when a token's hash and its copy are deleted | 5.1.1.5 |
| 5.9 | Unlocking the hosted bridge: the user's device checks the image, then seals the bridge key under a lease | 5.1.2.2 |
| 5.10 | Collect and push: messages are encrypted on the collector node before upload | 5.2.1 |
| 5.11 | Writing through the hosted bridge: each message is sealed to the account's public key | 5.2.1 |
| 5.12 | Approve a reader or writer: one approval, one token, one locked copy | 5.2.2 |
| 5.13 | Search and retrieve: the account key is opened for one request only | 5.2.3 |
| 5.14 | Update: a writer's change is encrypted on the server inside its request | 5.2.4 |
| 5.15 | Revoke and recover: one deletion cuts a holder off, and recovery needs another approved device | 5.2.5 |
| 5.16 | Model outputs: stored as encrypted writes, delivered as a pointer unless the user chooses full text | 5.3 |
| 6.1 | Latency budget: targets at the 95th percentile, not measurements | 6 |
| A.1 | One shared database compared with one database per user | Appendix A |
