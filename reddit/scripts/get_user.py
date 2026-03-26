#!/usr/bin/env python3
"""Get Reddit user profile. Usage: python3 get_user.py username --posts 10"""
import argparse
import json
from reddit_api import api_get, clean_user, clean_post, print_user, print_posts_list


def main():
    parser = argparse.ArgumentParser(description="Get Reddit user info")
    parser.add_argument("username", help="Reddit username (without u/)")
    parser.add_argument("--posts", "-p", type=int, default=0, help="Include N recent posts")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    data = api_get(f"user/{args.username}/about")
    user = clean_user(data)

    if args.json:
        result = {"user": user}
        if args.posts > 0:
            posts_data = api_get(f"user/{args.username}/submitted", {"limit": args.posts, "sort": "new"})
            posts = [clean_post(p) for p in posts_data.get("data", {}).get("children", [])]
            result["posts"] = posts
        print(json.dumps(result, indent=2))
    else:
        print_user(user)
        if args.posts > 0:
            posts_data = api_get(f"user/{args.username}/submitted", {"limit": args.posts, "sort": "new"})
            posts = posts_data.get("data", {}).get("children", [])
            if posts:
                print()
                print_posts_list(posts, f"u/{args.username}/posts")


if __name__ == "__main__":
    main()
