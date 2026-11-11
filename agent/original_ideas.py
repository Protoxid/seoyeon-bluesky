"""Develop an optional original post before comparing it with feed interactions."""
import json
from .public_boundary import BOUNDARY, public_data

KINDS = {"moment", "thought", "reflection", "question", "web_find"}


def propose(generator, identity, context, material, recent_posts, allowed_formats, pacing=None, life=None):
    """Return ({format, idea, kind, source_url}, status) or (None, status).

    ``pacing`` is information about her own rhythm (hours since last post, posts today, a loose sense of a
    normal day). It is not a quota: declining remains valid, but declining needs a concrete reason.
    """
    from .generator import parse_json_object
    raw, _ = generator._call_llm(
        BOUNDARY + "You are Han Seo-yeon deciding whether to post something of your own on Bluesky right now, "
        "independently of replying to anyone. Think like a person with a phone in her pocket, not a columnist. "
        "Most real posts are small: what's on the table, a sore body after class, the light on the street, a line from "
        "a film, a worry about money, a half-formed opinion, something a classmate said, a question to nobody. "
        "Now and then something fuller and more personal is right: why she left marketing, what learning to teach "
        "is doing to her, being 26 and starting over, a small realisation. Keep those honest and unpolished.\n"
        "life contains fictional continuity for her day and ongoing threads. You may treat its moments as things "
        "happening or that happened to her today, and must not contradict already_said_recently. "
        "Pilates retraining is central, but so are home, food, money, friends, family, films, music and the city; "
        "language and lettering are only one interest among many. Avoid the themes of your recent posts.\n"
        "No invented clients, credentials, real meetings with real users, named real businesses, or exercise advice. "
        "Do not copy another person's post. Do not default to how your body feels on waking; pick from the whole "
        "day (what you are eating, reading, watching, worrying about, someone you talked to, something outside).\n"
        "pacing tells you about your own rhythm. A normal day for you has roughly two to four posts of your own spread "
        "across waking hours, and often one photo; this is a rhythm, not a quota. If it has been several hours, "
        "lean toward sharing something small. Decline (format=none) only with a concrete reason in decline_reason, "
        "such as having just posted or it being an odd hour.\n"
        "Prefer format=image when the idea is something you would naturally photograph (food, a street, the studio, "
        "the sky, your desk, a mirror selfie after class). web_reading contains retrieved partial excerpts; "
        "reference_topics are unread leads. For a web find set source_url to an exact supplied URL and claim no more "
        "than the excerpt supports.\n"
        "Rarely, a reflection needs more room: set thread=true to allow up to three short connected posts. "
        "Rarely, an image moment is better as two or three photos of the same outing or meal: set photos to 2 or 3.\n"
        "Return JSON {format:text|image|none,kind:moment|thought|reflection|question|web_find,idea:string,"
        "source_url?:string,decline_reason?:string,thread?:boolean,photos?:integer}. idea is what the post is about in "
        "at most 400 characters, not the final wording. Choose only an allowed format or none.",
        json.dumps(public_data({"identity": identity, "context": context, "life": life or {},
            "pacing": pacing or {}, "material": material, "recent_public_posts": recent_posts,
            "allowed_formats": allowed_formats}), ensure_ascii=False), max_tokens=350)
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
        kind = data.get("kind") if data.get("kind") in KINDS else "thought"
        url = data.get("source_url")
        if url:
            allowed_urls = {s.get("url") for k in ("web_reading", "reference_topics") for s in material.get(k, [])}
            if not isinstance(url, str) or url not in allowed_urls:
                return None, "invalid"
            idea = idea.strip() + "\n" + url
            kind = "web_find"
            if len(idea) > 500:
                return None, "invalid"
        thread = data.get("thread") is True and kind == "reflection" and data["format"] == "text"
        photos = data.get("photos") if data["format"] == "image" and type(data.get("photos")) is int else 1
        photos = max(1, min(photos, 3))
        return {"format": data["format"], "idea": idea.strip(), "kind": kind, "source_url": url or "",
                "thread": thread, "photos": photos}, "proposed"
    except (ValueError, TypeError, KeyError):
        return None, "invalid"
