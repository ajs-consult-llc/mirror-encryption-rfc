# Contributing

Anyone may comment on this RFC. A change counts as submitted, and is credited, only when it
arrives signed by its author through one of the channels below. The full process, and the
attacks on attribution it is built to stop, are in Appendix A of the document.

## Channels

| Channel | Counts as | Credited to |
| --- | --- | --- |
| A pull request whose every commit is signed | An official text change | The GitHub account whose registered key signed each commit |
| An issue opened with the **Submission** form | An official comment or objection | The GitHub account that opened it |
| A signed email to the submissions address | An official submission, for people without GitHub | The holder of the signing key |
| A comment in a shared copy of the document, unsigned email, a DOCX | Discussion only | Not credited until filed through a channel above |

## Proposing a text change

1. Edit the chapter in `chapters/`. Do not edit `_quarto.yml`, `index.qmd`'s first line, or
   anything under `.sync/`; they are generated.
2. Sign every commit with a GPG or SSH key registered to your GitHub account, and add a
   Developer Certificate of Origin sign-off (https://developercertificate.org/):
   ```sh
   git config commit.gpgsign true
   git commit -S -s -m "Explain the change in one line"
   ```
   The sign-off licenses your change under CC BY 4.0. It is a licence, not proof of who you are:
   the signature is.
3. Open a pull request. The **Signed commits** check fails if any commit is unsigned or cannot
   be verified.
4. The editor records a decision for each submission in `SUBMISSIONS.md`: accepted, declined
   with a reason, or deferred. Accepted pull requests merge with a merge commit, so your signed
   commits land unchanged.

Turn on GitHub's vigilant mode, so any unsigned commit made under your email shows as
Unverified.

## Security problems

Do not report a vulnerability in the running service here. Chapter 17 of the document says
where to send it privately.
