# Deprecated Legacy Modules (Instagram & Fanvue)

As of October 2026, the project has completely removed all Instagram and Fanvue functionality to focus exclusively on Seo-yeon's autonomous Bluesky persona (`@syeonhn.bsky.social`).

The following files in `growth/` are deprecated and disabled:
- `fanvue_api.py`: Fanvue REST client.
- `fanvue_auth.py`: Fanvue OAuth helper.
- `fanvue_chat_agent.py`: Automated Fanvue subscriber chat responder.
- `fanvue_dm.py`: Automated Fanvue welcome DMs.
- `ig_engage.py`: Instagram liking and engagement script.
- `ig_schedule_worker.py`: Instagram automated schedule publisher.
- `bsky_funnel_post.py`: Legacy script posting Fanvue affiliate tracking links (`c=fv-4`).
- `campaign_orchestrator.py`: Cross-platform synchronized Fanvue/Bluesky dropper.
- `publish_sunday_fanvue.py`: One-off Sunday Fanvue drop script.

All autonomous activity is now managed through `agent/runner.py` / `agent_runner.py`.
