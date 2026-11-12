# 3. What it defends against

The design has one goal: a copy of the stored data is useless without a credential the user approved. It does not hide data from the server while the server answers an approved request.

| Who | Protected? |
| --- | --- |
| Someone who steals the database, a backup or a disk | Yes. They hold ciphertext, search tags and token hashes, and no key. The tags still leak some structure (see What it does not protect). Attachments are encrypted by the storage service under a key it does not keep, so a copy of the bucket is unreadable as well. |
| The operator's staff reading stored data | Yes, in the same way |
| A reader or writer after the user revokes it | Yes, through the service: its token no longer finds a copy |
| A compromised server, or an operator who changes the server's code | No. It sees the account key during any approved request and could keep it. |
| Malware on the user's desktop | No. The desktop holds the account key. |
