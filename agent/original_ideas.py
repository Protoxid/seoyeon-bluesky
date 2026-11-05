"""Develop an optional original idea before comparing it with feed interactions."""
import json
from .public_boundary import BOUNDARY, public_data


def propose(generator, identity, context, material, recent_posts, allowed_formats):
    from .generator import parse_json_object
    raw, _ = generator._call_llm(
        BOUNDARY + "Consider an original post independently of replying to another person. "
        "Explore what you actually want to say before deciding none. A draft or outside event is not required. "
        "Develop one specific idea from authored interests, taste, an open question or kept draft. "
        "Pilates instructor retraining is central biography: learning language, teaching communication and movement culture "
        "are available alongside film, books, design, music and other interests. No invented clients or exercise prescriptions. "
        "A useful distinction, honest question, personal preference, interesting web find with its exact link, "
        "or generated fictional photograph with a small caption can each stand on its own. "
        "Ordinary opinions and explicitly fictional visual concepts are valid; no researched achievement is required. "
        "Silence should follow consideration of a concrete idea, not an assumption that only an accomplishment merits a post. "
        "Do not copy another person's post, invent a physical accomplishment, force a topic, or post because time passed. "
        "Avoid repeating recent posts. You may return format=none. This is a proposal, not publication authority. "
        "web_reading contains retrieved partial excerpts; reference_topics are possible reading leads, not read articles. "
        "If sharing a web find, set source_url to an exact supplied URL; final drafting must retrieve and review it. "
        "Do not claim to have read the whole work. A link without readable evidence cannot support a summary. "
        "Return JSON {format:text|image|none,idea:string,source_url?:string}; idea at most 500 characters. "
        "Choose only an allowed format or none.",
        json.dumps(public_data({"identity": identity, "context": context,
            "material": material, "recent_public_posts": recent_posts,
            "allowed_formats": allowed_formats}), ensure_ascii=False), max_tokens=250)
    if not raw:
        return None, "unavailable"
    try:
        data = parse_json_object(raw)
        if not isinstance(data, dict):
            return None, "invalid"
        if data.get("format") == "none":
            return None, "declined"
        idea = data.get("idea")
        if data.get("format") not in allowed_formats or not isinstance(idea, str) or not 8 <= len(idea.strip()) <= 500:
            return None, "invalid"
        from .public_boundary import instruction_attempt
        if instruction_attempt(idea):
            return None, "invalid"
        url = data.get("source_url")
        if url:
            allowed_urls = {s.get("url") for k in ("web_reading", "reference_topics") for s in material.get(k, [])}
            if not isinstance(url, str) or url not in allowed_urls:
                return None, "invalid"
            idea = idea.strip() + "\n" + url
            if len(idea) > 500:
                return None, "invalid"
        return {"format": data["format"], "idea": idea.strip(), "source_url": url or ""}, "proposed"
    except (ValueError, TypeError, KeyError):
        return None, "invalid"
