#!/usr/bin/env python3
"""Browse subreddit posts. Usage: python3 get_posts.py HomeImprovement --sort top --time week"""
import argparse
from reddit_api import api_get, print_posts_list, print_pagination


def main():
    parser = argparse.ArgumentParser(description="Get subreddit posts")
    parser.add_argument("subreddit", help="Subreddit name (without r/)")
    parser.add_argument("--sort", "-s", choices=["hot", "new", "top", "rising", "controversial"],
                        default="hot", help="Sort method")
    parser.add_argument("--time", "-t", choices=["hour", "day", "week", "month", "year", "all"],
                        help="Time filter (for top/controversial)")
    parser.add_argument("--limit", "-l", type=int, default=25, help="Max posts")
    parser.add_argument("--after", "-a", help="Pagination cursor")
    args = parser.parse_args()

    path = f"r/{args.subreddit}/{args.sort}"
    params = {"t": args.time, "limit": min(args.limit, 100), "after": args.after}

    data = api_get(path, params)
    listing = data.get("data", {})
    posts = listing.get("children", [])

    print(f"subreddit: r/{args.subreddit}")
    print(f"sort: {args.sort}" + (f", time: {args.time}" if args.time else ""))
    print_posts_list(posts, f"r/{args.subreddit}/{args.sort}")
    print_pagination(listing)


if __name__ == "__main__":
    main()
