# 9. Decisions made to simplify

These choices keep the design small. Each has a cost, stated here so reviewers can challenge it.

| Decision | What it removes | What it costs |
| --- | --- | --- |
| Every source is collected on the desktop | Server-side collectors, and the public-key sealing they needed for mail that arrives while nobody is calling | A source that can only be read server-side, such as a hosted inbox or a chat bot, is out of scope until it can run on the desktop |
| The token is its own secret | Separate unlock secrets. SHA-256 of the token finds its copy; a key derived from the token with HKDF opens it, and knowing one gives nothing about the other. | A leaked token both identifies and unlocks, exactly as a leaked token-and-secret pair did before |
| Support is just another reader | The operator's hardware-held support key. To get help, the user approves a support reader with an end time, like any other. | Its use is recorded in the service's own log rather than by the cloud provider's audit log |
| Background AI work needs a reader | Server-side processing with no request open. Triage or filing runs on the desktop, or inside a reader's request. | Nothing is processed while every reader is idle |
| Attachments are encrypted by the storage service, under a key derived from the account key | Encrypting and chunking every file on the desktop | The storage service sees each file in the clear while it handles a request, and it must accept a key supplied per request. The bucket cannot hand out direct links, because every read needs the key. |
