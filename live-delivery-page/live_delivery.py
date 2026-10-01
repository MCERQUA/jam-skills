#!/usr/bin/env python3
"""live_delivery.py: the WRITER for a live-delivery page (fleet skill `live-delivery-page`).

One URL per in-progress job. The slots are seeded from the plan BEFORE the first artifact
exists, and each slot is flipped the moment its artifact is delivered. The page re-reads the
manifest every 30 s, so an empty slot reads as a missing beat, not as "no progress".

    # where: pick ONE (inside a tenant container nothing is needed, it finds /app/runtime/)
    --tenant <slug>                 VPS host paths /mnt/clients/<slug>/openvoiceui/{uploads,canvas-pages}
    --uploads DIR [--pages DIR]     any served uploads dir (+ the dir its pages are served from)
    --ssh HOST                      do the same thing on another machine over ssh (rigs off the VPS)

    live_delivery.py --job <slug> <where> --seed <shots.json|beats.json|N> [--title ..] [--ask ..]
    live_delivery.py --job <slug> <where> --publish-page
    live_delivery.py --job <slug> <where> --set N --status rendering
    live_delivery.py --job <slug> <where> --set N --status ready --file <name> [--measure k=v] [--note ..]
    live_delivery.py --job <slug> <where> --set N --status failed --note "why"
    live_delivery.py --job <slug> <where> --set N --file <other-take> --alt [--note ..]
    live_delivery.py --job <slug> <where> --header --finding "the one line worth reading first"
    live_delivery.py --job <slug> <where> --show [--json]
    live_delivery.py --job <slug> <where> --check        # is every declared file still at its URL?

    exit 0  written / shown / every declared file present
    exit 1  REFUSED: a rule fired and is NAMED on stderr (nothing was written). Usage errors too.
    exit 2  CANNOT-TELL: a read or write could not be completed. Nothing was changed, and this is
            never a verdict on the contents.

Contract, page obligations and failure modes: SKILL.md beside this file. Stdlib only.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

VERSION = "live-delivery-page/1 2026-09-30"
SCHEMA = "live-delivery/1"
TEMPLATE_MARK = "live-delivery-page/1"          # the published page carries this; foreign pages do not

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "page.html")

CONTAINER_UPLOADS = "/app/runtime/uploads"
CONTAINER_PAGES = "/app/runtime/canvas-pages"
HOST_ROOT = "/mnt/clients/%s/openvoiceui"
TENANT_URL = "https://%s.jam-bot.com"

# CLOSED on purpose. A status the page has no rendering for would fall through to an empty gap,
# which is the one thing a pending slot must never be.
STATUSES = ("queued", "rendering", "ready", "failed", "skipped")

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,200}$")   # a bare name in uploads, never a path


class CannotTell(Exception):
    """A read/write that did not complete. Distinct from 'absent' and from 'refused'."""


class Refused(Exception):
    def __init__(self, rule, msg):
        Exception.__init__(self, msg)
        self.rule = rule


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── storage: one interface, two transports ───────────────────────────────────────────────────
class Local(object):
    def read(self, path):
        """Text, or None when the file is absent. Anything else is CANNOT-TELL."""
        try:
            with open(path) as fh:
                return fh.read()
        except FileNotFoundError:
            return None
        except (OSError, UnicodeDecodeError) as ex:
            raise CannotTell("could not read %s: %s" % (path, ex))

    def exists(self, path):
        try:
            os.stat(path)
            return True
        except FileNotFoundError:
            return False
        except OSError as ex:
            raise CannotTell("could not stat %s: %s" % (path, ex))

    def isdir(self, path):
        return os.path.isdir(path)

    def write(self, path, text):
        """Same-directory temp file, then os.replace (rename(2)): a reader never sees a
        half-written manifest, and a failed write leaves the previous version live."""
        d = os.path.dirname(path) or "."
        try:
            fd, tmp = tempfile.mkstemp(prefix=".ld-", suffix=".tmp", dir=d)
        except OSError as ex:
            raise CannotTell("could not write in %s: %s" % (d, ex))
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
            os.chmod(tmp, 0o644)
            os.replace(tmp, path)
        except OSError as ex:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise CannotTell("could not write %s: %s" % (path, ex))


class Remote(object):
    """The same four operations over ssh. Every remote command prints a token as its last act:
    ssh swallowing an error and an empty answer look identical, so no token = CANNOT-TELL."""

    def __init__(self, host, key=None):
        self.host, self.key = host, key

    def _run(self, cmd, stdin=None):
        argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
        if self.key:
            argv += ["-i", os.path.expanduser(self.key)]
        argv += [self.host, cmd]
        try:
            p = subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as ex:
            raise CannotTell("ssh %s: %s" % (self.host, ex))
        return p.returncode, p.stdout, p.stderr.strip()

    def read(self, path):
        q = shlex.quote(path)
        rc, out, err = self._run("if [ -e %s ]; then echo LD-PRESENT; cat -- %s; "
                                 "else echo LD-ABSENT; fi" % (q, q))
        head, _, body = out.partition("\n")
        if rc != 0 or head not in ("LD-PRESENT", "LD-ABSENT"):
            raise CannotTell("ssh %s could not read %s (rc %d%s)"
                             % (self.host, path, rc, (": " + err) if err else ""))
        return body if head == "LD-PRESENT" else None

    def exists(self, path):
        rc, out, err = self._run("if [ -e %s ]; then echo LD-YES; else echo LD-NO; fi"
                                 % shlex.quote(path))
        if rc != 0 or out.strip() not in ("LD-YES", "LD-NO"):
            raise CannotTell("ssh %s could not check %s (rc %d%s)"
                             % (self.host, path, rc, (": " + err) if err else ""))
        return out.strip() == "LD-YES"

    def isdir(self, path):
        rc, out, _ = self._run("if [ -d %s ]; then echo LD-YES; else echo LD-NO; fi"
                               % shlex.quote(path))
        if rc != 0 or out.strip() not in ("LD-YES", "LD-NO"):
            raise CannotTell("ssh %s could not check %s (rc %d)" % (self.host, path, rc))
        return out.strip() == "LD-YES"

    def write(self, path, text):
        q, t = shlex.quote(path), shlex.quote(path + ".ld-tmp")
        rc, out, err = self._run("cat > %s && chmod 644 %s && mv -f %s %s && echo LD-WROTE "
                                 "|| { rm -f %s; exit 3; }" % (t, t, t, q, t), stdin=text)
        if rc != 0 or out.strip() != "LD-WROTE":
            raise CannotTell("ssh %s could not write %s (rc %d%s); the previous version is "
                             "still live" % (self.host, path, rc, (": " + err) if err else ""))


# ── where the job lives ───────────────────────────────────────────────────────────────────────
class Target(object):
    def __init__(self, fs, uploads, pages, base_url, where):
        self.fs, self.uploads, self.pages, self.base_url, self.where = \
            fs, uploads, pages, base_url.rstrip("/"), where

    def manifest(self, job):
        return "%s/%s.json" % (self.uploads, job)

    def page(self, job):
        return "%s/%s.html" % (self.pages, job) if self.pages else None

    def url(self, rel):
        return (self.base_url + rel) if self.base_url else rel


def resolve(a):
    fs = Remote(a.ssh, a.ssh_key) if a.ssh else Local()
    tenant_url = (TENANT_URL % a.tenant) if a.tenant else ""
    if a.uploads:
        uploads, pages, where = a.uploads.rstrip("/"), (a.pages or "").rstrip("/") or None, "--uploads"
    elif a.tenant:
        root = HOST_ROOT % a.tenant
        uploads, pages, where = root + "/uploads", root + "/canvas-pages", "tenant %s" % a.tenant
    elif not a.ssh and os.path.isdir(CONTAINER_UPLOADS):
        uploads, pages, where = CONTAINER_UPLOADS, CONTAINER_PAGES, "this container"
    else:
        raise Refused("no-target", "say where the job lives: --tenant <slug> (VPS host paths), "
                      "--uploads DIR [--pages DIR], or run inside a tenant container")
    if not fs.isdir(uploads):
        raise Refused("no-uploads-dir", "%s is not a directory (%s)%s" % (
            uploads, where, "" if not a.ssh else " on " + a.ssh))
    return Target(fs, uploads, pages, a.base_url or tenant_url, where)


# ── schema ────────────────────────────────────────────────────────────────────────────────────
def blank_slot(n):
    return {"n": n, "beat": None, "label": "Slot %d" % n, "shows": "", "status": "queued",
            "file": None, "url": None, "measurements": {}, "notes": "",
            "alternates": [], "superseded": []}


def normalise(obj):
    """Fill the defaults a slot needs. Keeps every key it does not know: a manifest written by
    another writer of this schema comes through with nothing dropped."""
    obj.setdefault("schema", SCHEMA)
    for c in obj.get("clips") or []:
        if not isinstance(c, dict):
            continue
        c.setdefault("beat", None)
        for k, kind in (("shows", str), ("notes", str), ("measurements", dict),
                        ("alternates", list), ("superseded", list)):
            if not isinstance(c.get(k), kind):
                c[k] = kind()
    return obj


def decorate(obj):
    """The writer composes every browser URL from the bare filename. The page never builds a
    path itself, so the two cannot disagree about where a file is."""
    for c in obj.get("clips") or []:
        c["url"] = ("/uploads/%s" % c["file"]) if c.get("file") else None
        for alt in c.get("alternates") or []:
            alt["url"] = ("/uploads/%s" % alt["file"]) if alt.get("file") else None
    return obj


def validate(obj):
    """Refuse a manifest the page could not render HONESTLY. Returns the reason or None."""
    if not isinstance(obj, dict) or not isinstance(obj.get("clips"), list):
        return "the manifest has no clips[] list"
    if not obj["clips"]:
        return ("the manifest has zero slots; the page would show an empty list, and an empty "
                "list must only ever mean 'could not read it'")
    seen = set()
    for c in obj["clips"]:
        if not isinstance(c, dict) or not isinstance(c.get("n"), int):
            return "a slot has no integer n"
        n = c["n"]
        if n in seen:
            return "slot %d appears twice" % n
        seen.add(n)
        if c.get("status") not in STATUSES:
            return "slot %d has status %r, not one of %s" % (n, c.get("status"), list(STATUSES))
        if c.get("status") == "ready" and not c.get("file"):
            return ("slot %d is 'ready' with no file; the page would draw a player with no source, "
                    "which reads as a BROKEN artifact, not a pending one" % n)
        for alt in c.get("alternates") or []:
            if not isinstance(alt, dict) or not alt.get("file"):
                return "slot %d has an alternate with no file" % n
    if sorted(seen) != list(range(1, len(seen) + 1)):
        return ("slot numbers are %s; they must run 1..%d with no gaps, because the viewer "
                "answers with a number" % (sorted(seen), len(seen)))
    return None


def load(t, job):
    """(manifest, None) · (None, 'absent') · Refused if the file is not a live-delivery manifest."""
    text = t.fs.read(t.manifest(job))
    if text is None:
        return None, "absent"
    try:
        obj = json.loads(text)
    except ValueError as ex:
        raise Refused("not-a-manifest", "%s exists and is not valid JSON (%s). It is left "
                      "exactly as it is; pick another --job." % (t.manifest(job), ex))
    if not isinstance(obj, dict) or not str(obj.get("schema", "")).startswith("live-delivery/"):
        raise Refused("not-a-manifest", "%s exists and is not a live-delivery manifest. It is "
                      "left exactly as it is; pick another --job." % t.manifest(job))
    return normalise(obj), None


def save(t, job, obj):
    obj["updated"] = now_iso()
    obj["written_by"] = VERSION
    decorate(obj)
    err = validate(obj)
    if err:
        raise Refused("schema", "the change would make the manifest invalid: %s" % err)
    t.fs.write(t.manifest(job), json.dumps(obj, indent=2) + "\n")


# ── seeding ───────────────────────────────────────────────────────────────────────────────────
def slots_from_seed(spec):
    """A count, a JSON list, or {shots|beats|clips|slots: [...]}. Per row, the first key present
    in each group, so a shot list written for another tool seeds with no reshaping."""
    if re.fullmatch(r"\d+", str(spec)):
        n = int(spec)
        if n < 1:
            raise Refused("bad-seed", "--seed %s asks for no slots" % spec)
        return [blank_slot(i) for i in range(1, n + 1)]
    path = os.path.expanduser(str(spec))
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        raise Refused("bad-seed", "%s is neither a number nor a file that exists" % spec)
    except (OSError, ValueError) as ex:
        raise Refused("bad-seed", "%s could not be read as JSON: %s" % (path, ex))
    rows = doc if isinstance(doc, list) else None
    if isinstance(doc, dict):
        for key in ("shots", "beats", "clips", "slots"):
            if isinstance(doc.get(key), list):
                rows = doc[key]
                break
    if not rows:
        raise Refused("bad-seed", "%s has no shots[]/beats[]/clips[]/slots[] list" % path)

    def pick(d, *keys):
        for k in keys:
            if d.get(k) not in (None, ""):
                return d[k]
        return None

    slots = []
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            s = blank_slot(i)
            s["label"] = str(r)
            slots.append(s)
            continue
        try:
            n = int(pick(r, "n", "index", "number") or i)
        except (TypeError, ValueError):
            n = i
        s = blank_slot(n)
        beat = pick(r, "beat", "beat_id", "id", "slug", "shot_id")
        s["beat"] = str(beat) if beat is not None else None
        s["label"] = str(pick(r, "label", "name", "title", "headline", "beat", "id") or s["label"])
        s["shows"] = str(pick(r, "shows", "purpose", "description", "desc", "summary", "intent",
                              "line", "action") or "")
        s["notes"] = str(pick(r, "notes", "note") or "")
        slots.append(s)
    # Contiguous from 1, in plan order: the viewer replies with a NUMBER, so a gap in the
    # numbering is a gap in the only affordance the page has.
    slots.sort(key=lambda s: s["n"])
    for i, s in enumerate(slots, start=1):
        s["n"] = i
    return slots


# ── commands ──────────────────────────────────────────────────────────────────────────────────
def cmd_seed(a, t):
    cur, _ = load(t, a.job)                       # raises not-a-manifest for someone else's file
    if cur is not None and not a.force:
        raise Refused("manifest-exists", "%s already exists (%d slots). Patch one slot with --set, "
                      "or --force to re-seed and FORGET every status and file it records."
                      % (t.manifest(a.job), len(cur.get("clips") or [])))
    slots = slots_from_seed(a.seed)
    obj = {"schema": SCHEMA, "job": a.job, "tenant": a.tenant or "", "updated": "",
           "title": a.title or a.job.replace("-", " ").capitalize(), "client": a.client or "",
           "note": a.note or "", "finding": a.finding or "", "ask": a.ask or "",
           "written_by": VERSION, "page": t.url("/pages/%s.html" % a.job), "clips": slots}
    save(t, a.job, obj)
    print("seeded %s: %d slots, all placeholders" % (t.manifest(a.job), len(slots)))
    print("manifest: %s" % t.url("/uploads/%s.json" % a.job))
    print("page:     %s   (publish it with --publish-page)" % t.url("/pages/%s.html" % a.job))
    return 0


def cmd_publish_page(a, t):
    if not t.pages:
        raise Refused("no-pages-dir", "--publish-page needs --pages DIR (the dir served as /pages/)")
    if not t.fs.isdir(t.pages):
        raise Refused("no-pages-dir", "%s is not a directory" % t.pages)
    cur, why = load(t, a.job)
    if cur is None:
        raise Refused("no-manifest", "%s does not exist. Seed first: a page with no manifest "
                      "tells its viewer the list cannot be read." % t.manifest(a.job))
    try:
        with open(TEMPLATE) as fh:
            html = fh.read()
    except OSError as ex:
        raise Refused("no-template", "the page template is missing at %s: %s" % (TEMPLATE, ex))
    if TEMPLATE_MARK not in html:
        raise Refused("no-template", "%s does not carry %s" % (TEMPLATE, TEMPLATE_MARK))
    existing = t.fs.read(t.page(a.job))
    if existing is not None and TEMPLATE_MARK not in existing and not a.force:
        raise Refused("page-exists", "%s exists and is not a live-delivery page. It is left as it "
                      "is; pick another --job, or --force to replace it." % t.page(a.job))
    t.fs.write(t.page(a.job), html)
    print("published %s" % t.page(a.job))
    print("page: %s" % t.url("/pages/%s.html" % a.job))
    print("NOTE: canvas pages are login-gated by default, and a gated page answers a bare "
          "'Unauthorized' with no sign-in redirect. When you send this link to a person, send ONE "
          "direct /uploads/ file URL with it (that opens with no login), and say 'sign in at the "
          "site first if the page says Unauthorized'.")
    return 0


def _parse_value(v):
    v = v.strip()
    try:
        return float(v) if re.fullmatch(r"-?\d+\.\d*|-?\.\d+", v) else int(v)
    except ValueError:
        return v


def cmd_set(a, t):
    obj, why = load(t, a.job)
    if obj is None:
        raise Refused("no-manifest", "%s does not exist yet; run --seed first" % t.manifest(a.job))
    slot = next((c for c in obj["clips"] if isinstance(c, dict) and c.get("n") == a.set), None)
    if slot is None:
        raise Refused("unknown-slot", "there is no slot %d; this manifest has %s"
                      % (a.set, sorted(c.get("n") for c in obj["clips"] if isinstance(c, dict))))
    if a.status is not None and a.status not in STATUSES:
        raise Refused("unknown-status", "%r is not one of %s" % (a.status, list(STATUSES)))
    if a.alt and not a.file:
        raise Refused("alt-without-file", "--alt adds a delivered take; pass --file")
    if a.alt and a.status:
        raise Refused("alt-with-status", "--alt never changes the slot's status; drop --status")
    if a.status == "ready" and not (a.file or slot.get("file")):
        raise Refused("ready-without-file", "slot %d cannot be 'ready' with no --file: the page "
                      "would draw a player with no source, which reads as a BROKEN artifact."
                      % a.set)
    measures = {}
    for kv in a.measure or []:
        if "=" not in kv or not kv.split("=", 1)[0].strip():
            raise Refused("bad-measure", "--measure wants key=value, got %r" % kv)
        k, v = kv.split("=", 1)
        measures[k.strip()] = _parse_value(v)
    if a.file:
        if not FILE_RE.match(a.file) or ".." in a.file:
            raise Refused("bad-file", "--file must be a bare filename in the uploads dir, got %r"
                          % a.file)
        delivered = t.fs.exists("%s/%s" % (t.uploads, a.file))
        if not delivered:
            raise Refused("file-not-delivered", "%s is not in %s. Deliver the file FIRST, then "
                          "flip the slot; otherwise the page links a 404 and the viewer sees a "
                          "broken artifact." % (a.file, t.uploads))
        if a.alt:
            alts = slot.setdefault("alternates", [])
            alt = next((x for x in alts if x.get("file") == a.file), None)
            if alt is None:
                alt = {"file": a.file, "note": "", "added": now_iso()}
                alts.append(alt)
            if a.note is not None:
                alt["note"] = a.note
            if measures:
                alt.setdefault("measurements", {}).update(measures)
        else:
            # A displaced primary stays DECLARED. Its file is not deleted (a link already sent
            # must keep working), so without this row a file sits in uploads that no manifest
            # names, and any checker that counts at the destination reads it as unexplained.
            old = slot.get("file")
            if old and old != a.file:
                sup = slot.setdefault("superseded", [])
                if not any(x.get("file") == old for x in sup):
                    sup.append({"file": old, "displaced_by": a.file, "displaced": now_iso()})
            slot["file"] = a.file
    if not a.alt:
        if a.status:
            slot["status"] = a.status
        for attr, key in (("label", "label"), ("beat", "beat"), ("shows", "shows"),
                          ("note", "notes")):
            v = getattr(a, attr)
            if v is not None:
                slot[key] = v
        slot.setdefault("measurements", {}).update(measures)
    save(t, a.job, obj)
    print("slot %d -> %s%s  (manifest updated %s)" % (
        a.set, slot["status"], (" · " + slot["file"]) if slot.get("file") else "", obj["updated"]))
    if a.alt:
        print("alternate %s added beside the primary" % a.file)
    print("the page shows this within 30 s; there is nothing else to publish.")
    return 0


def cmd_header(a, t):
    obj, why = load(t, a.job)
    if obj is None:
        raise Refused("no-manifest", "%s does not exist yet; run --seed first" % t.manifest(a.job))
    changed = False
    for attr in ("title", "note", "finding", "client", "ask"):
        v = getattr(a, attr)
        if v is not None:
            obj[attr] = v
            changed = True
    if not changed:
        raise Refused("empty-header", "--header changes nothing; pass --title/--note/--finding/"
                      "--client/--ask")
    save(t, a.job, obj)
    print("header updated (%s)" % obj["updated"])
    return 0


def cmd_show(a, t):
    obj, why = load(t, a.job)
    if obj is None:
        raise Refused("no-manifest", "%s does not exist" % t.manifest(a.job))
    if a.as_json:
        print(json.dumps(obj, indent=2))
        return 0
    print("%s  (updated %s)" % (obj.get("title"), obj.get("updated")))
    print("page: %s" % obj.get("page"))
    for c in obj["clips"]:
        m = c.get("measurements") or {}
        ms = " ".join("%s=%s" % (k, v) for k, v in sorted(m.items())) or "-"
        print("  %2d. %-34s %-10s %-24s %s" % (c.get("n"), (c.get("label") or "")[:34],
                                               c.get("status"), ms[:24], c.get("file") or ""))
    pend = [str(c["n"]) for c in obj["clips"] if c.get("status") in ("queued", "rendering")]
    if pend:
        print("still pending: %s" % ", ".join(pend))
    return 0


def cmd_check(a, t):
    """Every file the manifest says is live must still be at its URL. A file renamed or moved
    after it was flipped turns into a broken player on the page, and nothing else notices."""
    obj, why = load(t, a.job)
    if obj is None:
        raise Refused("no-manifest", "%s does not exist" % t.manifest(a.job))
    missing, n = [], 0
    for c in obj["clips"]:
        names = ([c["file"]] if c.get("status") == "ready" and c.get("file") else []) + \
                [x.get("file") for x in (c.get("alternates") or []) if x.get("file")]
        for f in names:
            n += 1
            if not t.fs.exists("%s/%s" % (t.uploads, f)):
                missing.append("slot %d: %s" % (c["n"], f))
    pend = [str(c["n"]) for c in obj["clips"] if c.get("status") in ("queued", "rendering")]
    if missing:
        for m in missing:
            print("MISSING %s" % m)
        print("%d of %d declared file(s) are not at their URL in %s" % (len(missing), n, t.uploads))
        return 1
    print("OK: %d declared file(s) present in %s%s" % (
        n, t.uploads, ("; still pending: " + ", ".join(pend)) if pend else ""))
    return 0


class _Parser(argparse.ArgumentParser):
    def error(self, message):              # a usage error is a refusal (1), never CANNOT-TELL (2)
        self.print_usage(sys.stderr)
        sys.stderr.write("REFUSED (usage): %s\n" % message)
        sys.exit(1)


def main(argv):
    ap = _Parser(description="Write the manifest a live-delivery page polls: one URL, slots "
                             "seeded before anything exists, one call per artifact as it lands.")
    ap.add_argument("--job", required=True, help="slug: manifest <job>.json, page <job>.html")
    ap.add_argument("--tenant", help="tenant slug: VPS host paths + https://<slug>.jam-bot.com")
    ap.add_argument("--uploads", help="the served uploads dir (its files answer at /uploads/<name>)")
    ap.add_argument("--pages", help="the dir served as /pages/ (needed only for --publish-page)")
    ap.add_argument("--base-url", dest="base_url", help="printed URLs start with this")
    ap.add_argument("--ssh", help="run the reads/writes on this host over ssh")
    ap.add_argument("--ssh-key", dest="ssh_key", help="identity file for --ssh")
    ap.add_argument("--seed", metavar="SPEC", help="shots.json | beats.json | N: create ALL slots")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--set", type=int, metavar="N", help="the slot to change")
    ap.add_argument("--status", help="|".join(STATUSES))
    ap.add_argument("--file", help="the delivered filename in the uploads dir")
    ap.add_argument("--alt", action="store_true", help="add --file as an alternate take")
    ap.add_argument("--measure", action="append", metavar="K=V")
    ap.add_argument("--note")
    ap.add_argument("--label")
    ap.add_argument("--beat")
    ap.add_argument("--shows", help="what the slot is FOR; shown on its placeholder")
    ap.add_argument("--header", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--finding")
    ap.add_argument("--client")
    ap.add_argument("--ask", help="one line telling the viewer how to answer")
    ap.add_argument("--publish-page", dest="publish_page", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args(argv[1:])

    try:
        if not SLUG_RE.match(a.job):
            raise Refused("bad-job", "--job must be a lowercase slug (a-z 0-9 -), got %r" % a.job)
        if a.tenant and not SLUG_RE.match(a.tenant):
            raise Refused("bad-tenant", "--tenant must be a lowercase slug, got %r" % a.tenant)
        modes = [m for m in ("seed", "publish_page", "header", "show", "check") if getattr(a, m)]
        modes += ["set"] if a.set is not None else []
        if len(modes) != 1:
            raise Refused("usage", "pick exactly one of --seed --publish-page --set --header "
                          "--show --check (got %s)" % (modes or "none"))
        if a.set is not None and not any((a.status, a.file, a.measure, a.note is not None,
                                          a.label is not None, a.beat is not None,
                                          a.shows is not None)):
            raise Refused("empty-set", "--set %d changes nothing" % a.set)
        t = resolve(a)
        return {"seed": cmd_seed, "publish_page": cmd_publish_page, "header": cmd_header,
                "show": cmd_show, "check": cmd_check, "set": cmd_set}[modes[0]](a, t)
    except Refused as r:
        sys.stderr.write("REFUSED (%s): %s\n" % (r.rule, r))
        return 1
    except CannotTell as ex:
        sys.stderr.write("CANNOT-TELL: %s\n(nothing was changed)\n" % ex)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
