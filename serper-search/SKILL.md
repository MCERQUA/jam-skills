---
name: serper-search
description: Google Search API via Serper.dev — use as SECONDARY search tool when web_search (Brave) hits limits or when you need Google-specific data (PAA, knowledge graph, local pack, maps).
metadata: {"openclaw": {"requires": {"env": ["SERPER_API_KEY"], "anyBins": ["curl"]}}}
---

# Serper Search Skill

Google Search API via Serper.dev. Returns real Google SERP data including organic results, People Also Ask, knowledge graph, local pack, maps, images, news, and more.

## When to Use

**Serper is your SECONDARY search provider.** Use the built-in `web_search` tool (Brave) first. Use Serper when:
- `web_search` hits rate limits or returns errors
- You need Google-specific SERP features (People Also Ask, Knowledge Graph, Featured Snippets)
- You need local business data (Places/Maps search with ratings, reviews, phone numbers)
- You need Google Scholar, Shopping, or Video results
- You're doing SEO analysis that requires actual Google rankings

**Budget rules:**
- ~2,500 free searches total (one-time, not monthly) — be mindful
- Max 5 Serper calls per task unless doing dedicated SEO/research work
- Always check if `web_search` or `web_fetch` can answer the question first
- Combine queries — "spray foam insulation cost Phoenix AZ" beats 3 separate searches

Valid use cases:
- Search Google for current information
- Research competitors or keywords
- Find local businesses (Maps/Places)
- Get news articles on a topic
- Analyze SERP features (People Also Ask, Featured Snippets)
- Find images, videos, or shopping results
- Check search rankings or visibility

## API Configuration

**Base URL:** `https://google.serper.dev`

**Authentication:** API key in header
```bash
-H "X-API-KEY: $SERPER_API_KEY"
-H "Content-Type: application/json"
```

**API Key:** Set `SERPER_API_KEY` environment variable

## Available Endpoints

### 1. Web Search (Most Common)
```bash
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation phoenix az"}'
```

### 2. Image Search
```bash
curl -s -X POST 'https://google.serper.dev/images' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation"}'
```

### 3. News Search
```bash
curl -s -X POST 'https://google.serper.dev/news' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "insulation industry news"}'
```

### 4. Places Search (Local SEO)
```bash
curl -s -X POST 'https://google.serper.dev/places' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "insulation contractors phoenix az"}'
```

### 5. Maps Search
```bash
curl -s -X POST 'https://google.serper.dev/maps' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "insulation contractors near me", "location": "Phoenix, AZ"}'
```

### 6. Video Search
```bash
curl -s -X POST 'https://google.serper.dev/videos' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation DIY"}'
```

### 7. Shopping Search
```bash
curl -s -X POST 'https://google.serper.dev/shopping' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation kit"}'
```

### 8. Scholar Search
```bash
curl -s -X POST 'https://google.serper.dev/scholar' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation energy efficiency study"}'
```

### 9. Autocomplete
```bash
curl -s -X POST 'https://google.serper.dev/autocomplete' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation"}'
```

## Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `gl` | string | Country code (default: "us") |
| `hl` | string | Language (default: "en") |
| `location` | string | Location for local results |
| `num` | int | Number of results (default: 10, max: 100) |
| `page` | int | Page number for pagination |
| `tbs` | string | Time filter: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month), qdr:y (year) |

## Response Structure

### Web Search Response
```json
{
  "searchParameters": {
    "q": "query",
    "gl": "us",
    "hl": "en"
  },
  "knowledgeGraph": {
    "title": "Entity Name",
    "type": "Entity Type",
    "description": "...",
    "attributes": {}
  },
  "organic": [
    {
      "title": "Page Title",
      "link": "https://...",
      "snippet": "Description...",
      "position": 1
    }
  ],
  "peopleAlsoAsk": [
    {
      "question": "Related question?",
      "snippet": "Answer...",
      "link": "https://..."
    }
  ],
  "relatedSearches": [
    {"query": "related search term"}
  ]
}
```

### Places Response
```json
{
  "places": [
    {
      "title": "Business Name",
      "address": "123 Main St, City, AZ",
      "rating": 4.8,
      "reviews": 150,
      "phone": "(555) 123-4567",
      "website": "https://...",
      "cid": "google_place_id"
    }
  ]
}
```

## Usage Examples

### SEO Competitor Analysis
```bash
# Search for competitor keywords
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "spray foam insulation phoenix",
    "num": 20
  }' | jq '.organic[] | {position, title, link}'
```

### Local Business Research
```bash
# Find competitors in a market
curl -s -X POST 'https://google.serper.dev/places' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "insulation contractors",
    "location": "Phoenix, AZ"
  }' | jq '.places[] | {title, rating, reviews, address}'
```

### Content Research (People Also Ask)
```bash
# Get related questions for content ideas
curl -s -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation cost"}' | jq '.peopleAlsoAsk'
```

### Keyword Ideas (Autocomplete)
```bash
# Get search suggestions
curl -s -X POST 'https://google.serper.dev/autocomplete' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "spray foam insulation"}' | jq '.suggestions'
```

## Python Helper Script

```python
#!/usr/bin/env python3
"""Serper Google Search API wrapper"""

import os
import json
import requests
from typing import Optional

SERPER_API_KEY = os.getenv('SERPER_API_KEY')
BASE_URL = "https://google.serper.dev"

def search(query: str, num: int = 10, **kwargs) -> dict:
    """Standard Google search"""
    return _request("/search", {"q": query, "num": num, **kwargs})

def images(query: str, num: int = 10, **kwargs) -> dict:
    """Image search"""
    return _request("/images", {"q": query, "num": num, **kwargs})

def news(query: str, num: int = 10, **kwargs) -> dict:
    """News search"""
    return _request("/news", {"q": query, "num": num, **kwargs})

def places(query: str, location: Optional[str] = None, **kwargs) -> dict:
    """Local places/business search"""
    params = {"q": query, **kwargs}
    if location:
        params["location"] = location
    return _request("/places", params)

def maps(query: str, location: str, **kwargs) -> dict:
    """Maps search"""
    return _request("/maps", {"q": query, "location": location, **kwargs})

def videos(query: str, num: int = 10, **kwargs) -> dict:
    """Video search"""
    return _request("/videos", {"q": query, "num": num, **kwargs})

def shopping(query: str, num: int = 10, **kwargs) -> dict:
    """Shopping search"""
    return _request("/shopping", {"q": query, "num": num, **kwargs})

def scholar(query: str, num: int = 10, **kwargs) -> dict:
    """Academic/scholar search"""
    return _request("/scholar", {"q": query, "num": num, **kwargs})

def autocomplete(query: str, **kwargs) -> dict:
    """Get search suggestions"""
    return _request("/autocomplete", {"q": query, **kwargs})

def _request(endpoint: str, params: dict) -> dict:
    """Make API request"""
    response = requests.post(
        f"{BASE_URL}{endpoint}",
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        },
        json=params
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search(query)
        print(json.dumps(results, indent=2))
    else:
        print("Usage: serper_search.py <query>")
```

## Pricing

- **Free tier:** 2,500 searches/month
- **Paid:** ~$0.001 per search ($1 per 1,000 searches)
- **No credit card required** for free tier

## Best Practices

1. **Cache results** when possible to save API calls
2. **Use specific queries** for better results
3. **Combine endpoints** - use autocomplete for keyword ideas, then search for rankings
4. **Local SEO** - always include location in Places/Maps searches
5. **Time filter** - use `tbs` parameter for recent results when needed

## Integration Ideas

- **SEO Rank Tracker** - Monitor keyword positions daily
- **Competitor Monitor** - Track competitor visibility
- **Content Research** - Find People Also Ask questions
- **Lead Generation** - Find businesses in target markets
- **News Monitoring** - Track industry news mentions
- **Local SEO Audit** - Analyze local pack results
