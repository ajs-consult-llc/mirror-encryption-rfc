# How it works

The same machinery seen twice: first what happens to the account key, then what happens to the data.

## Key management lifecycle

The account key is created once on the desktop, opened only inside approved requests, changed only by adding or removing locked copies, and destroyed by deleting every copy.

<!-- diagram: where the account key lives · 2 places in the clear -->
```mermaid
---
title: "The account key exists in the clear in only two places"
---
flowchart TB
  accTitle: The account key exists in the clear in only two places
  accDescr: Where the account key lives, where only a locked copy lives, and where it never goes. In the clear, the key exists only in the desktop OS keystore, at rest on each approved desktop and made on the first one, and in server memory, with its two derived keys, for one approved request only. Only a locked copy is in the database, one copy per approved token wrapped under a key from it, and in backups, where deleted copies stay until the backup expires, up to 30 days. The AIs, board and scripts hold a token but never the key, and the server unlocks it for them. AI providers see only the results they asked for. Logs and operator staff hold no key, no token and no plaintext. A token opens only its own copy, so deleting that copy cuts its holder off at once.
  subgraph never["Never holds the key"]
    direction TB
    N1["AIs, board and scripts<br/>hold a token, never the<br/>key, the server unlocks<br/>it for them"]
    N2["AI providers<br/>see only the results<br/>they asked for"]
    N3["Logs and operator staff<br/>no key, no token,<br/>no plaintext"]
    N1 ~~~ N2 ~~~ N3
  end
  subgraph locked["Only a locked copy"]
    direction TB
    L1["Database<br/>one copy per approved<br/>token, wrapped under<br/>a key from it"]
    L2["Backups<br/>deleted copies stay<br/>until the backup expires,<br/>up to 30 days"]
    L1 ~~~ L2
  end
  subgraph clear["In the clear"]
    direction TB
    K1["Desktop OS keystore<br/>the key at rest, on each<br/>approved desktop, made<br/>on the first one"]
    K2["Server memory<br/>the key and its two<br/>derived keys, for one<br/>approved request only"]
    K1 ~~~ K2
  end
  classDef hot stroke:#c8932e,fill:#fbf3e3,color:#1f2933
  class K1,K2 hot
```

Only a desktop keystore holds the account key at rest. The server holds it in memory for one request at a time; everything else holds a locked copy, a token, or nothing.

Every change to who can read the mirror is a copy of the account key added or deleted; the account key itself changes only if it is rotated.

### Create

On first run, the desktop app generates the account key from 256 random bits and stores it in the OS keystore. It then signs in, receives its own desktop token, wraps the account key under a key derived from that token, and uploads only that locked copy. The server stores the copy beside the token’s hash; it never sees the account key and never keeps the token.

<!-- diagram: create · 4 parties -->
```mermaid
---
title: "The account key is born on the desktop, and only a locked copy reaches the server"
---
sequenceDiagram
  accTitle: The account key is born on the desktop, and only a locked copy reaches the server
  accDescr: Create. The desktop app generates the account key from 256 random bits and stores it in the OS keystore. It signs in and asks the server for a desktop token, and the server replies with one. The desktop app wraps the account key under a key derived from the token and sends the locked copy to the server, which stores the token's hash and the copy in the database. The account key never leaves the desktop in the clear.
  participant D as Desktop app
  participant S as Server
  participant DB as Database
  Note over D: generate the account key from 256<br/>random bits
  Note over D: store the account key in the OS<br/>keystore
  D->>S: sign in, ask for a desktop token
  S-->>D: a desktop token
  Note over D: wrap the account key under a key<br/>derived from the token
  D->>S: the locked copy
  S->>DB: store the token's hash and the copy
  Note over D: The account key never leaves the<br/>desktop in the clear.
```

**Why this is best practice.** The key is made from a cryptographically secure random source on the device that will hold it, which is what [NIST SP 800-133 Rev. 2](https://csrc.nist.gov/pubs/sp/800/133/r2/final) recommends, and it is stored in the OS key store, hardware-backed where the platform offers it, rather than in a file. The server receives only a wrapped copy ([NIST SP 800-38F](https://csrc.nist.gov/pubs/sp/800/38/f/final)), so nothing the server stores can open the data. That separation is the core idea of client-side and envelope encryption.

### Read

A reader's request carries its token. The server finds the reader's locked copy by the token’s hash, derives the unwrapping key from the token with HKDF, and opens the account key in memory. It looks up the query's tags, decrypts only the candidate rows and returns the results. When the request ends, the account key is dropped; nothing of it is written to disk or logs.

<!-- diagram: read · 3 parties -->
```mermaid
---
title: "The account key is unwrapped for one request and never written down"
---
sequenceDiagram
  accTitle: The account key is unwrapped for one request and never written down
  accDescr: Read. A reader or writer sends a request carrying its token. The server looks up the token's hash in the database and gets back its locked copy. A key derived from the token unwraps the account key, in memory only. The server looks up the query's tags and gets back ciphertext rows, decrypts the candidates and builds the answer, and returns the results. The request ends and the account key is dropped.
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  R->>S: a request carrying its token
  S->>DB: look up the token's hash
  DB-->>S: its locked copy
  Note over S: a key derived from the token<br/>unwraps the account key, in memory<br/>only
  S->>DB: look up the query's tags
  DB-->>S: ciphertext rows
  Note over S: decrypt the candidates, build the<br/>answer
  S-->>R: the results
  Note over S,DB: The request ends and the account<br/>key is dropped.
```

**Why this is best practice.** The key is opened only in memory, only for one request, and then dropped. That follows [NIST SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final): keep plaintext keys out of persistent storage and out of logs, and limit how long they exist. The unwrapping key is derived from the token with HKDF ([RFC 5869](https://www.rfc-editor.org/rfc/rfc5869)), the standard way to turn a high-entropy secret into a key, and the server looks tokens up by hash, so its stored data holds no usable credential.

### Update

When the user approves a new reader or writer, the approval happens inside a session that already holds the account key. The server makes a new token, wraps the account key under a key derived from it, stores that copy beside the new token’s hash, and hands the new token to the new holder once. Renewing a token follows the same steps, then deletes the old token's hash and copy. The account key itself does not change.

<!-- diagram: update · 4 parties -->
```mermaid
---
title: "A new holder gets its own copy, made inside the user's session"
---
sequenceDiagram
  accTitle: A new holder gets its own copy, made inside the user's session
  accDescr: Update. The user approves a new reader or writer, inside a session that holds the account key. The server makes a new token and wraps the account key under a key derived from it, stores the new token's hash and the copy in the database, and hands the new token to the reader or writer once. Renewal runs the same steps, then deletes the old token's hash and copy.
  participant U as User
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  U->>S: approve, inside a session that holds the account key
  Note over S: make a new token, wrap the account<br/>key under a key derived from it
  S->>DB: store the new token's hash and the copy
  S-->>R: the new token, handed over once
  Note over R,DB: Renewal runs the same steps, then<br/>deletes the old token's hash and<br/>copy.
```

**Why this is best practice.** Granting access means wrapping the same key once more, not re-encrypting data or sharing one credential among holders. This is envelope encryption, the pattern cloud key-management services use, and it means every holder can be revoked on its own. Handing a new token over once and rotating it on renewal follows the OAuth security best current practice ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)).

### Expire

Every token has an end time, stored beside its hash. The server refuses an expired token on every request, and a periodic sweep then deletes the expired token's hash and its copy of the account key. A holder renews before its end time by presenting its current token, which follows Update; a refresh token presented twice revokes its whole chain. The lifetime for each kind of holder is question 4. Backups can still hold an expired copy for up to 30 days (see What it does not protect).

<!-- diagram: expire · 3 parties -->
```mermaid
---
title: "An expired token finds no copy and is refused"
---
sequenceDiagram
  accTitle: An expired token finds no copy and is refused
  accDescr: Expire. The server finds copies past their expiry in the database and deletes each one's hash and copy. When a reader or writer then sends a request with the expired token, the server refuses it, and the holder must renew or be approved again. The account key itself is rotated before its nonce budget runs out, by re-encrypting or by re-wrapping data keys (questions 2 to 4).
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  S->>DB: find copies past their expiry
  S->>DB: delete each one's hash and copy
  R->>S: a request with the expired token
  S-->>R: refused, renew or re-approve
  Note over R,DB: The account key is rotated before<br/>its nonce budget runs out, by<br/>re-encrypting or re-wrapping data<br/>keys (questions 2 to 4).
```

**Why this is best practice.** Every token has a fixed lifetime, and its copy of the key is deleted when that lifetime ends, so a leaked token stops working without anyone acting. Bounded lifetimes are what [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) recommends for tokens, and NIST calls them cryptoperiods ([SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)).

### Delete

The user ends access in one of three ways, each from an approved device:

- **Revoke one reader or writer** (an AI, a browser session, a script). The server deletes that token's hash and its copy of the account key. That holder is cut off at once, and every other holder keeps working.
- **Remove a lost device.** The same deletion, for the device's token. Recovery then runs as an Update from a device the user still has.
- **Delete the account.** The server deletes every copy and every row. With no copy of the account key left, nothing live can open the mirror.

Backups still hold old copies until they expire, up to 30 days. If every holder is lost, the next desktop makes a new account key and collects again from the sources.

<!-- diagram: delete · 4 parties -->
```mermaid
---
title: "Deleting copies is how access ends"
---
sequenceDiagram
  accTitle: Deleting copies is how access ends
  accDescr: Delete. The user revokes a token, or deletes the account. The server deletes that token's hash and copy, or every copy and row. Backups keep old copies until they expire, up to 30 days. If every holder is lost, the next desktop makes a new account key and collects again.
  participant U as User
  participant S as Server
  participant DB as Database
  U->>S: revoke a token, or delete the account
  S->>DB: delete the hash and copy, or every copy and row
  Note over S,DB: Backups keep old copies until they<br/>expire, up to 30 days.
  Note over U: If every holder is lost, the next<br/>desktop makes a new account key<br/>and collects again.
```

**Why this is best practice.** Deleting every copy of the key, as account deletion does, is cryptographic erase, a sanitization method NIST recognizes ([SP 800-88 Rev. 1](https://csrc.nist.gov/pubs/sp/800/88/r1/final)). It works at once, even when ciphertext remains in storage the user cannot reach. Revoking a single holder is weaker: it ends that holder's access through the service, but other copies of the same key remain. Revocation takes effect server-side on the token's next use, as OAuth token revocation specifies ([RFC 7009](https://www.rfc-editor.org/rfc/rfc7009)). The known exception is backups, which keep old copies for up to 30 days.

## How data moves

Five flows cover everything the system does. In each one, the account key is opened only inside a request that presents an approved token.

### Collect and push

New messages are locked on the user's own computer before they go anywhere, so the service stores only ciphertext, which opens only inside an approved request.

1. The desktop app reads a new message from a source on the desktop: mail, messaging apps, team chat, a calendar.
2. It encrypts the message under the content key and computes its search tags under the tag key, both derived from the account key.
3. It uploads the ciphertext and tags over TLS, presenting its own token. The server stores them and cannot open them without an approved token.
4. The message is searchable as soon as it is stored.

<!-- diagram: collect and push · 4 parties -->
```mermaid
---
title: "Messages are encrypted on the desktop before they leave it"
---
sequenceDiagram
  accTitle: Messages are encrypted on the desktop before they leave it
  accDescr: Collect and push. The desktop app reads a new message from a local source, such as mail, chat or calendar. It encrypts the message under the account key and computes its search tags. It sends the ciphertext and tags to the server over TLS, with its token. The server stores them and cannot read them. The message is searchable as soon as it is stored.
  participant D as Desktop app
  participant S as Server
  participant DB as Database
  Note over D: read a new message from a local<br/>source, mail, chat or calendar
  Note over D: encrypt it under the account key,<br/>compute its search tags
  D->>S: ciphertext and tags over TLS, with its token
  S->>DB: store them, the server cannot read them
  Note over S,DB: The message is searchable as soon<br/>as it is stored.
```

Only ciphertext and tags leave the desktop; the server cannot open them without an approved token.

**Why this is best practice.** Encrypting on the client before upload, so the storage provider holds only ciphertext, is the model behind end-to-end encrypted storage and client-side encryption. Each message is sealed with AES-256-GCM ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final)), an authenticated cipher that detects any change to the ciphertext, and it is bound to its account and message ids as associated data ([RFC 5116](https://www.rfc-editor.org/rfc/rfc5116)), so a row cannot be moved to another account or message. TLS protects the upload in transit ([RFC 8446](https://www.rfc-editor.org/rfc/rfc8446)).

### Approve a reader or writer

Nothing gets access unless the user says yes, and every approved AI, browser or device gets its own key that can be cancelled on its own.

1. The user approves it: OAuth consent for an AI, the web app opened from the desktop, or a matching code for a second device.
2. Inside the user's own approved session, the server makes a new token and a copy of the account key locked under it.
3. The token is handed to the new reader or writer once. The server keeps only its hash.

<!-- diagram: approve a reader or writer · 4 parties -->
```mermaid
---
title: "Approving a reader or writer creates one token and one copy of the account key"
---
sequenceDiagram
  accTitle: Approving a reader or writer creates one token and one copy of the account key
  accDescr: Approve a reader or writer. The user approves it by OAuth consent, by the web app opened from the desktop, or with a matching code. Inside the user's session, the server makes a token and a copy of the account key locked under it, stores the token's hash and the copy in the database, and hands the token to the reader or writer once.
  participant U as User
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  U->>S: approve by OAuth consent, the web app opened from the desktop, or a matching code
  Note over S: inside the user's session, make a<br/>token and a copy of the account<br/>key locked under it
  S->>DB: store the token's hash and the copy
  S-->>R: the token, handed over once
```

The server keeps only the token’s hash; the token itself is handed over once.

**Why this is best practice.** AI clients are approved through OAuth consent with PKCE, as the OAuth security best current practice requires ([RFC 9700](https://www.rfc-editor.org/rfc/rfc9700)), and a second device is approved by comparing a short code on both screens, a relative of the device flow in [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628). Giving each holder its own token and its own wrapped copy of the key is least privilege: no credential is shared, so each one can be revoked alone. Storing only a hash of each token means a database copy yields no usable credential, as [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) requires for stored passwords.

### Search and retrieve

An approved AI gets answers in well under a second, and the data is unlocked only for that one question, then locked again.

1. A reader sends a query with its token.
2. The server finds the token's copy by its hash and unlocks the account key for this request.
3. It turns the query into tags, finds the candidates in the index, decrypts only those, and checks the real match.
4. It returns the results and drops the account key.

<!-- diagram: search and retrieve · 3 parties, one request -->
```mermaid
---
title: "The account key is unlocked for one request and dropped when it ends"
---
sequenceDiagram
  accTitle: The account key is unlocked for one request and dropped when it ends
  accDescr: Search and retrieve. A reader or writer sends a query with its token. The server finds the token's copy by its hash, unlocks the account key for this request and turns the query into tags. It finds the candidates in the index and gets back candidate rows, still ciphertext. It decrypts only the candidates, checks the real match, and returns the results. The request ends and the account key is dropped.
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  R->>S: a query, with its token
  S->>DB: find the token's copy by its hash
  Note over S: unlock the account key for this<br/>request, turn the query into tags
  S->>DB: find the candidates in the index
  DB-->>S: candidate rows, still ciphertext
  Note over S: decrypt only the candidates, check<br/>the real match
  S-->>R: the results
  Note over S,DB: The request ends and the account<br/>key is dropped.
```

Only the candidate rows are decrypted, and the account key lives only for the request.

**Why this is best practice.** Search runs on keyed tags, the standard construction for searching encrypted data ([Song, Wagner and Perrig, IEEE S&P 2000](https://people.eecs.berkeley.edu/~dawnsong/papers/se.pdf)). The query is reduced to trigrams and the real match is checked afterwards, as in production regex search ([Russ Cox, trigram index](https://swtch.com/~rsc/regexp/regexp4.html)). Holding the key in memory for one request only follows [NIST SP 800-57 Part 1](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final) on limiting how long plaintext keys exist. The known cost is access-pattern leakage ([Cash et al., CCS 2015](https://eprint.iacr.org/2016/718)), which question 1 puts to reviewers.

### Update

Edits by an approved AI or by the user are locked the moment they are saved, and every other reader sees them on its next request.

1. A writer sends a change with its token: an AI's tool call, or an edit on the web app.
2. The server unlocks the account key, encrypts the change, recomputes its tags and stores it.
3. Every reader sees it on its next request.

<!-- diagram: update · 4 parties -->
```mermaid
---
title: "A writer's change is encrypted on the server and seen on the next read"
---
sequenceDiagram
  accTitle: A writer's change is encrypted on the server and seen on the next read
  accDescr: Update. A reader or writer sends a change with its token, such as an AI tool call or a web-app edit. The server unlocks the account key, encrypts the change, recomputes its tags and stores it. On any reader's next request, the server returns the updated message.
  participant R as Reader or writer
  participant S as Server
  participant DB as Database
  R->>S: a change with its token, an AI tool call or a web-app edit
  Note over S: unlock the account key, encrypt<br/>the change, recompute its tags
  S->>DB: store it
  R->>S: any reader's next request
  S-->>R: the updated message
```

Writes follow the same rule as reads: the account key is opened only inside the writer’s request.

**Why this is best practice.** A write uses the same authenticated encryption as a read, so the server never stores an edited row in the clear. Every write gets a fresh random nonce, which is what keeps AES-GCM secure when the same key encrypts many messages ([NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final), section 8). The tags are recomputed with HMAC-SHA256 ([FIPS 198-1](https://csrc.nist.gov/pubs/fips/198-1/final)), so the search index never falls out of step with the content.

### Revoke and recover

Cutting off an AI or a lost device takes effect at once and touches no one else; a replacement device is approved like any other.

- **Revoke.** Deleting a token's hash and copy cuts that reader or writer off at once.
- **A lost desktop.** From another approved device the user revokes it, then approves a new desktop, which receives the account key through its own copy.
- **The only desktop lost.** A recovery code made at setup is one more token, printed and kept offline, with its own locked copy. Presented from a new desktop, it approves that desktop. Without one, the mirror starts again with a new account key even if AI readers still hold tokens, because a reader's token cannot approve a device.
- **Every holder lost.** The mirror cannot be read. A new desktop makes a new account key and collects again from the sources.

<!-- diagram: revoke and recover · 4 parties -->
```mermaid
---
title: "Revoking deletes a copy, and recovery needs another approved device"
---
sequenceDiagram
  accTitle: Revoking deletes a copy, and recovery needs another approved device
  accDescr: Revoke and recover. The user revokes a token, or a lost desktop, and the server deletes its hash and its copy in the database. A new desktop asks the server to join, the user approves the new desktop, and the server gives the new desktop its own token, which opens its own copy of the account key. If every holder is lost, the mirror cannot be read, and a new desktop makes a new account key and collects again from the sources.
  participant U as User
  participant D as Desktop app
  participant S as Server
  participant DB as Database
  U->>S: revoke a token, or a lost desktop
  S->>DB: delete its hash and its copy
  D->>S: a new desktop asks to join
  U->>S: approve the new desktop
  S-->>D: its own token, which opens its own copy of the account key
  Note over D,DB: If every holder is lost, the<br/>mirror cannot be read. A new<br/>desktop makes a new account key<br/>and collects again from the<br/>sources.
```

Cutting off a reader is one deletion; a replacement desktop is approved like any other holder.

**Why this is best practice.** Revoking a token server-side, so that it fails on its next use, is what OAuth token revocation specifies ([RFC 7009](https://www.rfc-editor.org/rfc/rfc7009)). Deleting that token's copy ends its access through the service. Only deleting every copy is cryptographic erase, the sanitization method NIST recognizes ([SP 800-88 Rev. 1](https://csrc.nist.gov/pubs/sp/800/88/r1/final)). Recovering through another approved device, rather than through a reset the operator controls, keeps the operator unable to open the data. End-to-end encrypted services use the same approach, and when every holder is lost the honest result is that the data cannot be read.
