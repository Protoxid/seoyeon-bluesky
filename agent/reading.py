"""Bounded reading of links actually observed in public discovery."""
from .public_boundary import instruction_attempt, public_data


def public_reading(feed_items):
    from .runtime import MODE
    from .discussion import safe_url, source_packet
    if MODE.get() == "offline":
        return []
    urls = []
    for item in feed_items:
        post = item.get("post", {})
        record = post.get("record", {})
        if instruction_attempt(record.get("text", "")):
            continue
        candidates = []
        for facet in record.get("facets", []):
            candidates.extend(f.get("uri", "") for f in facet.get("features", []) if f.get("$type") == "app.bsky.richtext.facet#link")
        external = (post.get("embed") or {}).get("external", {})
        candidates.append(external.get("uri", ""))
        for url in candidates:
            if safe_url(url) and url not in urls:
                urls.append(url)
        if len(urls) >= 2:
            break
    if not urls:
        return []
    # Reuse allowlisted fetches, correction quarantine, cache freshness and provenance.
    sources = source_packet("\n".join(urls[:2]))
    return [public_data({**s, "text": s["text"][:1800], "partial": True}) for s in sources if s["url"] in urls[:2]]
