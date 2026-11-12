# 3. System Requirements

The design exists to meet six requirements, and nothing in it serves anything else.

| # | Requirement | How the design meets it |
| --- | --- | --- |
| R1 | The user controls the keys | The account key is made on the user's desktop. A reader or writer gets access only when the user approves it, and loses it when the user revokes it. |
| R2 | A collector node collects and pushes messages in real time, encrypted from the source | The node is the user's desktop app (5.4.1) or a hosted bridge unlocked by the user's key (5.4.2). The desktop encrypts each message under a content key derived from the account key, and computes its search tags, before it uploads. The bridge seals each message to the account's public key, so it cannot read the mirror back. The database never receives plaintext from either. Attachments are the exception (see Decisions made to simplify). |
| R3 | Data is secure at rest in the database | The database holds ciphertext, keyed tags and token hashes. Nothing in it opens without a token. |
| R4 | Approved readers and writers can search, retrieve and update in near real time | Each holds a token that opens its own copy of the account key for one request. A message is searchable as soon as it is stored. |
| R5 | Under 10 seconds from a user's question to the AI's first response | The mirror's share is budgeted at 1 second at the 95th percentile. The rest belongs to the AI. |
| R6 | Model outputs stay encrypted back to the user | Everything a model writes for the user is stored as a write under the content key, remembers its sources, and leaves the mirror in the clear only where the user chooses (5.5). |
