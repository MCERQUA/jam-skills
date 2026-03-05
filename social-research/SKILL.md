---
name: social-research
description: "Social media research tools for local service businesses. Use when the owner mentions 'market research,' 'what customers say,' 'competitor monitoring,' 'Reddit research,' 'social listening,' 'customer sentiment,' 'common complaints,' 'what people ask about,' or wants to understand what customers discuss online about their industry. Zero cost -- no API keys required."
metadata:
  version: 1.0.0
---

# Social Research

Free social listening toolkit for local service businesses. Search Reddit's public JSON API to discover what real customers say about your industry -- complaints, questions, recommendations, and competitor mentions. No API keys, no cost, no rate-limit hassles.

## Why This Matters for Local Service Businesses

Your customers talk about you online before they ever call you. Reddit is where homeowners ask for advice, complain about bad contractors, recommend good ones, and discuss pricing. This skill lets you tap into that conversation at zero cost.

**What you can learn:**
- What homeowners complain about most when hiring your trade
- What questions people ask before buying your service
- What competitors get praised or criticized for
- What price ranges customers consider "fair" vs "too expensive"
- What objections come up most often
- What content topics would resonate with your audience

## Prerequisites

**No API key required.** Reddit's public JSON API works without authentication. Just run the scripts.

**Quick test:**
```bash
cd <skill_directory>
python3 scripts/get_posts.py HomeImprovement --limit 3
```

## Scripts

All scripts are in `scripts/` and run with Python 3 (stdlib only, no pip installs needed).

### search_posts.py -- Search for topics across all of Reddit

Find posts matching any keyword or phrase. Optionally restrict to a specific subreddit.

```bash
# Search all of Reddit
python3 scripts/search_posts.py "plumber ripped me off" --limit 20

# Search within a specific subreddit
python3 scripts/search_posts.py "HVAC replacement cost" --subreddit HomeImprovement --limit 20

# Search by top-voted results in the past year
python3 scripts/search_posts.py "best roofing contractor" --sort top --time year --limit 25

# Search sorted by most comments (highest engagement)
python3 scripts/search_posts.py "pest control worth it" --sort comments --time all
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `query` | Search terms (required) | -- |
| `--subreddit` / `-r` | Restrict to one subreddit | all |
| `--sort` / `-s` | relevance, hot, top, new, comments | relevance |
| `--time` / `-t` | hour, day, week, month, year, all | all |
| `--limit` / `-l` | Max results (up to 100) | 25 |
| `--after` / `-a` | Pagination cursor for next page | -- |

### get_posts.py -- Browse a subreddit's posts

Get hot, new, top, rising, or controversial posts from any subreddit.

```bash
# Hot posts (default)
python3 scripts/get_posts.py HomeImprovement --limit 20

# Newest posts
python3 scripts/get_posts.py HVAC --sort new --limit 20

# Top posts of all time
python3 scripts/get_posts.py Plumbing --sort top --time all --limit 10

# Top posts this week
python3 scripts/get_posts.py Roofing --sort top --time week

# Rising posts (gaining traction right now)
python3 scripts/get_posts.py electricians --sort rising
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `subreddit` | Subreddit name without r/ (required) | -- |
| `--sort` / `-s` | hot, new, top, rising, controversial | hot |
| `--time` / `-t` | hour, day, week, month, year, all (for top/controversial) | -- |
| `--limit` / `-l` | Max results (up to 100) | 25 |
| `--after` / `-a` | Pagination cursor for next page | -- |

### get_post.py -- Get a full post with all comments

Retrieve a specific post and its comment thread. Use this after finding an interesting post via search or browsing.

```bash
# Get post with default 20 comments
python3 scripts/get_post.py abc123

# Get post with 50 comments
python3 scripts/get_post.py abc123 --comments 50

# Get raw JSON output
python3 scripts/get_post.py abc123 --json
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `post_id` | Reddit post ID (required) | -- |
| `--comments` / `-c` | Max comments to retrieve | 20 |
| `--json` / `-j` | Output raw JSON | off |

### get_subreddit.py -- Get subreddit metadata

Check subscriber count, activity level, and description for any subreddit.

```bash
python3 scripts/get_subreddit.py HomeImprovement
python3 scripts/get_subreddit.py HVAC
python3 scripts/get_subreddit.py phoenix --json
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `subreddit` | Subreddit name without r/ (required) | -- |
| `--json` / `-j` | Output raw JSON | off |

### get_user.py -- Get a user's profile

Look up a Reddit user's karma, account age, and recent posts. Useful for checking if a commenter is a real customer or a competitor/shill.

```bash
python3 scripts/get_user.py some_username
python3 scripts/get_user.py some_username --posts 10
```

**Arguments:**
| Arg | Description | Default |
|-----|-------------|---------|
| `username` | Reddit username without u/ (required) | -- |
| `--posts` / `-p` | Include N recent posts | 0 |
| `--json` / `-j` | Output raw JSON | off |

## Sort Options Reference

| Sort | Description | Time Filter? |
|------|-------------|-------------|
| `hot` | Trending posts (default) | No |
| `new` | Latest posts | No |
| `top` | Highest voted | Yes: hour, day, week, month, year, all |
| `rising` | Gaining traction now | No |
| `controversial` | Mixed upvotes/downvotes | Yes: hour, day, week, month, year, all |
| `relevance` | Best match (search only) | Yes |
| `comments` | Most commented (search only) | Yes |

## Key Subreddits for Local Service Businesses

### Home Services (where your customers are)
| Subreddit | Subscribers | What You'll Find |
|-----------|------------|-----------------|
| r/HomeImprovement | 5M+ | Homeowner questions, contractor reviews, project advice |
| r/homeowners | 500K+ | New homeowner questions, maintenance concerns |
| r/DIY | 20M+ | DIY attempts (often leading to "should've hired a pro" posts) |
| r/RealEstate | 800K+ | Home inspection issues, repair negotiations |

### Trade-Specific
| Subreddit | Focus |
|-----------|-------|
| r/HVAC | HVAC techs and homeowner questions about heating/cooling |
| r/Plumbing | Plumbing issues, cost discussions, contractor selection |
| r/electricians | Electrical work questions, code requirements, hiring |
| r/Roofing | Roof repairs, replacement costs, material comparisons |
| r/pestcontrol | Pest identification, treatment effectiveness, pricing |
| r/landscaping | Landscaping design, lawn care, hardscaping costs |
| r/Insurance | Home insurance claims, coverage questions |

### Business Strategy
| Subreddit | Focus |
|-----------|-------|
| r/smallbusiness | Operations, marketing, pricing strategy |
| r/entrepreneur | Growth tactics, hiring, business development |
| r/sweatystartup | Service business startups (HVAC, cleaning, etc.) |
| r/Contractor | Contractor business operations, bidding, contracts |

### Local / Regional
City and regional subreddits are goldmines for local market research:
- r/phoenix, r/dallas, r/houston, r/denver, r/seattle, r/atlanta, r/chicago
- r/AskLosAngeles, r/AskNYC, r/AskSF
- People constantly ask "can anyone recommend a good plumber/electrician/etc?"
- Search your city subreddit for your trade to see what locals say

## Research Workflow

Use this 5-step process to turn Reddit data into actionable business intelligence.

### Step 1: Discover What Customers Are Saying

Search for your service type using the language customers actually use (not industry jargon).

```bash
# What do homeowners say about hiring your trade?
python3 scripts/search_posts.py "hiring a plumber" --sort top --time year --limit 25
python3 scripts/search_posts.py "plumber cost" --subreddit HomeImprovement --limit 20
python3 scripts/search_posts.py "HVAC company recommendation" --sort top --time year

# What are people frustrated about?
python3 scripts/search_posts.py "plumber ripped me off" --limit 20
python3 scripts/search_posts.py "bad contractor experience" --subreddit homeowners --limit 20

# What do people wish they knew?
python3 scripts/search_posts.py "what I wish I knew before" --subreddit HomeImprovement --sort top --time all
```

### Step 2: Identify Top Pain Points and Complaints

Read the highest-voted complaint threads to find recurring themes.

```bash
# Top posts about problems with contractors
python3 scripts/search_posts.py "contractor nightmare" --sort top --time all --limit 20

# Browse a trade subreddit for customer frustrations
python3 scripts/get_posts.py Plumbing --sort top --time month --limit 25

# Read comments on a high-engagement complaint post
python3 scripts/get_post.py <post_id> --comments 50
```

**Common patterns to look for:**
- Pricing surprises / hidden fees
- Poor communication / no-shows
- Quality issues after the job
- Difficulty getting callbacks or quotes
- Feeling pressured by upsells

### Step 3: Monitor Competitor Mentions

Search for competitor brand names, or search your city subreddit for your trade.

```bash
# Search for a competitor by name
python3 scripts/search_posts.py "ServiceTitan" --sort new --limit 20
python3 scripts/search_posts.py "CompetitorName HVAC" --limit 15

# What does your city's subreddit say about your trade?
python3 scripts/search_posts.py "plumber" --subreddit phoenix --sort new --limit 25
python3 scripts/search_posts.py "AC repair" --subreddit dallas --sort top --time year
```

### Step 4: Extract Content and FAQ Ideas

Real customer questions make the best content topics. Every question you find is a blog post, social media post, or FAQ answer.

```bash
# Questions people ask before hiring
python3 scripts/search_posts.py "how to choose a plumber" --sort top --time all
python3 scripts/search_posts.py "what to look for HVAC company" --limit 20
python3 scripts/search_posts.py "is it worth replacing" --subreddit HomeImprovement --sort top --time year

# Price-related questions (great for pricing pages)
python3 scripts/search_posts.py "how much should I pay for" --subreddit HomeImprovement --limit 25
python3 scripts/search_posts.py "fair price for roof replacement" --sort top --time all
```

### Step 5: Compile Into Actionable Intelligence

After gathering data, organize findings into:

1. **Top 5 Customer Complaints** -- Address these in your sales process and on your website
2. **Top 10 Customer Questions** -- Build FAQ pages and blog content around these
3. **Price Expectations** -- Know what customers think is "fair" so you can frame your pricing
4. **Competitor Weaknesses** -- Position your business against what others get wrong
5. **Content Calendar** -- Turn every real question into a piece of content
6. **Objection Handling Scripts** -- Use real objections from Reddit to prepare your team

## Use Case Examples

### "What do homeowners complain about when hiring a plumber?"
```bash
python3 scripts/search_posts.py "plumber complaint" --sort top --time year --limit 25
python3 scripts/search_posts.py "plumber overcharged" --subreddit HomeImprovement --limit 20
python3 scripts/search_posts.py "bad plumber experience" --sort top --time all --limit 15
```

### "What questions do people ask about HVAC in r/HomeImprovement?"
```bash
python3 scripts/search_posts.py "HVAC" --subreddit HomeImprovement --sort top --time year --limit 25
python3 scripts/search_posts.py "air conditioning replacement" --subreddit HomeImprovement --limit 20
python3 scripts/search_posts.py "furnace" --subreddit HomeImprovement --sort new --limit 20
```

### "What are common objections to roof replacement costs?"
```bash
python3 scripts/search_posts.py "roof replacement cost" --sort top --time all --limit 25
python3 scripts/search_posts.py "roofing too expensive" --limit 20
python3 scripts/search_posts.py "worth it to replace roof" --subreddit homeowners --limit 20
```

### "What do people in Phoenix say about AC companies?"
```bash
python3 scripts/search_posts.py "AC repair" --subreddit phoenix --sort top --time year --limit 20
python3 scripts/search_posts.py "air conditioning company" --subreddit phoenix --limit 25
python3 scripts/search_posts.py "HVAC recommendation" --subreddit phoenix --sort new --limit 15
```

## API Details

- **Method:** Reddit public JSON API (append `.json` to any Reddit URL)
- **Authentication:** None required
- **Rate limit:** ~100 requests/minute (generous for research use)
- **Cost:** Free
- **Docs:** https://www.reddit.com/dev/api

## Related Skills

| Skill | How It Connects |
|-------|----------------|
| `content-strategy` | Turn discovered questions and pain points into content plans |
| `review-manager` | Cross-reference Reddit complaints with your own review monitoring |
| `customer-comms` | Address discovered pain points proactively in customer communications |
| `sales-scripts` | Build objection-handling scripts from real objections found on Reddit |
| `marketing-ideas` | Use research findings to generate research-backed growth ideas |
| `copywriting` | Write website copy that addresses real customer concerns |
| `local-seo` | Target the exact phrases customers use when searching for your service |
| `competitor-alternatives` | Build comparison pages using competitor strengths/weaknesses from Reddit |
