# 7. What it does not protect

This is encryption controlled by the user's keys, not end-to-end encryption: the server decrypts inside each approved request. By the definition in [Knodel et al. (2025)](https://arxiv.org/abs/2412.20231), a cloud machine is never an endpoint however it is keyed, so neither a hosted bridge (5.4.2) nor an attested worker (5.5) makes it end-to-end encryption (question 8). The limits follow.

| Limit | Consequence |
| --- | --- |
| The server holds the account key and the results while it answers | A compromised server can capture the account key from any approved request. That one key opens the whole mirror, past and future, until the key is rotated. Proving which code the server runs (attestation) would close this; it is not in this design. |
| AI providers see what they retrieve and what they write | Their handling of prompts and outputs, including retention, is outside this design |
| Search tags reveal which messages share a fragment | The tags are deterministic and overlap, so a thief of the database may recover text from fragment frequencies alone, and more with some known plaintext (question 1). Sizes and times are visible too. |
| A stolen token works until it is revoked | Expiry limits the damage (question 4) |
| Malware on the desktop sees everything | The desktop holds the account key |
| Backups keep deleted copies until they expire | A revoked token can still open its copy in a backup taken earlier, for up to 30 days |
| Revoking one holder is access control, not erasure | Other copies of the same key remain, and a holder that paired its token with a copy of the database keeps the key. Only deleting every copy, or rotating the key, erases. |
| Every token opens the whole account key | What a holder may do (read only, one source, approve others) is enforced by the server's rules, not by cryptography |
| Tokens, queries and results are plaintext in the server's memory | They must be kept out of logs, traces and error reports. Whatever ends TLS in front of the server sees tokens too. Mitigation: the implementation's source code is published, and automated tests plant marker values in tokens, queries and results and fail if a marker reaches a log, a trace, an error report or stored data. Publishing the source shows what the code does; proving that the running server is that code is what attestation would add (question 7). |
| The mirror is only as fresh as the desktop | While the desktop is off or asleep, nothing new is collected |
| Search needs a fixed fragment of three or more characters | A query without one cannot use the index. It must be refused, or answered by decrypting every row. |
| Attachments are encrypted by the storage service, not on the desktop | The storage service sees each file in the clear while it handles an upload or a read. At rest, a file opens only with the storage key, which is derived from the account key inside an approved request. The bucket's access policy stays as a second line. |
| A hosted bridge sees what it carries | While unlocked, the bridge sees every message passing through it, and so does anyone who controls its machine if attestation fails. It cannot start without the user's device, and cannot read the mirror's history (5.4.2). |
| A hosted bridge is a device on the user's chat accounts | The other people in a conversation agreed to the user's devices, not to a hosted one, and are not told. Its identity at the chat service lasts until it is unlinked, and a chat service's terms may forbid it. |
| Attestation trusts the hardware maker | The hosted bridge and the attested worker are only as sound as the confidential-computing hardware and its maker's keys. |
| Outputs are shaped by untrusted inputs | An injected instruction in an incoming message can steer what a model writes. The rendering rules limit what an output can send out (5.5); they do not stop the model being misled. |
| Outputs sent to a channel are plaintext to that channel | A mail or chat service sees any output the user chooses to send it in full. |
