#!/usr/bin/env python3
"""
Shared JSON-LD schema generator for local business landers.

Takes business-type + services + NAP and emits valid JSON-LD blocks:
  - LocalBusiness with hasOfferCatalog (home / service / location pages)
  - ContactPage (contact pages)
  - FAQPage (any page with FAQ accordion)
  - BreadcrumbList (interior pages)

Usage:
  # Full config files:
  generate_jsonld.py --business business.json --page page.json

  # Inline NAP (quick):
  generate_jsonld.py \
    --name "The Seattle Siding Company" \
    --url "https://theseattlesidingcompany.com" \
    --phone "+12065551234" \
    --city Seattle --state WA \
    --page-type home \
    --output html
"""

import argparse
import json
import sys


# ---------------------------------------------------------------------------
# Schema builders
# ---------------------------------------------------------------------------

def _postal_address(addr: dict) -> dict:
    return {
        "@type": "PostalAddress",
        "streetAddress": addr.get("street", ""),
        "addressLocality": addr.get("city", ""),
        "addressRegion": addr.get("state", ""),
        "postalCode": addr.get("zip", ""),
        "addressCountry": addr.get("country", "US"),
    }


def build_local_business(
    *,
    name: str,
    url: str,
    phone: str,
    address: dict,
    business_type: str = "HomeAndConstructionBusiness",
    description: str = "",
    logo_url: str = "",
    services: list | None = None,
    area_served: list | str | None = None,
    rating: dict | None = None,
    opening_hours: list | None = None,
) -> dict:
    """LocalBusiness with optional hasOfferCatalog, areaServed, aggregateRating."""
    schema: dict = {
        "@context": "https://schema.org",
        "@type": business_type,
        "name": name,
        "url": url,
        "telephone": phone,
        "address": _postal_address(address),
    }

    if description:
        schema["description"] = description
    if logo_url:
        schema["logo"] = logo_url

    if services:
        schema["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": f"{name} Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": svc["name"],
                        **({"description": svc["description"]} if svc.get("description") else {}),
                        **({"url": svc["url"]} if svc.get("url") else {}),
                        **(
                            {
                                "areaServed": (
                                    [{"@type": "City", "name": c} for c in area_served]
                                    if isinstance(area_served, list)
                                    else {"@type": "City", "name": area_served}
                                )
                            }
                            if area_served
                            else {}
                        ),
                    },
                }
                for svc in services
            ],
        }

    if area_served:
        if isinstance(area_served, list):
            schema["areaServed"] = [{"@type": "City", "name": c} for c in area_served]
        else:
            schema["areaServed"] = {"@type": "City", "name": area_served}

    if rating:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(rating["value"]),
            "reviewCount": str(rating["count"]),
            "bestRating": "5",
            "worstRating": "1",
        }

    if opening_hours:
        schema["openingHours"] = opening_hours

    return schema


def build_faq_page(faqs: list, url: str = "") -> dict:
    """FAQPage from [{question, answer}] list."""
    schema: dict = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                },
            }
            for faq in faqs
        ],
    }
    if url:
        schema["url"] = url
    return schema


def build_contact_page(
    *,
    name: str,
    url: str,
    phone: str,
    address: dict,
    email: str = "",
) -> dict:
    """ContactPage schema."""
    schema: dict = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "name": f"Contact {name}",
        "url": url,
        "telephone": phone,
        "address": _postal_address(address),
    }
    if email:
        schema["email"] = email
    return schema


def build_breadcrumb(items: list) -> dict:
    """BreadcrumbList from [{name, url}] list."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item["name"],
                "item": item["url"],
            }
            for i, item in enumerate(items)
        ],
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

PAGE_TYPES = ("home", "service", "location", "contact", "faq", "blog")


def generate_blocks(biz: dict, page: dict) -> list[dict]:
    """
    Combine business config + page config into a list of JSON-LD schema blocks.

    Business config keys (all optional except name/url/phone/address):
        name, url, phone, address (dict), business_type, description, logo_url,
        services ([{name, description?, url?}]), area_served (str | [str]),
        rating ({value, count}), opening_hours ([str])

    Page config keys:
        page_type  (home|service|location|contact|faq|blog)  default: home
        page_url   (overrides biz.url for page-specific schemas)
        faqs       ([{question, answer}])
        breadcrumbs ([{name, url}])
        email      (for contact page)
    """
    page_type = page.get("page_type", "home")
    page_url = page.get("page_url", biz.get("url", ""))
    address = biz.get("address", {})
    if isinstance(address, str):
        # Minimal: treat string as city
        address = {"city": address}

    blocks: list[dict] = []

    # ---- LocalBusiness block (home / service / location) ----
    if page_type in ("home", "service", "location"):
        blocks.append(
            build_local_business(
                name=biz["name"],
                url=biz["url"],
                phone=biz["phone"],
                address=address,
                business_type=biz.get("business_type", "HomeAndConstructionBusiness"),
                description=biz.get("description", ""),
                logo_url=biz.get("logo_url", ""),
                services=biz.get("services"),
                area_served=biz.get("area_served"),
                rating=biz.get("rating"),
                opening_hours=biz.get("opening_hours"),
            )
        )

    # ---- ContactPage block ----
    if page_type == "contact":
        blocks.append(
            build_contact_page(
                name=biz["name"],
                url=page_url,
                phone=biz["phone"],
                address=address,
                email=page.get("email", biz.get("email", "")),
            )
        )

    # ---- FAQPage block ----
    faqs = page.get("faqs") or biz.get("faqs")
    if faqs and page_type in ("home", "service", "location", "faq"):
        blocks.append(build_faq_page(faqs, url=page_url))

    # ---- BreadcrumbList block (not on homepage) ----
    crumbs = page.get("breadcrumbs")
    if crumbs and page_type != "home":
        blocks.append(build_breadcrumb(crumbs))

    return blocks


def render_html(blocks: list[dict]) -> str:
    parts = []
    for block in blocks:
        parts.append('<script type="application/ld+json">')
        parts.append(json.dumps(block, indent=2, ensure_ascii=False))
        parts.append("</script>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_json_arg(val: str) -> dict | list:
    """Load from file path or parse inline JSON string."""
    try:
        with open(val) as f:
            return json.load(f)
    except (OSError, IsADirectoryError):
        return json.loads(val)


def build_biz_from_flags(args) -> dict:
    biz: dict = {
        "name": args.name,
        "url": args.url,
        "phone": args.phone,
        "address": {
            "street": args.street_address or "",
            "city": args.city,
            "state": args.state,
            "zip": args.zip or "",
            "country": args.country,
        },
        "business_type": args.business_type,
    }
    if args.description:
        biz["description"] = args.description
    if args.logo_url:
        biz["logo_url"] = args.logo_url
    if args.services:
        biz["services"] = _load_json_arg(args.services)
    if args.area_served:
        biz["area_served"] = _load_json_arg(args.area_served)
    if args.rating_value and args.rating_count:
        biz["rating"] = {"value": args.rating_value, "count": args.rating_count}
    return biz


def build_page_from_flags(args) -> dict:
    page: dict = {"page_type": args.page_type}
    if args.page_url:
        page["page_url"] = args.page_url
    if args.faqs:
        page["faqs"] = _load_json_arg(args.faqs)
    if args.breadcrumbs:
        page["breadcrumbs"] = _load_json_arg(args.breadcrumbs)
    if args.email:
        page["email"] = args.email
    return page


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate JSON-LD schema blocks for local business landers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Config-file mode
    parser.add_argument("--business", metavar="FILE|JSON",
                        help="Business config (JSON file path or inline JSON)")
    parser.add_argument("--page", metavar="FILE|JSON",
                        help="Page config (JSON file path or inline JSON)")

    # Individual NAP flags (used when --business not provided)
    grp = parser.add_argument_group("NAP flags (alternative to --business)")
    grp.add_argument("--business-type", default="HomeAndConstructionBusiness")
    grp.add_argument("--name")
    grp.add_argument("--url")
    grp.add_argument("--phone")
    grp.add_argument("--street-address", default="")
    grp.add_argument("--city")
    grp.add_argument("--state")
    grp.add_argument("--zip", default="")
    grp.add_argument("--country", default="US")
    grp.add_argument("--description", default="")
    grp.add_argument("--logo-url", default="")
    grp.add_argument("--services", metavar="FILE|JSON",
                     help='[{"name":"...","description":"...","url":"..."}]')
    grp.add_argument("--area-served", metavar="FILE|JSON",
                     help='["Seattle","Bellevue"] or "Seattle"')
    grp.add_argument("--rating-value", type=float)
    grp.add_argument("--rating-count", type=int)

    # Page flags (alternative to --page)
    pgrp = parser.add_argument_group("Page flags (alternative to --page)")
    pgrp.add_argument("--page-type", choices=PAGE_TYPES, default="home")
    pgrp.add_argument("--page-url", default="")
    pgrp.add_argument("--faqs", metavar="FILE|JSON",
                      help='[{"question":"...","answer":"..."}]')
    pgrp.add_argument("--breadcrumbs", metavar="FILE|JSON",
                      help='[{"name":"Home","url":"https://..."}]')
    pgrp.add_argument("--email", default="")

    # Output
    parser.add_argument("--output", choices=["html", "json"], default="html",
                        help="html = <script> tags; json = raw array")

    args = parser.parse_args(argv)

    # Resolve business config
    if args.business:
        biz = _load_json_arg(args.business)
    else:
        if not (args.name and args.url and args.phone and args.city and args.state):
            parser.error(
                "Provide --business FILE or supply --name, --url, --phone, --city, --state"
            )
        biz = build_biz_from_flags(args)

    # Resolve page config
    if args.page:
        page = _load_json_arg(args.page)
    else:
        page = build_page_from_flags(args)

    blocks = generate_blocks(biz, page)

    if not blocks:
        print("# No schema blocks generated for this page_type / config combination",
              file=sys.stderr)
        sys.exit(0)

    if args.output == "json":
        print(json.dumps(blocks, indent=2, ensure_ascii=False))
    else:
        print(render_html(blocks))


if __name__ == "__main__":
    main()
