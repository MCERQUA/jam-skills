#!/usr/bin/env python3
"""Get a full post with comments. Usage: python3 get_post.py abc123 --comments 50"""
import argparse
import json
from reddit_api import api_get, clean_post, clean_comment, print_post, print_comments_list


def main():
    parser = argparse.ArgumentParser(description="Get Reddit post with comments")
    parser.add_argument("post_id", help="Reddit post ID")
    parser.add_argument("--comments", "-c", type=int, default=20, help="Max comments")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    post_id = args.post_id.strip()
    if post_id.startswith("t3_"):
        post_id = post_id[3:]

    # Reddit returns [post_listing, comments_listing]
    data = api_get(f"comments/{post_id}", {"limit": args.comments, "depth": 3})

    if isinstance(data, list) and len(data) >= 2:
        post_data = data[0]["data"]["children"][0]
        comments_data = data[1]["data"]["children"]

        if args.json:
            print(json.dumps({"post": clean_post(post_data), "comments": [
                clean_comment(c) for c in comments_data if c.get("kind") == "t1"
            ]}, indent=2))
        else:
            post = clean_post(post_data)
            print_post(post)
            print()
            print_comments_list(comments_data)
    else:
        print("error: Unexpected response format")


if __name__ == "__main__":
    main()
