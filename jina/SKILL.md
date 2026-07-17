---
name: jina
description: "Jina AI — the content/semantic layer that pairs with DataForSEO. Reader (URL→clean LLM-ready markdown, JS-rendered), Search (SERP+content in one call), Embeddings, Reranker, free Segmenter, and Grounding fact-check. Use when you need the ACTUAL CONTENT of a web page for an LLM, competitor content-gap analysis, semantic retrieval over research, or fact-checking a claim. DataForSEO = who ranks/metrics; Jina = what the page says."
metadata:
  version: 0.1.0-plan
  status: "REFERENCE ONLY — proxy not wired yet (see docs/jambot/jina-integration-plan.md). Do NOT call api.jina.ai directly from a container."
  openclaw:
    emoji: "📄"
---

# Jina AI — Content & Semantic Layer

Jina turns web pages into clean, LLM-ready content and lets you reason over it (embed, rerank, chunk, fact-check). It is the **complement** to DataForSEO, not an overlap:

- **DataForSEO** → metrics *about* pages: who ranks, search volume, backlinks, technical scores, AI-mode SERP.
- **Jina** → the *content* of pages, rendered to markdown, plus embeddings/rerank/chunk to work with it.

The killer combo: **DataForSEO gives you the ranking URLs → Jina Reader gives you what those pages actually wrote → real content-gap analysis.**

> ⚠️ **STATUS (2026-07-13): PLAN ONLY.** The key-safe cost-tracked proxy on `:6350` is designed but **not built yet** — see `docs/jambot/jina-integration-plan.md`. Until it ships, treat this as reference. **Never put `JINA_API_KEY` in a container or call `api.jina.ai` directly from an agent** (breaks the proxy-only key rule + cost tracking).

## Authentication (once the proxy is live)

Same pattern as DataForSEO: **you never hold the key.** All calls route through the social-dashboard proxy on `:6350`, which holds `JINA_API_KEY` (in `.platform-keys.env`) and meters spend per tenant.

```bash
# helper resolves your tenant from the container hostname automatically
bash /mnt/system/base/skills/jina/scripts/jina.sh <product> '<json_body>'
```

One key = all products, one shared token wallet. New keys start with **10,000,000 free tokens**.

## The products

### Reader — URL → clean markdown  (the workhorse)
Renders any URL with a headless browser (executes JS, extracts PDFs, captions images), strips nav/ads/scripts, returns markdown an LLM can read.
```bash
bash jina.sh reader '{"url":"https://competitor.com/services"}'
# optional: {"target_selector":"main","remove":"nav,footer","wait_for":".content"}
```
- **Single URL only** — no whole-site crawl. Enumerate URLs (sitemap / DataForSEO SERP / Search) then Reader each.
- Cost ~$0.02/1M output tokens. ReaderLM HTML→MD mode costs 3×.
- **Use for:** competitor page content, reference articles for `article-writer`, JS-rendered client sites the seo-review crawler can't see, `llms.txt` source content.

### Search — SERP + fetched content in one call
```bash
bash jina.sh search '{"q":"best spray foam contractor phoenix"}'
```
- Returns top ~5 results with URL + cleaned content each. Fixed **10K tokens/call** (~$0.0005).
- **Use for:** ad-hoc "what does the web say, with content" grounding. **NOT** a rank/volume source — DataForSEO + Serper own ranking data.

### Embeddings — vectors for the knowledge brain
```bash
bash jina.sh embeddings '{"input":["chunk one","chunk two"],"model":"jina-embeddings-v3","dimensions":1024}'
```
- Models: `jina-embeddings-v3` (89 langs, 8K ctx, Matryoshka dims), `-v4` (multimodal, 32K), `-v5-*`. ~$0.045/1M.
- **Use for:** semantic retrieval over the per-client research brain (embed once, reuse — never re-pay for research).

### Reranker — precision layer for RAG
```bash
bash jina.sh rerank '{"query":"spray foam R-value","documents":["...","..."],"top_n":5,"model":"jina-reranker-v3"}'
```
- Reorders candidates by true relevance (deeper than cosine). ~$0.045/1M.
- **Use for:** sharpening top-k before the drafting LLM sees retrieved research.

### Segmenter — chunking + token counting  (**FREE**)
```bash
bash jina.sh segment '{"content":"<long text>","max_chunk_length":1000,"return_chunks":true}'
```
- Semantic chunks + token IDs, 100+ languages, up to 64K chars/request. **Zero tokens deducted.**
- **Use for:** chunking before embedding; free token-counting to decide what's worth embedding.

### Grounding — fact-check a claim  (heavy, gated)
```bash
bash jina.sh grounding '{"statement":"Closed-cell spray foam has an R-value of about 6.5 per inch."}'
```
- Returns factuality score 0–1 + 10–30 cited sources. **~300K tokens/call (~30s)** — only ~30 calls on the free wallet.
- **Use for:** final-draft editorial QA in `article-writer`, metered hard. Only works on verifiable factual claims (not opinion/future/hypothetical).

### Skip these
- **DeepSearch** — overlaps our `deep-research` skill; don't use.
- **Classifier** — hold unless we need zero-shot content/intent tagging at volume.

## How Jina fits the SEO workflow

1. **SEO audit (seo-review):** when the deterministic crawler gets a thin JS-rendered page, Reader fills in the real content so findings aren't false.
2. **Article research (article-writer):** DataForSEO SERP → top URLs → Reader → clean competitor content → genuine content-gap outline. Segmenter+Embeddings store it in the client brain for reuse.
3. **AEO / llms.txt:** Reader pulls clean site content for `llms-txt-writer`.
4. **Editorial QA:** Grounding fact-checks claims with citations before publish.

## Cost discipline
- Meter everything through the proxy — `jina_queries` table + `provider-calls/jina-*.jsonl` receipts (mirrors DataForSEO's "who spent it?" answerability).
- Cheap: Reader, Search, Segmenter (free). **Expensive: Grounding, DeepSearch** — gate/avoid.
- 10M free tokens ≈ 5,000 Reader pages or 1,000 searches. Watch the roll to paid.

## Full spec
`docs/jambot/jina-integration-plan.md` — architecture, backend routes, phased build, verification steps.
