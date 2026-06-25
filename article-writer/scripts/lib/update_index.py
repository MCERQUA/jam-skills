#!/usr/bin/env python3
"""
update_index.py — insert a new blog post entry into a Next.js blog index file.

Supports the two Next.js patterns the JamBot sites use:

  next-mdx-content : a `const posts = [ {...}, ... ]` array in app/blog/page.tsx.
                     We PREPEND a new object literal (newest first). Idempotent:
                     if a post with the same slug already exists, do nothing.

  next-slug-record : a `const blogPosts: Record<...> = { "<slug>": {...} }` map in
                     [slug]/page.tsx. We insert a "<slug>": {...} entry with the body
                     read from --record-from (the staged article body). Idempotent.

Usage:
  update_index.py <index_file> --slug S --title T --description D --date DATE
                  [--category C] [--read-time "8 min read"]
                  [--record-from <article.mdx>]   # for next-slug-record

Exit 0 on success (or no-op), 1 on failure. NO LLM — text manipulation.
"""
import argparse
import os
import re
import sys


def js_str(s):
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def insert_posts_array(src, args):
    if f'"{args.slug}"' in src or f"'{args.slug}'" in src:
        return src, "noop (slug already present)"
    m = re.search(r"const\s+posts\s*=\s*\[", src)
    if not m:
        return src, "ERROR: no `const posts = [` array found"
    insert_at = m.end()
    # Emit a SUPERSET of fields so the entry fits any index shape we see: some sites
    # read post.description, others post.excerpt/post.image. Untyped arrays +
    # ignoreBuildErrors make extra fields harmless.
    entry = (
        "\n  {\n"
        f"    slug: {js_str(args.slug)},\n"
        f"    title: {js_str(args.title)},\n"
        f"    description: {js_str(args.description)},\n"
        f"    excerpt: {js_str(args.description)},\n"
        f"    date: {js_str(args.date)},\n"
        f"    readTime: {js_str(args.read_time)},\n"
        f"    category: {js_str(args.category)},\n"
        f"    image: {js_str(args.image)},\n"
        "  },"
    )
    new = src[:insert_at] + entry + src[insert_at:]
    return new, "prepended to posts[]"


def insert_slug_record(src, args):
    if f'"{args.slug}"' in src:
        return src, "noop (slug already present)"
    m = re.search(r"const\s+blogPosts\s*:[^=]*=\s*\{", src)
    if not m:
        return src, "ERROR: no `const blogPosts: ... = {` map found"
    body = ""
    if args.record_from and os.path.isfile(args.record_from):
        raw = open(args.record_from, encoding="utf-8").read()
        # strip frontmatter
        fm = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", raw, re.DOTALL)
        body = fm.group(1).strip() if fm else raw.strip()
    # escape for a JS template literal
    body_tl = body.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    insert_at = m.end()
    entry = (
        f"\n  {js_str(args.slug)}: {{\n"
        f"    title: {js_str(args.title)},\n"
        f"    date: {js_str(args.date)},\n"
        f"    category: {js_str(args.category)},\n"
        "    content: `\n" + body_tl + "\n`.trim(),\n"
        "  },"
    )
    new = src[:insert_at] + entry + src[insert_at:]
    return new, "inserted slug record"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index_file")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--category", default="Insurance Guide")
    ap.add_argument("--read-time", dest="read_time", default="8 min read")
    ap.add_argument("--image", default="")
    ap.add_argument("--record-from", dest="record_from", default="")
    args = ap.parse_args()

    if not os.path.isfile(args.index_file):
        print(f"update_index: file not found: {args.index_file}", file=sys.stderr)
        sys.exit(1)
    src = open(args.index_file, encoding="utf-8").read()

    if args.record_from:
        new, msg = insert_slug_record(src, args)
    else:
        new, msg = insert_posts_array(src, args)

    if msg.startswith("ERROR"):
        print(f"update_index: {msg}", file=sys.stderr)
        sys.exit(1)
    if new != src:
        open(args.index_file, "w", encoding="utf-8").write(new)
    print(f"update_index: {msg}")
    sys.exit(0)


if __name__ == "__main__":
    main()
