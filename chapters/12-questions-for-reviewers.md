# 9. Questions for reviewers

These seven are where review is wanted most.

1. **Search leakage.** Is a keyed trigram index acceptable for this threat model, or should tag sets be padded?
2. **Nonce budget.** One content key encrypts every message for the account's life with random 96-bit nonces, and NIST SP 800-38D limits that to 2³² uses per key. The largest account today holds about 1.6 million messages, far below that. Proposed answer: derive a new content key each year with HKDF from the account key and the year, so the limit applies per year and nothing extra is stored. Is that enough, or is a cipher that tolerates nonce reuse (AES-GCM-SIV, XAES-256-GCM) still worth adding?
3. **Rotating the account key.** Proposed answer: rotation is a re-push. The desktop makes a new account key, re-encrypts the mirror under it, including what writers added, uploads it again and deletes the old copies. That is the same path as when every holder is lost. It costs a full upload, so it is for a suspected compromise, not a schedule. Is that acceptable, or are data keys wrapped by the account key worth their extra machinery?
4. **Token lifetimes.** What expiry and renewal should each kind have: desktop, AI access and refresh, web app session, script?
5. **A second desktop.** Is a matching code shown on both screens enough to approve one, given the cross-device risks set out in RFC 10027? And how should the new desktop's token reach it without the server storing it: handed to a waiting request in memory, or sealed to a key the new desktop sends?
6. **Support audit.** Is the service's own log enough for support access, or is an independent audit worth a second key?
7. **Attestation.** Is proving which code the server runs worth adding later, to close the first limit?
