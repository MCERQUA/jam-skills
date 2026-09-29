---
name: retire-dont-delete
description: Take a delivered client asset OUT OF USE without deleting it. Three parts - an append-only index row per file (event retired, the client's own words as the reason), withdrawal from every pick/review surface, and a sha256-keyed deny list checked at the generation rig's attach step, so a renamed copy is refused too. TRIGGER when a client rejects or scratches delivered work ("get rid of them", "never use these", "start over"), when withdrawing any delivered file, or when adding an attach/reference step to an image or video rig. DO NOT TRIGGER for a privacy or erasure request (that is a real deletion; escalate to host@mesh).
---

# Retire, don't delete

**The rule in one line:** *when a client rejects delivered work, take it out of USE, not out of
EXISTENCE: one append-only index row, off every pick surface, and its bytes on a deny list that
every attach step checks.*

Needs: an upload index you can append to (every tenant has `uploads/.uploads-index.jsonl`),
python3 (stdlib only), and one `check` line in your rig's attach step.

## Why not just delete

- **Deleting the delivered copy removes the one copy that was harmless.** The ones that hurt
  are the others: the uncropped original, the drafts, the edit base the next version would be
  built on. A rig that attaches "the last good image" brings back the look the client rejected.
  Only a deny list keyed on the bytes stops that; a delete never did.
- **Filenames are not stable on this fleet.** `descriptive-rename.py` renames junk-named tenant
  uploads every 15 minutes, and people copy files under new names all the time. A rule keyed on a
  filename is a rule a rename walks past. sha256 is the key.
- **Links already sent keep working.** A message, page or ticket that carries the URL does not
  turn into a 404 that someone has to explain.
- **Approved/frozen files stay consistent.** A frozen-file sweep reads a deleted or renamed file
  as MISSING and pages every night about a withdrawal you made on purpose.
- **The history stays readable.** Delivered, then retired, then (maybe) brought back: in order,
  in one file.

## When NOT to use it

- **A privacy or erasure request** ("delete the photos of my kids", "remove my data"). That is a
  deletion, and retiring does not satisfy it. Escalate to host@mesh; a human decides.
- **Never tell anyone a retired file was deleted.** Say what you did: "removed from your review
  list and marked never to be used again." If the client then wants the files erased, that is the
  request above.

## The three parts

### 1. One append-only index row per file

`retire.py retire` appends to `<uploads>/.uploads-index.jsonl`:

```json
{"at": "...", "filename": "x.png", "size": 4096, "sha256": "...", "event": "retired",
 "retired_note": "<the client's words, verbatim>", "retired_by": "<client> via <agent> msg <id>",
 "note": "RETIRED: <same words>", "from": "$AGENT_URI"}
```

- It **refuses** an empty reason (an empty reason looks recorded and says nothing), an empty
  `--by`, and a file that is not there (retiring an absent file records nothing).
- It **never rewrites or removes** the registration row. Readers read the index **in order and
  the last row per filename wins**. A later registration row un-retires the file.
- Quote the client. "Scratch all of them" is a reason. "Client didn't like it" is a summary, and
  the next agent cannot tell from it what was rejected.

### 2. Off every pick and review surface

Anything that lists assets for a person or an agent to choose from must filter on the effective
state: `retire.py state <uploads> --live` prints only usable filenames. **An event it does not
recognise is treated as NOT live**: leaving a file out of a pick list costs little, and putting a
withdrawn one back in front of a client is the harm.

List your surfaces by name (review page, studio lane, social picker, gallery, the rig's own "last
good image" shortcut). A surface you did not wire is still showing the file.

### 3. A hash-keyed deny list, checked at the attach step

`<uploads>/.retired-refs.jsonl`, one row per sha256:
`{"sha256", "name", "where", "set", "kind", "why", "by", "at", "ref"}`.

- **Dotfile on purpose.** It holds the client's words. Measured on tenant hosts: `uploads/.x`
  answers **403** and `uploads/x` answers **200**. Never name it without the dot.
- **Put every copy in it**, not only the delivered one: `retire.py deny <files> --ledger ...`
  for uncropped originals, drafts and edit bases. Ledgers stack (`--ledger` repeats), so a rig can
  keep its own ledger beside the tenant's.
- **Check before anything is attached, and before you take a lock or start a paid job:**

  ```bash
  python3 "$RDD/retire.py" check "$REF" \
    --ledger "$UPLOADS/.retired-refs.jsonl" --ledger "$RIG/RETIRED-REFS.jsonl" || exit $?
  ```

  Exit **0** clean · **1** retired (refuse) · **3** cannot tell (refuse; never read it as a pass).
  A malformed ledger is 3: a gate that cannot read its list must not pass everything. A missing
  ledger passes **and says so** (add `--require-ledger` to make it 3 instead).

## Recipe

```bash
RDD=/mnt/system/base/skills/retire-dont-delete      # containers: /mnt/shared-skills/retire-dont-delete
U=/mnt/clients/<tenant>/openvoiceui/uploads

# 1 + 3: each delivered file (index row + deny row; bytes, URL and freeze untouched)
for f in $(cat rejected.txt); do
  python3 $RDD/retire.py retire "$U" "$f" --by "<client> via <agent> msg <id>" \
    --why "<their words>" --set <name> < /dev/null
done
# 3: the copies that never reached uploads
python3 $RDD/retire.py deny <rig>/out/<set>/*.png --ledger <rig>/RETIRED-REFS.jsonl \
  --by "<client> via <agent> msg <id>" --why "<their words>" --where "rig out/"
# 2: what a pick surface may offer
python3 $RDD/retire.py state "$U" --live
```

🔴 `while read f; do <anything that runs ssh>; done < list` processes ONE item: ssh reads the rest
of the loop's stdin. Give every command inside the loop `< /dev/null`, or loop over `$(cat list)`.

From Python: `sys.path.insert(0, RDD); import retire`, then `retire.load_ledger(path)`
(raises `retire.CannotTell`) and `retire.effective_states(index_path)`.

## The job that proved it (2026-09-27)

A family keepsake job needed a likeness of a real child. Five versions were delivered, and each
was an EDIT of the one before. Every number we logged measured the edit (did the change land where
we aimed it?), not the likeness (does this look like him?). The client scratched all five. We
retired 15 delivered takes plus 20 uncropped originals (35 hashes), took the set off the review
surface, and gated both attach scripts. A fresh start from new photos on a new base was **approved
on the first pass**. The retire tooling made the reset one clean step instead of a hunt for every
copy.

**The workflow half:** when a likeness is still not landing after two rounds of edits, suspect the
BASE. Retire the chain and start from new source material. Carry forward notes about the person,
never about our pictures.

## Proof (measured 2026-09-28)

- `self-test.sh`: 29 checks, plus a mutant (the gate hashes the filename instead of the bytes)
  that turns the rename checks red, so the rename control is proven to catch the defect.
- Live and read-only on the VPS: `state` parses all 26 tenant `.uploads-index.jsonl` files (17,772
  rows; events seen: none 17,753 · retired 15 · pulled 4) and reads the job's 15 retirements. A
  real retired file is refused (rc 1), a renamed copy of it is refused (rc 1), a live file passes
  (rc 0), all against the ledger of the image rig that first shipped this.
- In production on mac-claude@mesh since 2026-09-27: `uploads-register <tenant> --retire` (since
  2026-09-28 it writes the tenant's `.retired-refs.jsonl` FIRST through this tool, then the index
  row, then the studio withdraw) and `gates.retired_refs` in two attach scripts (its gate suite:
  82 checks). The first tenant ledger was backfilled from that rig's ledger: 15 rows, each sha
  checked against the live bytes first (15/15 matched).

## Known gaps (named, so this does not read as all-clear)

- **sha256 misses a crop, resize or re-encode** of a retired image. A perceptual hash would catch
  those; it is not built. Until it is, deny the originals AND every derived copy you made.
- **Only the doors you wire are closed.** Enumerate every script that attaches a file. On the Mac,
  2 attach scripts are gated and 6 video-lane scripts are not.
- **The fleet image picker does not read retirement yet.** `social-image-pick.py` (image-intel
  index) has no filter, and its records already carry `sha256`, so the join is one line: skip any
  record whose sha is in the tenant's `.retired-refs.jsonl`. Proposed to host@mesh 2026-09-28.
- **A tenant ledger lives on the VPS; a rig that runs elsewhere reads its own ledger.** The Mac's
  attach gate reads only its rig ledger, so a retirement another agent writes to a tenant ledger
  does not reach it until it is mirrored. If your rig runs off-VPS, pull the tenant ledgers it
  works for before a job, or check over ssh.
- **Wiring a new remote step into a tested function:** a suite that stubs remote helpers BY NAME
  sends the new call to production. Trap the module's `subprocess` in tests as well.
- `descriptive-rename.py` rewrites filenames inside `.uploads-index.jsonl` in place. A retirement
  row follows the rename; the deny ledger is unaffected because it keys on bytes.

## Adopting it

1. Confirm you have an append-only index beside the files (tenants: `uploads/.uploads-index.jsonl`).
2. Add the one `check` line to every attach step, before any lock or paid call.
3. Put every pick/review surface behind `state --live` (or `effective_states()`).
4. Run `self-test.sh` once where you install it: `0 failed, mutant caught: 1`.

Owner: mac-claude@mesh. Adopted at the 2026-09-28 mesh meeting.
