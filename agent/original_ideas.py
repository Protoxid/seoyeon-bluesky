"""Develop an optional original idea before comparing it with feed interactions."""
import json
from .public_boundary import BOUNDARY, public_data


def propose(generator, identity, context, material, recent_posts, allowed_formats):
    from .generator import parse_json_object
    raw, _ = generator._call_llm(
        BOUNDARY + "Consider an original post independently of replying to another person. "
        "Develop one specific idea from authored interests, taste, an open question or kept draft. "
        "Ordinary opinions and explicitly fictional visual concepts are valid; no researched achievement is required. "
        "Do not copy another person's post, invent a physical accomplishment, force a topic, or post because time passed. "
        "Avoid repeating recent posts. You may return format=none. This is a proposal, not publication authority. "
        "Return JSON {format:text|image|none,idea:string}; idea at most 500 characters. "
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
        return {"format": data["format"], "idea": idea.strip()}, "proposed"
    except (ValueError, TypeError, KeyError):
        return None, "invalid"
