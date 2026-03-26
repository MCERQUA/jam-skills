#!/usr/bin/env python3
"""
Reddit API - No credentials needed for public read-only access.
Just need a proper User-Agent header.
"""

USER_AGENT = "JamBot-Reddit/1.0 (by /u/jambot-research)"


def get_user_agent() -> str:
    """Get User-Agent for Reddit API requests"""
    return USER_AGENT
