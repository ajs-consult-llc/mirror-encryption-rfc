# Latency budget

Encryption costs the answer well under a second: the mirror's whole share is targeted at 0.4 seconds, inside a 1-second budget, so most of the 10 seconds belongs to the AI.

<!-- diagram: latency budget · targets at the 95th percentile, not measurements -->
```mermaid
gantt
  accTitle: Encryption adds well under a second, and the answer lands inside the 10-second budget
  accDescr: Question to first response is 7.4 seconds at the 95th percentile, of which the mirror is 0.405 seconds. These are targets, not measurements. The AI provider reads the question and calls the mirror in an assumed 3 seconds. The mirror then takes 0.405 seconds of its 1-second budget: 0.2 seconds for the request to the server and back over the network, 0.005 seconds on the server to find the token and unlock the key, 0.1 seconds in the database to look up the query's tags, and 0.1 seconds on the server to decrypt and check 200 candidates. The AI provider then writes the first words from the results in an assumed 4 seconds, so the first response arrives at 7.4 seconds, inside the 10-second budget.
  title Question to first response, 7.4 s of a 10 s budget (targets, not measurements)
  dateFormat x
  axisFormat %S.%L s
  section AI provider, assumed
  Read the question and call the mirror (3 s)        : 0, 3000
  Write the first words from the results (4 s)       : 3405, 7405
  section Mirror, 0.405 s of a 1 s budget
  Request to the server and back (network, 0.2 s)    : 3000, 3200
  Find the token and unlock the key (server, 0.005 s) : 3200, 3205
  Look up the query's tags (database, 0.1 s)         : 3205, 3305
  Decrypt and check 200 candidates (server, 0.1 s)   : 3305, 3405
```

These are targets, not measurements. Before launch they are measured on a synthetic account the size of the largest real one, about 1.6 million messages. A new message is searchable once its upload completes; the target is under 2 seconds from arriving on the desktop.
