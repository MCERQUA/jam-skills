---
name: reddit
description: "Reddit research tools. Search posts, browse subreddits, read threads with comments, check user profiles. No API key required. Use when the user mentions 'reddit,' 'subreddit,' 'r/,' 'reddit search,' 'reddit research,' 'what does reddit say,' 'reddit posts,' or wants to search/browse Reddit for any reason."
metadata:
  version: 1.0.0
---

# Reddit Research

Search and browse Reddit's public content. No API key, no auth, no cost.

## Tools

All scripts run with Python 3 (stdlib only). Run from the skill directory:

```bash
cd /mnt/shared-skills/reddit/scripts
```

### Search Posts
```bash
python3 /mnt/shared-skills/reddit/scripts/search_posts.py "query" [options]
```
| Arg | Description | Default |
|-----|-------------|---------|
| `query` | Search terms (required) | -- |
| `--subreddit` / `-r` | Restrict to one subreddit | all |
| `--sort` / `-s` | relevance, hot, top, new, comments | relevance |
| `--time` / `-t` | hour, day, week, month, year, all | all |
| `--limit` / `-l` | Max results (up to 100) | 25 |
| `--after` / `-a` | Pagination cursor | -- |

### Browse Subreddit
```bash
python3 /mnt/shared-skills/reddit/scripts/get_posts.py SUBREDDIT [options]
```
| Arg | Description | Default |
|-----|-------------|---------|
| `subreddit` | Subreddit name without r/ (required) | -- |
| `--sort` / `-s` | hot, new, top, rising, controversial | hot |
| `--time` / `-t` | hour, day, week, month, year, all | -- |
| `--limit` / `-l` | Max results (up to 100) | 25 |

### Get Post + Comments
```bash
python3 /mnt/shared-skills/reddit/scripts/get_post.py POST_ID [options]
```
| Arg | Description | Default |
|-----|-------------|---------|
| `post_id` | Reddit post ID (required) | -- |
| `--comments` / `-c` | Max comments | 20 |
| `--json` / `-j` | Raw JSON output | off |

### Get Subreddit Info
```bash
python3 /mnt/shared-skills/reddit/scripts/get_subreddit.py SUBREDDIT [--json]
```

### Get User Profile
```bash
python3 /mnt/shared-skills/reddit/scripts/get_user.py USERNAME [--posts 10] [--json]
```

## Examples

```bash
# Search all of Reddit
python3 /mnt/shared-skills/reddit/scripts/search_posts.py "AI agents" --sort top --time month --limit 20

# Search within a subreddit
python3 /mnt/shared-skills/reddit/scripts/search_posts.py "best framework" -r webdev --limit 15

# Browse hot posts
python3 /mnt/shared-skills/reddit/scripts/get_posts.py ClaudeAI --limit 10

# Top posts this week
python3 /mnt/shared-skills/reddit/scripts/get_posts.py LocalLLaMA --sort top --time week

# Read a specific thread
python3 /mnt/shared-skills/reddit/scripts/get_post.py abc123 --comments 50

# Check a user
python3 /mnt/shared-skills/reddit/scripts/get_user.py some_user --posts 5
```

## Notes

- **No API key required** -- uses Reddit's public JSON API
- **Rate limit:** ~100 req/min (generous)
- **Datacenter IP warning:** Reddit blocks some datacenter IPs with 403. If all requests fail, the IP is blocked -- not a code issue.
- **Pagination:** Use `--after` with the `next_cursor` from output to get more results
