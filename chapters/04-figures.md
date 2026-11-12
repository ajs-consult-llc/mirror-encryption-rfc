# Figures

| Figure | Caption | Section |
| --- | --- | --- |
| 5.1 | The whole design: one account key, one kind of token, a database and a blob store | 5 |
| 6.1 | Where the account key lives in the clear, and where only locked copies exist | 6.1 |
| 6.2 | Create: the desktop makes the account key and uploads only a locked copy | 6.1.1 |
| 6.3 | Read: a token opens its copy of the account key for one request | 6.1.2 |
| 6.4 | Update: a new reader or writer gets its own token and its own locked copy | 6.1.3 |
| 6.5 | Expire: an expired token is refused and its copy is deleted | 6.1.4 |
| 6.6 | Delete: access ends when a token's hash and its copy are deleted | 6.1.5 |
| 6.7 | Collect and push: messages are encrypted on the desktop before upload | 6.2.1 |
| 6.8 | Approve a reader or writer: one approval, one token, one locked copy | 6.2.2 |
| 6.9 | Search and retrieve: the account key is opened for one request only | 6.2.3 |
| 6.10 | Update: a writer's change is encrypted on the server inside its request | 6.2.4 |
| 6.11 | Revoke and recover: one deletion cuts a holder off, and recovery needs another approved device | 6.2.5 |
| 7.1 | Latency budget: targets at the 95th percentile, not measurements | 7 |
| A.1 | One shared database compared with one database per user | Appendix A |
