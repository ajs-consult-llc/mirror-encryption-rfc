# 8. Decisions made to simplify

These choices keep the design small. Each has a cost, stated here so reviewers can challenge it.

| Decision | What it removes | What it costs |
| --- | --- | --- |
| Every source is collected by a node the user's key unlocks: the desktop, or a hosted bridge | Server-side collectors that run without the user's key | The hosted bridge brings back public-key sealing (HPKE) for writes it cannot read back, and it means something only with attestation and a lease (5.1.2) |
| The token is its own secret | Separate unlock secrets. SHA-256 of the token finds its copy; a key derived from the token with HKDF opens it, and knowing one gives nothing about the other. | A leaked token both identifies and unlocks, exactly as a leaked token-and-secret pair did before |
| Support is just another reader | The operator's hardware-held support key. To get help, the user approves a support reader with an end time, like any other. | Its use is recorded in the service's own log rather than by the cloud provider's audit log |
| Background AI work needs a reader or an attested worker | Server-side processing the user never unlocked. Triage, filing and briefings run on the desktop, inside a reader's request, or in a worker the user unlocked under a lease (5.3). | While no reader is active and no lease is live, nothing is processed |
| Attachments are encrypted by the storage service, under a key derived from the account key | Encrypting and chunking every file on the desktop | The storage service sees each file in the clear while it handles a request, and it must accept a key supplied per request. The bucket cannot hand out direct links, because every read needs the key. |
