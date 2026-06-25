# Blog-Factory per-client config schema

One JSON file per target site, named `<site-key>.json`, lives in this dir. The
orchestrator (`blog-factory.sh`) loads it, derives the per-run `meta.json` the gates
read, and drives topic-pick → generate → verify → deploy → live-verify.

It is PARAMETERIZED so the same shared engine serves every client on any framework.

```jsonc
{
  // --- identity ---
  "site_key":    "manufacturedproductinsurance",      // unique key (matches filename)
  "brand":       "Manufactured Product Insurance",     // publisher / byline brand
  "site_author": "Contractor's Choice Agency",         // author byline
  "site_url":    "https://manufacturedproductinsurance.com",
  "location":    "United States",                       // DataForSEO location_name

  // --- where the code lives + how blogs are deployed ---
  "repo_path":   "/mnt/clients/josh/openclaw/workspace/Websites/manufacturedproductinsurance.com",
  "git_branch":  "main",
  "framework":   "next-mdx-content",   // one of:
                                       //   next-mdx-content : .mdx files in blog_dir,
                                       //                      index has a posts[] array to update
                                       //   next-slug-record : single [slug]/page.tsx record map
                                       //   markdown         : plain .md drop-in (generic)
  "blog_dir":    "content/blog",       // relative to repo_path — where the .mdx lands
  "blog_index":  "app/blog/page.tsx",  // relative — the posts[] array to update (next-mdx-content)
  "sitemap_file":"app/sitemap.ts",     // relative — optional; appended if present
  "blog_path_prefix": "/blog/",        // public URL prefix for a post

  // --- knowledge base (Tier-2 brain) ---
  "knowledge_base": "/mnt/clients/josh/openclaw/workspace/knowledge",

  // --- money pages (internal-link targets). Derived from seo-plan.json when present,
  //     else listed explicitly here. ---
  "money_pages": ["/quote", "/services", "/industries", "/contact", "/about"],

  // --- GATE THRESHOLDS (copied into each run's meta.json) ---
  "gates": {
    "min_words":            1000,
    "meta_desc_min":        120,
    "meta_desc_max":        165,
    "title_max":            65,
    "min_h2":               4,
    "require_featured_image": false,   // set true once an image pipeline is wired
    "min_outbound":         4,
    "authority_dr_min":     60,
    "authority_allowlist":  [".gov", ".edu", "iii.org", "naic.org", "irs.gov",
                             "osha.gov", "sba.gov", "consumer.ftc.gov", "cpsc.gov",
                             "iso.org", "ansi.org", "nist.gov", "ftc.gov"],
    "min_money_links":      1,
    "min_blog_links":       1,
    "min_internal_total":   2
  },

  // --- scheduling ---
  "cadence_cron": "0 13 * * 1",        // weekly Mon 13:00 UTC (documented, NOT auto-enabled)

  // --- generation model (bulk body → cheap, cap-proof) ---
  "gen_model": "glm"                   // "glm" (claude-zai.sh) | "haiku"
}
```

## Framework field — how deploy differs

| framework | drop file | index update | notes |
|---|---|---|---|
| `next-mdx-content` | `<blog_dir>/<slug>.mdx` with frontmatter | prepend entry to `posts[]` in `blog_index` | the proof target. Renderer reads dir via `generateStaticParams`. |
| `next-slug-record` | add record to `blogPosts` map in `[slug]/page.tsx` | same file | content stored as a template-string field. |
| `markdown` | `<blog_dir>/<slug>.md` | none (framework auto-lists) | generic SSG (Astro/Hugo/Eleventy). |

The gates themselves are framework-agnostic — they read the staged `article.mdx`
+ `meta.json` + `schema.json`, never the destination framework. Only `deploy.sh`
branches on `framework`.
