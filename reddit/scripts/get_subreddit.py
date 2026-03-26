#!/usr/bin/env python3
"""Get subreddit info. Usage: python3 get_subreddit.py HomeImprovement"""
import argparse
import json
from reddit_api import api_get, clean_subreddit, print_subreddit


def main():
    parser = argparse.ArgumentParser(description="Get subreddit info")
    parser.add_argument("subreddit", help="Subreddit name (without r/)")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    data = api_get(f"r/{args.subreddit}/about")
    sub = clean_subreddit(data)

    if args.json:
        print(json.dumps(sub, indent=2))
    else:
        print_subreddit(sub)


if __name__ == "__main__":
    main()
