# 5. How it works

The same machinery seen twice: first what happens to the account key, then what happens to the data.

## 5.1 Key management lifecycle

The account key is created once on the desktop, opened only inside approved requests, changed only by adding or removing locked copies, and destroyed by deleting every copy.

<!-- diagram: Figure 5.1. Where the account key lives in the clear, and where only locked copies exist -->
![The account key exists in the clear in only two places](../figures/where-the-account-key-lives-2-places-in-the-clear.png)

**Figure 5.1.** Where the account key lives in the clear, and where only locked copies exist · [Text version](14-appendix-b-the-diagrams-as-text.md#where-the-account-key-lives-2-places-in-the-clear)
<!-- /diagram -->

Only a desktop keystore holds the account key at rest. The server holds it in memory for one request at a time; everything else holds a locked copy, a token, or nothing. An attested worker, if the user unlocks one, holds it in memory for the length of its lease (5.5).

Every change to who can read the mirror is a copy of the account key added or deleted; the account key itself changes only if it is rotated.

### 5.1.1 Create

On first run, the desktop app generates the account key from 256 random bits and stores it in the OS keystore. It then signs in, receives its own desktop token, wraps the account key under a key derived from that token, and uploads only that locked copy. The server stores the copy beside the token’s hash; it never sees the account key and never keeps the token.

<!-- diagram: Figure 5.2. Create: the desktop makes the account key and uploads only a locked copy -->
![The account key is born on the desktop, and only a locked copy reaches the server](../figures/create-4-parties.png)

**Figure 5.2.** Create: the desktop makes the account key and uploads only a locked copy · [Text version](14-appendix-b-the-diagrams-as-text.md#create-4-parties)
<!-- /diagram -->

**Why this is best practice.** The key is made from a cryptographically secure random source on the device that will hold it, which is what [NIST SP 800-133 Rev. 2](https://csrc.nist.gov/pubs/sp/800/133/r2/final) recommends, and it is stored in the OS key store, hardware-backed where the platform offers it, rather than in a file. The server receives only a wrapped copy ([NIST SP 800-38F](https://csrc.nist.gov/pubs/sp/800/38/f/final)), so nothing the server stores can open the data. That separation is the core idea of client-side and envelope encryption.

### 5.1.2 Read

A reader's request carries its token. The server finds the reader's locked copy by the token’s hash, derives the unwrapping key from the token with HKDF, and opens the account key in memory. It looks up the query's tags, decrypts only the candidate rows and returns the results. When the request ends, the account key is dropped; nothing of it is written to disk or logs.

<!-- diagram: Figure 5.3. Read: a token opens its copy of the account key for one request -->
![The account key is unwrapped for one request and never written down](../figures/read-3-parties.png)

**Figure 5.3.** Read: a token opens its copy of the account key for one request · [Text version](14-appendix-b-the-diagrams-as-text.md#read-3-parties)
<!-- /diagram -->

**Why this is best practice.** The key is opened only in memory, only for one request, and then dropped. That follows [NIST SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final): keep plaintext keys out of persistent storage and out of logs, and limit how long they exist. The unwrapping key is derived from the token with HKDF ([RFC 5869](https://www.rfc-editor.org/rfc/rfc5869)), the standard way to turn a high-entropy secret into a key, and the server looks tokens up by hash, so its stored data holds no usable credential.

### 5.1.3 Update

When the user approves a new reader or writer, the approval happens inside a session that already holds the account key. The server makes a new token, wraps the account key under a key derived from it, stores that copy beside the new token’s hash, and hands the new token to the new holder once. Renewing a token follows the same steps, then deletes the old token's hash and copy. The account key itself does not change.

<!-- diagram: Figure 5.4. Update: a new reader or writer gets its own token and its own locked copy -->
![A new holder gets its own copy, made inside the user's session](../figures/update-4-parties.png)

**Figure 5.4.** Update: a new reader or writer gets its own token and its own locked copy · [Text version](14-appendix-b-the-diagrams-as-text.md#update-4-parties)
<!-- /diagram -->

**Why this is best practice.** Granting access means wrapping the same key once more, not re-encrypting data or sharing one credential among holders. This is envelope encryption, the pattern cloud key-management services use, and it means every holder can be revoked on its own. Handing a new token over once and rotating it on renewal follows the OAuth security best current practice ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)).

### 5.1.4 Expire

Every token has an end time, stored beside its hash. The server refuses an expired token on every request, and a periodic sweep then deletes the expired token's hash and its copy of the account key. A holder renews before its end time by presenting its current token, which follows Update; a refresh token presented twice revokes its whole chain. The lifetime for each kind of holder is question 4. Backups can still hold an expired copy for up to 30 days (see What it does not protect).

<!-- diagram: Figure 5.5. Expire: an expired token is refused and its copy is deleted -->
![An expired token finds no copy and is refused](../figures/expire-3-parties.png)

**Figure 5.5.** Expire: an expired token is refused and its copy is deleted · [Text version](14-appendix-b-the-diagrams-as-text.md#expire-3-parties)
<!-- /diagram -->

**Why this is best practice.** Every token has a fixed lifetime, and its copy of the key is deleted when that lifetime ends, so a leaked token stops working without anyone acting. Bounded lifetimes are what [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) recommends for tokens, and NIST calls them cryptoperiods ([SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)).

### 5.1.5 Delete

The user ends access in one of three ways, each from an approved device:

- **Revoke one reader or writer** (an AI, a browser session, a script). The server deletes that token's hash and its copy of the account key. That holder is cut off at once, and every other holder keeps working.
- **Remove a lost device.** The same deletion, for the device's token. Recovery then runs as an Update from a device the user still has.
- **Delete the account.** The server deletes every copy and every row. With no copy of the account key left, nothing live can open the mirror.

Backups still hold old copies until they expire, up to 30 days. If every holder is lost, the next desktop makes a new account key and collects again from the sources.

<!-- diagram: Figure 5.6. Delete: access ends when a token's hash and its copy are deleted -->
![Deleting copies is how access ends](../figures/delete-4-parties.png)

**Figure 5.6.** Delete: access ends when a token's hash and its copy are deleted · [Text version](14-appendix-b-the-diagrams-as-text.md#delete-4-parties)
<!-- /diagram -->

**Why this is best practice.** Deleting every copy of the key, as account deletion does, is cryptographic erase, a sanitization method NIST recognizes ([SP 800-88 Rev. 1](https://csrc.nist.gov/pubs/sp/800/88/r1/final)). It works at once, even when ciphertext remains in storage the user cannot reach. Revoking a single holder is weaker: it ends that holder's access through the service, but other copies of the same key remain. Revocation takes effect server-side on the token's next use, as OAuth token revocation specifies ([RFC 7009](https://www.rfc-editor.org/rfc/rfc7009)). The known exception is backups, which keep old copies for up to 30 days.

## 5.2 How data moves

Five flows cover everything the system does. In each one, the account key is opened only inside a request that presents an approved token.

### 5.2.1 Collect and push

New messages are locked on the user's own computer before they go anywhere, so the service stores only ciphertext, which opens only inside an approved request.

1. The desktop app reads a new message from a source on the desktop: mail, messaging apps, team chat, a calendar.
2. It encrypts the message under the content key and computes its search tags under the tag key, both derived from the account key.
3. It uploads the ciphertext and tags over TLS, presenting its own token. The server stores them and cannot open them without an approved token.
4. The message is searchable as soon as it is stored.

<!-- diagram: Figure 5.7. Collect and push: messages are encrypted on the desktop before upload -->
![Messages are encrypted on the desktop before they leave it](../figures/collect-and-push-4-parties.png)

**Figure 5.7.** Collect and push: messages are encrypted on the desktop before upload · [Text version](14-appendix-b-the-diagrams-as-text.md#collect-and-push-4-parties)
<!-- /diagram -->

Only ciphertext and tags leave the desktop; the server cannot open them without an approved token.

**Why this is best practice.** Encrypting on the client before upload, so the storage provider holds only ciphertext, is the model behind end-to-end encrypted storage and client-side encryption. Each message is sealed with AES-256-GCM ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final)), an authenticated cipher that detects any change to the ciphertext, and it is bound to its account and message ids as associated data ([RFC 5116](https://www.rfc-editor.org/rfc/rfc5116)), so a row cannot be moved to another account or message. TLS protects the upload in transit ([RFC 8446](https://www.rfc-editor.org/rfc/rfc8446)).

### 5.2.2 Approve a reader or writer

Nothing gets access unless the user says yes, and every approved AI, browser or device gets its own key that can be cancelled on its own.

1. The user approves it: OAuth consent for an AI, the web app opened from the desktop, or a matching code for a second device.
2. Inside the user's own approved session, the server makes a new token and a copy of the account key locked under it.
3. The token is handed to the new reader or writer once. The server keeps only its hash.

<!-- diagram: Figure 5.8. Approve a reader or writer: one approval, one token, one locked copy -->
![Approving a reader or writer creates one token and one copy of the account key](../figures/approve-a-reader-or-writer-4-parties.png)

**Figure 5.8.** Approve a reader or writer: one approval, one token, one locked copy · [Text version](14-appendix-b-the-diagrams-as-text.md#approve-a-reader-or-writer-4-parties)
<!-- /diagram -->

The server keeps only the token’s hash; the token itself is handed over once.

**Why this is best practice.** AI clients are approved through OAuth consent with PKCE, as the OAuth security best current practice requires ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)), and a second device is approved by comparing a short code on both screens, a relative of the device flow in [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628), with the cross-device risks that [RFC 10027](https://www.rfc-editor.org/rfc/rfc10027) sets out. Giving each holder its own token and its own wrapped copy of the key is least privilege: no credential is shared, so each one can be revoked alone. Storing only a hash of each token means a database copy yields no usable credential, as [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) requires for stored passwords.

### 5.2.3 Search and retrieve

An approved AI gets answers in well under a second, and the data is unlocked only for that one question, then locked again.

1. A reader sends a query with its token.
2. The server finds the token's copy by its hash and unlocks the account key for this request.
3. It turns the query into tags, finds the candidates in the index, decrypts only those, and checks the real match.
4. It returns the results and drops the account key.

<!-- diagram: Figure 5.9. Search and retrieve: the account key is opened for one request only -->
![The account key is unlocked for one request and dropped when it ends](../figures/search-and-retrieve-3-parties-one-request.png)

**Figure 5.9.** Search and retrieve: the account key is opened for one request only · [Text version](14-appendix-b-the-diagrams-as-text.md#search-and-retrieve-3-parties-one-request)
<!-- /diagram -->

Only the candidate rows are decrypted, and the account key lives only for the request.

**Why this is best practice.** Search runs on keyed tags, the standard construction for searching encrypted data ([Song, Wagner and Perrig, IEEE S&P 2000](https://people.eecs.berkeley.edu/~dawnsong/papers/se.pdf)). The query is reduced to trigrams and the real match is checked afterwards, as in production regex search ([Russ Cox, trigram index](https://swtch.com/~rsc/regexp/regexp4.html)). Holding the key in memory for one request only follows [NIST SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final) on limiting how long plaintext keys exist. The known cost is access-pattern leakage ([Cash et al., CCS 2015](https://eprint.iacr.org/2016/718)), which question 1 puts to reviewers.

### 5.2.4 Update

Edits by an approved AI or by the user are locked the moment they are saved, and every other reader sees them on its next request.

1. A writer sends a change with its token: an AI's tool call, or an edit on the web app.
2. The server unlocks the account key, encrypts the change, recomputes its tags and stores it.
3. Every reader sees it on its next request.

<!-- diagram: Figure 5.10. Update: a writer's change is encrypted on the server inside its request -->
![A writer's change is encrypted on the server and seen on the next read](../figures/update-4-parties-2.png)

**Figure 5.10.** Update: a writer's change is encrypted on the server inside its request · [Text version](14-appendix-b-the-diagrams-as-text.md#update-4-parties-2)
<!-- /diagram -->

Writes follow the same rule as reads: the account key is opened only inside the writer’s request.

**Why this is best practice.** A write uses the same authenticated encryption as a read, so the server never stores an edited row in the clear. Every write gets a fresh random nonce, which is what keeps AES-GCM secure when the same key encrypts many messages ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final), section 8). The tags are recomputed with HMAC-SHA256 ([FIPS 198-1](https://csrc.nist.gov/pubs/fips/198-1/final)), so the search index never falls out of step with the content.

### 5.2.5 Revoke and recover

Cutting off an AI or a lost device takes effect at once and touches no one else; a replacement device is approved like any other.

- **Revoke.** Deleting a token's hash and copy cuts that reader or writer off at once.
- **A lost desktop.** From another approved device the user revokes it, then approves a new desktop, which receives the account key through its own copy.
- **The only desktop lost.** A recovery code made at setup is one more token, printed and kept offline, with its own locked copy. Presented from a new desktop, it approves that desktop. Without one, the mirror starts again with a new account key even if AI readers still hold tokens, because a reader's token cannot approve a device.
- **Every holder lost.** The mirror cannot be read. A new desktop makes a new account key and collects again from the sources.

<!-- diagram: Figure 5.11. Revoke and recover: one deletion cuts a holder off, and recovery needs another approved device -->
![Revoking deletes a copy, and recovery needs another approved device](../figures/revoke-and-recover-4-parties.png)

**Figure 5.11.** Revoke and recover: one deletion cuts a holder off, and recovery needs another approved device · [Text version](14-appendix-b-the-diagrams-as-text.md#revoke-and-recover-4-parties)
<!-- /diagram -->

Cutting off a reader is one deletion; a replacement desktop is approved like any other holder.

**Why this is best practice.** Revoking a token server-side, so that it fails on its next use, is what OAuth token revocation specifies ([RFC 7009](https://www.rfc-editor.org/rfc/rfc7009)). Deleting that token's copy ends its access through the service. Only deleting every copy is cryptographic erase, the sanitization method NIST recognizes ([SP 800-88 Rev. 1](https://csrc.nist.gov/pubs/sp/800/88/r1/final)). Recovering through another approved device, rather than through a reset the operator controls, keeps the operator unable to open the data. End-to-end encrypted services use the same approach, and when every holder is lost the honest result is that the data cannot be read.

## 5.3 The chain of joins

The service joins systems that were built separately, and each join decides who can read. End-to-end encryption survives a join only where the join point is one of the user's own endpoints, and the whole chain is only as strong as its weakest hop.

| Hop | Join point | Who can read at that point | What sets the guarantee |
| --- | --- | --- | --- |
| An end-to-end encrypted chat to the collector | The collector node | With the desktop node, only the user's own devices. With a hosted bridge, the bridge as well (5.4.2) | The chat's own protocol, then this design |
| A hosted source (mail, calendars, contacts, device clouds) to the collector | The collector node | The source's provider, which already could | The source's provider: these sources were never end-to-end encrypted |
| The collector to the mirror | The server, inside an approved request | The server, during that request | This design: encryption under the user's keys. End-to-end encryption ends here |
| The mirror to an AI reader | The AI provider | The AI provider | The provider's terms and retention |
| An output to a delivery channel | A mail or chat service | That service, and any recipient | The user's choice for each delivery (5.5) |

**Why this is best practice.** The IETF's MIMI working group joins separately run messaging services by making every client a member of one end-to-end security state: servers relay ciphertext and take part only as senders who can authenticate, not read ([draft-ietf-mimi-arch](https://datatracker.ietf.org/doc/draft-ietf-mimi-arch/), over MLS, [RFC 9420](https://www.rfc-editor.org/rfc/rfc9420)). A join point that decrypts and re-encrypts is a participant, and confidentiality is broken wherever content can be decrypted between the ends ([draft-knodel-e2ee-definition](https://datatracker.ietf.org/doc/draft-knodel-e2ee-definition/), section 2). The security questions interoperability raises, identity, protocols and abuse, are laid out by [Len, Ghosh, Grubbs and Rösler (2023)](https://eprint.iacr.org/2023/386). This design states the guarantee of every hop rather than claiming one for the whole chain.

## 5.4 Two ways to collect: the desktop node and the hosted bridge

Every source is collected by a node that only the user's key can unlock: the desktop app the user runs, or a bridge the service hosts for them. Both write into the same mirror, under the same account key.

### 5.4.1 The desktop node

The desktop node is the pattern in 5.2.1. It holds the account key, reads each source on the user's machine, and encrypts and tags each message before upload. It is the strongest pattern: an end-to-end encrypted chat stays end-to-end encrypted as far as the user's own device. Its cost is that every user must run one, and the mirror is only as fresh as that machine.

### 5.4.2 The hosted bridge

A hosted bridge does the desktop's collecting on the service's machines, so the user needs no desktop running. For an end-to-end encrypted chat it is a server-side bridge: a linked device of the user's account that sees every message it carries. The design cannot change that. What it can do is make sure the bridge runs only for the user, unlocked by the user's key.

1. **It starts locked.** At rest, the bridge's state (its linked-device keys, session state and source credentials) is ciphertext under a bridge key derived from the account key with HKDF. A copy of that state cannot run, and cannot fork a chat's message ratchet.
2. **The user's device unlocks it after checking what it runs.** The bridge runs in a confidential virtual machine. On start it makes a one-time key pair and an attestation that binds the public key to the measurement of its image. An approved device of the user checks that measurement against a published, append-only log of release images, then seals the bridge key to the one-time public key. After any restart the bridge stays locked until a device unlocks it again, and the chat services hold messages meanwhile.
3. **The unlock is a lease.** The unlock expires (proposed: 7 days), and the user's approved devices renew it in the background. When no device renews it, the bridge erases the bridge key and stops.
4. **It can write but not read back.** The bridge seals each message with HPKE to the account's public key, an X25519 key pair whose private half is derived from the account key. Only an approved request can open it; that request re-encrypts the message under the content key and computes its tags, so the mirror keeps one format at rest. A compromised bridge exposes the messages passing through it while it is compromised, not the mirror's history. The bridge holds no tag key (question 9).
5. **Revocation reaches the source.** Revoking the bridge ends its lease, unlinks its device from each chat service, and rotates the bridge key. Without the unlink, the bridge's identity at the chat service outlives anything the service controls.

### 5.4.3 Which sources each pattern carries

| Source | Desktop node | Hosted bridge |
| --- | --- | --- |
| Hosted mail, calendars, contacts, and device or industrial clouds | Yes | Yes. These sources were never end-to-end encrypted, so the bridge adds the service as one more party that sees them, not a new kind of exposure |
| End-to-end encrypted chats whose service allows a third-party linked client | Yes | Yes, as a linked device (5.4.2), within that service's terms |
| End-to-end encrypted chats that require the vendor's own hardware or client | Yes | No |

**Why this is best practice.** Releasing a secret only to a machine that proves which code it runs is remote attestation ([RFC 9334](https://www.rfc-editor.org/rfc/rfc9334), the RATS architecture). Cloud key services already release keys only to an attested image ([Google Confidential Space](https://cloud.google.com/confidential-computing/confidential-space/docs/confidential-space-overview)), and having the user's device check the image against a public log before it sends anything is how [Apple Private Cloud Compute](https://security.apple.com/blog/private-cloud-compute/) works. Sealing to a public key with HPKE ([RFC 9180](https://www.rfc-editor.org/rfc/rfc9180)) lets a writer add data it can never read back. None of this makes the bridge an endpoint by the definition in [Knodel et al. (2025)](https://arxiv.org/abs/2412.20231); that is question 8.

## 5.5 Model outputs stay encrypted back to the user

Everything a model writes for the user is stored and delivered under the same rule as the user's own messages: readable only through a credential the user approved.

1. **Every output is a write.** A briefing, a summary, a note a model keeps between runs, a title or a label is encrypted under the content key, with its own tags, inside the request or worker that made it (5.2.4). Nothing a model writes is stored in the clear, including fields that look like metadata, such as a briefing's title.
2. **Outputs remember their sources.** Each derived row records, encrypted, the ids of the rows it was made from. Deleting or revoking a source deletes, or marks for regeneration, what was derived from it, so a summary cannot outlive the messages it summarises.
3. **Unattended output runs only where the user's key is unlocked.** In order of preference: when the user opens it, inside that session; inside the desktop's or the bridge's own push; or in an attested worker unlocked and leased exactly like the hosted bridge (5.4.2), with its own key and lease so it can be revoked on its own. Unlike the bridge, the worker reads the mirror, so it is the one place unattended reading happens.
4. **Delivery carries a pointer by default.** A notification says a briefing is ready and links to it; the text opens inside an approved session. Sending the full text to a channel that can read it, such as email or a chat bot, is a choice the user makes for each delivery, labelled as plaintext to that channel. Sending it to other people is the user's own disclosure.
5. **Outputs are rendered as untrusted.** Incoming messages from anyone shape what a model writes, so an output may carry an injected instruction or link. Outputs are shown without remote content, and links are shown in full or limited to an allowlist, so an output cannot send data out just by being displayed.

**Why this is best practice.** A summary is a function of the content, and [Knodel et al. (2025)](https://arxiv.org/abs/2412.20231) treat any non-trivial function of protected content as that content, so it needs the same protection. Prompt injection through content a model reads is the first risk in the [OWASP Top 10 for LLM applications](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), and it becomes exploitable when private data, untrusted content and a way to send data out meet in one system ([Willison, "The lethal trifecta"](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)). A pointer by default and rendering without remote content remove the third.
