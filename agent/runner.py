"""
agent/runner.py — Master Autonomous Agent Execution Runner.

Executes a single autonomous tick of Seo-yeon:
  1. Gathers sensory inputs (Seoul environment, notifications, DMs, timeline).
  2. Evaluates context with the cognitive decision engine.
  3. Executes the winning action (post, reply, DM, like, or NO_ACTION).
  4. Records interactions into persistent multi-tier memory.
  5. Outputs rich, structured observability logs.

Usage:
  python -m agent.runner --auto
  python -m agent.runner --dry-run
  python -m agent.runner --status
  python -m agent.runner --force-action PUBLISH_TEXT_POST
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import os
from typing import Any, Dict, List, Optional

# Module execution must establish isolation before persistent singletons are imported.
if __name__ == "__main__":
    from .cli import main as isolated_main
    sys.exit(isolated_main())

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config import LOGS_DIR, config
from .context_engine import build_environment_context, get_seoul_datetime
from .memory_store import memory_store
from .bsky_client import bsky_client
from .budget_manager import budget_manager
from .decision_engine import ActionType, decision_engine
from .generator import generator
from .goal_manager import goal_manager
from .image_engine import image_engine
from .narrative_engine import narrative_engine
from .notifier import notifier
from .validator import validator


TICK_LOG_FILE = LOGS_DIR / "tick_history.jsonl"


def log_tick(entry: Dict[str, Any]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TICK_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def print_header(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def run_tick(
    dry_run: Optional[bool] = None,
    force_action: Optional[str] = None,
) -> int:
    from .runtime import MODE
    is_dry = (dry_run if dry_run is not None else config.dry_run) or MODE.get() != "live"
    if is_dry and MODE.get() == "live":
        import subprocess
        command = [sys.executable, str(pathlib.Path(__file__).resolve().parent.parent / "agent_runner.py"), "--dry-run"]
        if force_action:
            command.extend(["--force-action", force_action])
        return subprocess.call(command)

    from .vault import vault
    if vault.enc_file.exists():
        if not vault.load_vault():
            print("[CRITICAL] Existing encrypted vault (vault.enc) could not be decrypted.")
            print("Stopping execution safely to prevent data loss or state corruption.")
            return 1
    else:
        vault.load_vault()

    if not is_dry:
        from .migration import migrate_legacy_state
        migrate_legacy_state(memory_store.memory_dir, vault)

    print_header(f"SEO-YEON HAN — AUTONOMOUS SOCIAL AGENT TICK {'[DRY-RUN]' if is_dry else '[LIVE]'}")

    # 1. Check Operational Status
    ok, status_msg = config.is_operational()
    if not ok and not is_dry:
        print(f"[HALTED] {status_msg}")
        return 1

    # 3. Authenticate with Bluesky
    bsky_client.dry_run = is_dry
    auth_ok = bsky_client.authenticate() if MODE.get() != "offline" else False
    if not auth_ok and not is_dry:
        print("[ERROR] Bluesky authentication failed; no simulated success.")
        return 1

    if auth_ok and not is_dry:
        from .delivery import recover_delivery
        if not recover_delivery():
            print("[Delivery] An uncertain action requires reconciliation before new actions.")
            return 1

    if not is_dry:
        from .state_manager import state_manager
        now = get_seoul_datetime()
        state_manager.update_circadian_dynamics(now.hour, now.day, now=now)

    # 2. Build Environment & Temporal Context
    posts_today, replies_today, dms_today, likes_today = memory_store.get_activity_counts_today()
    hours_since_post = memory_store.get_hours_since_last_post()
    hours_since_action = memory_store.get_hours_since_last_action()

    context = build_environment_context(
        hours_since_last_post=hours_since_post,
        hours_since_last_action=hours_since_action,
        posts_today=posts_today,
        replies_today=replies_today,
        dms_today=dms_today,
        likes_today=likes_today,
    )

    print(f"Time:     {context.seoul_time_display} ({context.day_of_week}, {context.circadian_phase})")
    print(f"Weather:  {context.weather.summary()}")
    if context.holiday_note:
        print(f"Calendar: {context.holiday_note}")
    print(f"Recency:  Last post {context.hours_since_last_post:.1f}h ago | Today: {posts_today} posts, {replies_today} replies, {dms_today} DMs, {likes_today} likes")

    # 2b. Check Inbound Master Messages
    processed_master_msgs = notifier.process_master_inbox(context, dry_run=is_dry)
    if processed_master_msgs > 0:
        print(f"  [Master Telegram Interaction] Processed {processed_master_msgs} message(s) from my master.")

    # 2c. Deep Night Cognitive Sleep Pass (Consolidation)
    if context.circadian_phase == "deep_night":
        from .consolidator import consolidator
        consolidator.consolidate(context, dry_run=is_dry)

    # 4. Gather Sensory Observations
    print("\n[Observing Bluesky Sensory Inputs...]")
    notifications = []
    dms = []
    feed_items = []

    if auth_ok:
        notifications = bsky_client.list_notifications(limit=30)
        dms = bsky_client.list_convos(limit=10)
        feed_items = bsky_client.get_discovery_feed(limit=25)
    elif is_dry and os.environ.get("SEOYEON_REPLAY_FILE"):
        fixture = json.loads(pathlib.Path(os.environ["SEOYEON_REPLAY_FILE"]).read_text(encoding="utf-8"))
        notifications, dms, feed_items = fixture.get("notifications", []), fixture.get("dms", []), fixture.get("feed", [])

    if auth_ok and not is_dry:
        from .continuity import ContinuityStore
        from .delivery import Outbox, recover_delivery
        store = ContinuityStore()
        for item in feed_items[:10]:
            post = item.get("post", item)
            text = post.get("record", {}).get("text", "")
            if post.get("uri") and text:
                store.observe(post["uri"], text, kind="external_observation", subject=post.get("author", {}).get("did", ""))

    print(f"  Notifications: {len(notifications)} received")
    print(f"  Conversations: {len(dms)} direct message threads")
    print(f"  Feed Items:    {len(feed_items)} community & timeline posts")

    # 5. Check Budget & Image Constraints
    can_img, img_reason = budget_manager.can_generate_image()

    # 6. Cognitive Evaluation & Decision
    if force_action:
        try:
            chosen_action = ActionType(force_action)
            reason = f"Manually forced via CLI: {force_action}"
            outcome = decision_engine.evaluate(context, notifications, dms, feed_items, can_image=can_img)
            outcome.selected_action = chosen_action
            outcome.reason = reason
            for cand in outcome.all_candidates:
                if cand.action == chosen_action and cand.target_data:
                    outcome.target_data = cand.target_data
                    outcome.intent = cand.intent
                    break
        except ValueError:
            print(f"[ERROR] Invalid force action: {force_action}")
            return 1
    else:
        outcome = decision_engine.evaluate(context, notifications, dms, feed_items, can_image=can_img)

    if not force_action:
        from .choice import choose
        outcome = choose(outcome, context)
    target = outcome.target_data or {}
    post_target = target.get("post") or target.get("notification") or {}
    previous_posts = memory_store.get_recent_context().get("posts", [])
    previous_id = previous_posts[0].get("post_id", "") if previous_posts else "start"
    bsky_client.action_identity = outcome.selected_action.value + ":" + (target.get("last_message_id") or post_target.get("uri") or target.get("did") or (context.date_display + ":" + previous_id))

    print("\n[Cognitive Evaluation]")
    print(f"  Candidate Scores: {json.dumps(outcome.candidate_scores, indent=2)}")
    print(f"  Selected Action:  >>> {outcome.selected_action.value} <<<")
    print(f"  Reasoning:        {outcome.reason}")

    # 7. Action Execution Stage
    executed = False
    result_details: Dict[str, Any] = {}

    if outcome.selected_action == ActionType.NO_ACTION:
        print("\n[Outcome] Decision is NO_ACTION. Seo-yeon remains quietly offline. Restraint preserved.")
        executed = True
        if not is_dry:
            from .continuity import reflect
            reflect(context)
        result_details = {"action": "NO_ACTION", "reason": outcome.reason}

    elif outcome.selected_action == ActionType.PUBLISH_TEXT_POST:
        print("\n[Generating Original Text Post...]")
        post_text, model_used = generator.generate_post(outcome.intent, context)
        print(f"  Draft ({model_used}): \"{post_text}\"")

        if not post_text:
            log_tick({"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "action": "NO_ACTION", "executed": False, "status": "draft_unavailable", "dry_run": is_dry})
            return 0
        res = bsky_client.publish_text_post(post_text)
        if res.get("uri"):
            print(f"  [SUCCESS] Published: {res.get('uri')}")
            if not is_dry:
                memory_store.record_recent_post(post_text, topic="general_thought", post_id=res.get("uri", ""))
                memory_store.log_episode("post", "Published spontaneous thought", {"text": post_text, "uri": res.get("uri")})
                from .continuity import learn_interaction
                learn_interaction(res["uri"], "", post_text, "self")
            executed = True
            result_details = {"uri": res.get("uri"), "text": post_text, "model": model_used}

    elif outcome.selected_action == ActionType.PUBLISH_IMAGE_POST:
        post_text, model_used = generator.generate_post(outcome.intent, context, include_image=True)
        scene_desc = generator.determine_image_scene(post_text, context)
        if not post_text or not scene_desc:
            return 0  # No justified draft/scene, no fabricated fallback.
        from .budget_manager import IMAGE_GEN_COST
        img_res_id = budget_manager.reserve(IMAGE_GEN_COST, action_type="image_generation", provider="kie.ai")
        if not img_res_id:
            return 0
        image_engine.reservation_id = img_res_id
        budget_manager.mark_submitted(img_res_id)
        img_bytes, prompt_used, err = image_engine.generate_image(scene_desc,
            is_selfie=getattr(generator, "last_scene", {}).get("is_selfie"), dry_run=is_dry)
        if img_bytes:
            budget_manager.reconcile(img_res_id, IMAGE_GEN_COST, action_type="image_generation", details="provider completion; estimated tariff")
            approved, alt_text = generator.review_image(img_bytes, post_text, scene_desc)
            if not approved:
                result_details = {"status": "image_review_rejected"}
            else:
                res = bsky_client.publish_image_post(post_text, img_bytes, alt_text=alt_text)
                executed = bool(res.get("uri"))
                if executed and not is_dry:
                    memory_store.record_recent_post(post_text, topic="image_post", post_id=res["uri"], has_image=True)
                result_details = {"uri":res.get("uri"), "text":post_text, "alt_text":alt_text, "status":"delivered" if executed else "delivery_uncertain"}
        else:
            if getattr(image_engine, "last_outcome", "uncertain") in {"not_sent", "rejected"}:
                budget_manager.release(img_res_id)
            result_details = {"status":"image_generation_failed", "request_id":getattr(image_engine,"last_task_id","")}
        image_engine.reservation_id = None

    elif outcome.selected_action in (ActionType.REPLY_COMMENT, ActionType.ANSWER_MENTION):
        notif = outcome.target_data.get("notification", {})
        target_author = notif.get("author", {}).get("handle", "user")
        target_uri = notif.get("uri", "")
        target_cid = notif.get("cid", "")
        user_text = outcome.target_data.get("text", "")
        profile = outcome.target_data.get("profile") or memory_store.get_user_profile(target_author)

        print(f"\n[Processing Inbound Mention/Comment from @{target_author}...]")
        print(f"  User said: \"{user_text}\"")

        # 1. Pre-execution Safety: Check memory store
        if memory_store.has_replied_to_notification(target_uri) or memory_store.has_replied_to_post(target_uri):
            print(f"  [SAFETY ABORT] Target {target_uri} already marked as replied in memory. Preventing duplicate comment.")
            memory_store.mark_notification_handled(notif.get("uri", ""), target_post_uri=target_uri)
            if auth_ok:
                bsky_client.update_seen()
            executed = True
            result_details = {"status": "aborted_duplicate_comment", "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Safety abort: already replied to {target_author}'s comment ({target_uri}).",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        # 2. Pre-execution Safety: Inspect live thread context
        thread_ctx = bsky_client.get_thread_context(target_uri)
        can_reply, block_reason = bsky_client.can_reply_to_thread(target_uri, thread_ctx)
        if not can_reply:
            print(f"  [SAFETY ABORT] {block_reason}. Preventing duplicate comment on same post.")
            memory_store.mark_notification_handled(notif.get("uri", ""), target_post_uri=target_uri)
            if auth_ok:
                bsky_client.update_seen()
            executed = True
            result_details = {"status": "aborted_thread_safety", "reason": block_reason, "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Safety abort: {block_reason}.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        # 3. Draft in-character reply
        reply_text, model_used = generator.generate_reply(target_author, user_text, thread_ctx, profile, context)
        print(f"  Draft Reply ({model_used}): \"{reply_text}\"")

        if not reply_text or model_used in ("failed", "fallback"):
            print(f"  [RESTRAINT ABORT] Could not formulate authentic contextual reply. Remaining silent.")
            memory_store.mark_notification_handled(notif.get("uri", ""), target_post_uri=target_uri)
            if auth_ok:
                bsky_client.update_seen()
            executed = True
            result_details = {"status": "aborted_generation_failed", "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Restraint abort: could not formulate authentic contextual reply to {target_author}.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        # Resolve root & parent
        record = notif.get("record", {})
        reply_meta = record.get("reply", {})
        root_uri = reply_meta.get("root", {}).get("uri", target_uri) if reply_meta else target_uri
        root_cid = reply_meta.get("root", {}).get("cid", target_cid) if reply_meta else target_cid

        res = bsky_client.publish_reply(reply_text, target_uri, target_cid, root_uri, root_cid)
        if res.get("uri"):
            print(f"  [SUCCESS] Published Reply: {res.get('uri')}")
            # Optionally like user's comment
            if config.allow_likes and not is_dry:
                bsky_client.like_post(target_uri, target_cid)

            if not is_dry:
                memory_store.record_user_interaction(target_author, user_text, reply_text, "reply", did=notif.get("author", {}).get("did", ""))
                memory_store.record_recent_reply(
                    target_handle=target_author,
                    user_text=user_text,
                    reply_text=reply_text,
                    uri=res.get("uri", ""),
                    target_uri=target_uri,
                    root_uri=root_uri,
                    notification_uri=notif.get("uri", "")
                )
                from .continuity import learn_interaction
                learn_interaction(res["uri"], user_text, reply_text, profile.did or target_author)
                narrative_engine.detect_and_manage_loops(
                    partner_identifier=notif.get("author", {}).get("did", target_author),
                    partner_handle=target_author,
                    inbound_text=user_text,
                    reply_text=reply_text,
                    dry_run=is_dry,
                )
            executed = True
            result_details = {"reply_uri": res.get("uri"), "reply_text": reply_text}

        if auth_ok:
            bsky_client.update_seen()

    elif outcome.selected_action == ActionType.ANSWER_DM:
        convo_id = outcome.target_data.get("convo_id", "")
        handle = outcome.target_data.get("handle", "user")
        profile = outcome.target_data.get("profile") or memory_store.get_user_profile(handle)
        last_msg_id = outcome.target_data.get("last_message_id", "")

        print(f"\n[Processing Direct Message Thread with @{handle}...]")

        # 1. Pre-execution Safety: Verify message not already handled in memory
        if last_msg_id and memory_store.has_replied_to_dm(last_msg_id):
            print(f"  [SAFETY ABORT] Direct message {last_msg_id} already marked handled in memory. Preventing duplicate reply.")
            executed = True
            result_details = {"status": "aborted_duplicate_dm", "last_message_id": last_msg_id}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Safety abort: already replied to @{handle}'s message ({last_msg_id}).",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        raw_msgs = bsky_client.get_convo_messages(convo_id, limit=10) if convo_id else []

        # 2. Pre-execution Safety: Verify last message was not sent by Seo-yeon
        if raw_msgs:
            newest = raw_msgs[-1] if isinstance(raw_msgs, list) else {}
            newest_sender_did = newest.get("sender", {}).get("did", "")
            if bsky_client.did and newest_sender_did == bsky_client.did:
                print(f"  [SAFETY ABORT] Most recent message in convo {convo_id} was already sent by Seo-yeon. Preventing double response.")
                if last_msg_id and not is_dry:
                    memory_store.mark_dm_handled(last_msg_id)
                executed = True
                result_details = {"status": "aborted_already_sent_by_self", "convo_id": convo_id}
                now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
                log_tick({
                    "ts": now_iso,
                    "seoul_time": context.seoul_time_display,
                    "action": "NO_ACTION",
                    "reason": f"Safety abort: already sent last message in conversation with @{handle}.",
                    "dry_run": is_dry,
                    "executed": True,
                    "details": result_details,
                    "budget": budget_manager.get_summary(),
                })
                return 0

        dm_history = []
        for m in raw_msgs:
            dm_history.append({
                "sender_handle": handle if m.get("sender", {}).get("did") != bsky_client.did else config.bsky_handle,
                "text": m.get("text", "")
            })

        reply_text, model_used = generator.generate_dm_reply(dm_history, profile, context)
        print(f"  Draft DM ({model_used}): [private message generated: {len(reply_text)} chars]")

        if not reply_text or model_used in ("failed", "fallback", "budget_exceeded"):
            print(f"  [RESTRAINT ABORT] Could not formulate authentic DM response. Remaining silent.")
            executed = True
            result_details = {"status": "aborted_generation_failed", "convo_id": convo_id}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Restraint abort: could not formulate authentic DM response to @{handle}.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        res = bsky_client.send_dm(convo_id, reply_text)
        is_delivered = False
        if res and (res.get("id") or res.get("simulated")):
            is_delivered = True

        if is_delivered:
            print(f"  [SUCCESS] Direct Message Sent to @{handle}")
            sent_msg_id = res.get("id") or last_msg_id
            if convo_id and (sent_msg_id or last_msg_id):
                bsky_client.mark_convo_read(convo_id, sent_msg_id or last_msg_id)
            if not is_dry:
                if last_msg_id:
                    memory_store.mark_dm_handled(last_msg_id)
                if sent_msg_id:
                    memory_store.mark_dm_handled(sent_msg_id)
                memory_store.record_user_interaction(handle, "[private direct message]", "[private direct message reply]", "dm")
                vault.append_private_dm(convo_id, handle, dm_history[-1]["text"] if dm_history else "", reply_text)
                from .continuity import learn_interaction
                learn_interaction(last_msg_id or sent_msg_id, dm_history[-1]["text"] if dm_history else "", reply_text,
                                  profile.did or handle, scope="private:" + (profile.did or handle))
                narrative_engine.detect_and_manage_loops(
                    partner_identifier=convo_id or handle,
                    partner_handle=handle,
                    inbound_text=dm_history[-1]["text"] if dm_history else "",
                    reply_text=reply_text,
                    dry_run=is_dry,
                )
            executed = True
            result_details = {"dm_sent": True, "to": handle, "char_count": len(reply_text)}
        else:
            print(f"  [ERROR] DM delivery to @{handle} failed or uncertain. Leaving message unhandled for next tick.")
            executed = False
            result_details = {"dm_sent": False, "to": handle, "error": "delivery_failed_or_uncertain"}

    elif outcome.selected_action == ActionType.BROWSE_AND_LIKE:
        post = outcome.target_data.get("post", {})
        post_uri = post.get("uri", "")
        post_cid = post.get("cid", "")
        author = post.get("author", {}).get("handle", "")
        print(f"\n[Liking Feed Post from @{author}...]")
        if not is_dry:
            res = bsky_client.like_post(post_uri, post_cid)
            if res.get("uri"):
                memory_store.record_recent_like(post_uri, author)
            print("  [SUCCESS] Like confirmed." if res.get("uri") else "  [ERROR] Like not confirmed.")
        else:
            print(f"  [DRY-RUN] Would like post: {post_uri}")
        executed = is_dry or bool(res.get("uri"))
        result_details = {"liked_post": post_uri, "status": "delivered" if executed else "delivery_uncertain"}

    elif outcome.selected_action == ActionType.BROWSE_AND_REPLY:
        post = outcome.target_data.get("post", {})
        target_author = post.get("author", {}).get("handle", "user")
        target_uri = post.get("uri", "")
        target_cid = post.get("cid", "")
        user_text = post.get("record", {}).get("text", "")
        profile = memory_store.get_user_profile(target_author)

        print(f"\n[Thoughtfully Replying to Feed Post by @{target_author}...]")
        print(f"  Post said: \"{user_text}\"")

        # 1. Pre-execution Safety: Check memory store
        if memory_store.has_replied_to_post(target_uri):
            print(f"  [SAFETY ABORT] Feed post {target_uri} already replied to in memory. Preventing duplicate comment.")
            executed = True
            result_details = {"status": "aborted_duplicate_feed_reply", "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Safety abort: already replied to feed post ({target_uri}).",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        # 2. Pre-execution Safety: Inspect live thread context
        thread_ctx = bsky_client.get_thread_context(target_uri)
        can_reply, block_reason = bsky_client.can_reply_to_thread(target_uri, thread_ctx)
        if not can_reply:
            print(f"  [SAFETY ABORT] {block_reason}. Aborting feed reply.")
            memory_store.mark_notification_handled(target_uri, target_post_uri=target_uri)
            executed = True
            result_details = {"status": "aborted_thread_safety", "reason": block_reason, "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Safety abort: {block_reason}.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        reply_text, model_used = generator.generate_reply(target_author, user_text, thread_ctx, profile, context)
        print(f"  Draft Reply ({model_used}): \"{reply_text}\"")

        if not reply_text or model_used in ("failed", "fallback"):
            print(f"  [RESTRAINT ABORT] Could not formulate authentic contextual reply to feed. Remaining silent.")
            executed = True
            result_details = {"status": "aborted_generation_failed", "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Restraint abort: could not formulate authentic contextual reply to @{target_author}'s post.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        record = post.get("record", {})
        reply_meta = record.get("reply", {})
        root_uri = reply_meta.get("root", {}).get("uri", target_uri) if reply_meta else target_uri
        root_cid = reply_meta.get("root", {}).get("cid", target_cid) if reply_meta else target_cid

        res = bsky_client.publish_reply(reply_text, target_uri, target_cid, root_uri, root_cid)
        if res.get("uri"):
            print(f"  [SUCCESS] Published Feed Reply: {res.get('uri')}")
            if not is_dry:
                memory_store.record_user_interaction(target_author, user_text, reply_text, "reply", did=post.get("author", {}).get("did", ""))
                memory_store.record_recent_reply(
                    target_handle=target_author,
                    user_text=user_text,
                    reply_text=reply_text,
                    uri=res.get("uri", ""),
                    target_uri=target_uri,
                    root_uri=root_uri,
                    notification_uri=target_uri
                )
                from .continuity import learn_interaction
                learn_interaction(res["uri"], user_text, reply_text, profile.did or target_author)
                narrative_engine.detect_and_manage_loops(
                    partner_identifier=post.get("author", {}).get("did", target_author),
                    partner_handle=target_author,
                    inbound_text=user_text,
                    reply_text=reply_text,
                    dry_run=is_dry,
                )
            executed = True
            result_details = {"reply_uri": res.get("uri"), "reply_text": reply_text}

    elif outcome.selected_action == ActionType.QUOTE_POST:
        post = outcome.target_data.get("post", {})
        target_author = post.get("author", {}).get("handle", "user")
        target_uri = post.get("uri", "")
        target_cid = post.get("cid", "")
        user_text = post.get("record", {}).get("text", "")
        print(f"\n[Quote-Posting Thought by @{target_author}...]")
        print(f"  Quoted Post: \"{user_text}\"")

        quote_comment, model_used = generator.generate_quote_post(target_author, user_text, context)
        print(f"  Draft Quote ({model_used}): \"{quote_comment}\"")

        if not quote_comment or model_used in ("failed", "fallback"):
            print(f"  [RESTRAINT ABORT] Could not formulate authentic quote commentary. Remaining silent.")
            executed = True
            result_details = {"status": "aborted_generation_failed", "target_uri": target_uri}
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            log_tick({
                "ts": now_iso,
                "seoul_time": context.seoul_time_display,
                "action": "NO_ACTION",
                "reason": f"Restraint abort: could not formulate authentic quote commentary on @{target_author}.",
                "dry_run": is_dry,
                "executed": True,
                "details": result_details,
                "budget": budget_manager.get_summary(),
            })
            return 0

        res = bsky_client.quote_post(quote_comment, target_uri, target_cid)
        if res.get("uri"):
            print(f"  [SUCCESS] Published Quote Post: {res.get('uri')}")
            if not is_dry:
                memory_store.record_recent_post(quote_comment, topic="quote_post", post_id=res.get("uri", ""))
            executed = True
            result_details = {"uri": res.get("uri"), "text": quote_comment, "target_uri": target_uri}

    elif outcome.selected_action == ActionType.REPOST:
        post = outcome.target_data.get("post", {})
        post_uri = post.get("uri", "")
        post_cid = post.get("cid", "")
        author = post.get("author", {}).get("handle", "")
        print(f"\n[Reposting Post by @{author}...]")
        if not is_dry:
            res = bsky_client.repost(post_uri, post_cid)
            print("  [SUCCESS] Repost confirmed." if res.get("uri") else "  [ERROR] Repost not confirmed.")
        else:
            print(f"  [DRY-RUN] Would repost: {post_uri}")
        executed = is_dry or bool(res.get("uri"))
        result_details = {"reposted_post": post_uri}

    elif outcome.selected_action == ActionType.FOLLOW:
        subject_did = outcome.target_data.get("did", "")
        handle = outcome.target_data.get("handle", "")
        print(f"\n[Following User @{handle} ({subject_did})...]")
        if not is_dry:
            res = bsky_client.follow(subject_did)
            print("  [SUCCESS] Follow confirmed." if res.get("uri") else "  [ERROR] Follow not confirmed.")
        else:
            print(f"  [DRY-RUN] Would follow: @{handle}")
        executed = is_dry or bool(res.get("uri"))
        result_details = {"followed_did": subject_did}

    # 8. Record Tick History & Observability
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    log_tick({
        "ts": now_iso,
        "seoul_time": context.seoul_time_display,
        "action": outcome.selected_action.value,
        "reason": outcome.reason,
        "dry_run": is_dry,
        "executed": executed,
        "details": result_details,
        "budget": budget_manager.get_summary(),
    })

    if executed and not is_dry:
        try:
            from .state_manager import state_manager
            state_manager.consume_interaction(outcome.selected_action.value)
        except Exception:
            pass

    print("\n[Budget & Resource Status]")
    summary = budget_manager.get_summary()
    print(f"  Daily Spend:   ${summary['daily_spend_usd']:.3f} / ${summary['daily_budget_usd']:.2f}")
    print(f"  Images Today:  {summary['daily_images_count']} / {summary['max_daily_images']}")

    # 9. End-of-Day Evening Check-in & Catch-up to My Master
    notifier.check_and_send_evening_summary(context, dry_run=is_dry)

    # 10. Persist Encrypted Private Vault
    if not is_dry:
        vault.save_vault()
        from .delivery import checkpoint
        checkpoint()
    print("=" * 65 + "\n")
    return 0 if executed else 1


def show_status() -> int:
    print_header("SEO-YEON HAN — AUTONOMOUS AGENT DASHBOARD")
    now_kst = get_seoul_datetime()
    context = build_environment_context()

    print(f"Current Seoul Time: {context.seoul_time_display} ({context.day_of_week}, {context.circadian_phase})")
    print(f"Current Weather:    {context.weather.summary()}")
    print(f"Current Season:     {context.season}")

    print("\n[Activity Metrics]")
    posts_today, replies_today, dms_today, likes_today = memory_store.get_activity_counts_today()
    print(f"  Posts Today:    {posts_today} / {config.max_posts_per_day}")
    print(f"  Replies Today:  {replies_today} / {config.max_replies_per_day}")
    print(f"  DMs Today:      {dms_today} / {config.max_dms_per_day}")
    print(f"  Likes Today:    {likes_today} / {config.max_likes_per_day}")
    print(f"  Last Post:      {memory_store.get_hours_since_last_post():.1f} hours ago")
    print(f"  Last Action:    {memory_store.get_hours_since_last_action():.1f} hours ago")

    print("\n[Budget Ledger]")
    summary = budget_manager.get_summary()
    print(f"  Daily Spend:    ${summary['daily_spend_usd']:.3f} / ${summary['daily_budget_usd']:.2f}")
    print(f"  Monthly Spend:  ${summary['monthly_spend_usd']:.3f} / ${summary['monthly_budget_usd']:.2f}")
    print(f"  Images Today:   {summary['daily_images_count']} / {summary['max_daily_images']}")

    print("\n[Cognitive State & Energy]")
    try:
        from .state_manager import state_manager
        st = state_manager.get_state()
        print(f"  Social Battery:      {int(st.social_battery * 100)}%")
        print(f"  Physical Fatigue:    {int(st.physical_fatigue * 100)}%")
        print(f"  Financial Awareness: {int(st.financial_awareness * 100)}%")
        print(f"  Creative Drive:      {int(st.creative_drive * 100)}%")
        print(f"  Internal Mood:       '{st.mood_descriptor}'")
        print(f"  Last Consolidation:  {st.last_consolidation_date or 'none'}")
        print(f"  Last Daily Report:   {memory_store.get_last_daily_report_date() or 'none'}")
    except Exception as e:
        print(f"  (Failed to load state: {e})")

    print("\n[Memory Summary]")
    ident = memory_store.get_identity()
    opinions = memory_store.get_opinions()
    recent = memory_store.get_recent_context()
    print(f"  Identity:       {ident['name_en']} ({ident['name_ko']}), age {ident['age_stated']}")
    print(f"  Opinions:       {len(opinions)} established topic stances")
    print(f"  Recent Posts:   {len(recent.get('posts', []))} tracked for repetition defense")

    print("\n[Active Goals & Pursuits]")
    active_goals = goal_manager.get_active_goals()
    if active_goals:
        for g in active_goals:
            metrics_str = f" ({g.metrics})" if g.metrics else ""
            print(f"  - [{g.category}] {g.title} [{g.status}]{metrics_str}")
    else:
        print("  No active goals.")

    print("\n[Legacy narrative records — not verified current activity]")
    arcs = narrative_engine.get_active_narrative_arcs()
    if arcs:
        for a in arcs:
            print(f"  - {a.title}: {a.summary[:65]}...")
    else:
        print("  No active narrative arcs.")

    print("\n[Offline snapshot: credentials intentionally not loaded]")
    print(f"  Bluesky Handle:    {config.bsky_handle}")
    print(f"  App Password:      {'Configured' if config.bsky_app_password else 'MISSING'}")
    print(f"  Kie API Key:       {'Configured' if config.kie_api_key else 'Missing'}")
    print(f"  OpenRouter Key:    {'Configured' if config.openrouter_api_key else 'Missing'} (Exclusive Text Provider)")
    print(f"  Primary Model:     {config.primary_text_model}")
    print(f"  Fallback Model:    {config.fallback_text_model}")
    print(f"  Human / Master:    my master ({config.master_telegram_handle})")
    print(f"  Telegram Bot:      {'Configured' if config.telegram_bot_token else 'Token Unset (Outbox Active)'}")
    print(f"  Emergency Stop:    {'ACTIVE' if config.emergency_stop else 'OFF'}")

    print("=" * 65 + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Seo-yeon Han Autonomous Bluesky Agent Runner")
    parser.add_argument("--auto", action="store_true", help="Execute single autonomous cognitive tick")
    parser.add_argument("--dry-run", action="store_true", help="Simulate tick without publishing any live content")
    parser.add_argument("--status", action="store_true", help="Display agent metrics, memory stats, and environment context")
    parser.add_argument("--force-action", type=str, help="Force a specific ActionType (e.g. PUBLISH_TEXT_POST, NO_ACTION)")
    parser.add_argument("--ask-master", type=str, help="Send a direct Telegram question/inquiry to my master")
    parser.add_argument("--check-master", action="store_true", help="Poll and reply to incoming Telegram messages from my master")
    parser.add_argument("--consolidate", action="store_true", help="Run nightly memory consolidation and private journal pass")
    parser.add_argument("--daily-summary", action="store_true", help="Generate and send Telegram check-in to my master")
    parser.add_argument("--plan-week", action="store_true", help="Display or generate Seo-yeon's 7-day weekly life itinerary")
    parser.add_argument("--force-plan", action="store_true", help="Force regenerate fresh 7-day weekly itinerary with LLM")
    parser.add_argument("--preview", action="store_true", help="Paid provider preview in isolated state; never publish")
    parser.add_argument("--replay", type=str, help="Offline observation fixture JSON")
    parser.add_argument("--date", type=str, help="Target date for daily summary (YYYY-MM-DD)")
    args = parser.parse_args()
    if args.replay:
        os.environ["SEOYEON_REPLAY_FILE"] = args.replay
        args.dry_run = True
    if args.preview:
        args.dry_run = True

    if args.plan_week or args.force_plan:
        from .weekly_planner import weekly_planner
        now_kst = get_seoul_datetime()
        schedule_data = weekly_planner.get_or_create_schedule(now_kst=now_kst, force=args.force_plan)
        print("\n" + weekly_planner.format_schedule_summary(schedule_data))
        current_act = weekly_planner.get_current_activity(now_kst)
        print(f"\n[Current Rhythm Right Now ({now_kst.strftime('%H:%M KST')})]")
        print(f"  Day:      {current_act.get('day', '').capitalize()}")
        print(f"  Phase:    {current_act.get('phase', '').replace('_', ' ').capitalize()}")
        print(f"  Activity: {current_act.get('activity', '')}")
        print(f"  Area:     {current_act.get('area', '')}")
        print(f"  Vibe:     {current_act.get('vibe', '')}\n")
        return 0

    if args.status:
        return show_status()

    if args.check_master:
        context = build_environment_context()
        print(f"\n[Checking inbound messages from my master ({config.master_telegram_handle})...]")
        count = notifier.process_master_inbox(context, dry_run=args.dry_run)
        print(f"Processed {count} new message(s) from my master.")
        return 0

    if args.consolidate:
        from .vault import vault
        if vault.enc_file.exists():
            if not vault.load_vault():
                print("[CRITICAL] Existing encrypted vault (vault.enc) could not be decrypted.")
                print("Stopping consolidation safely to prevent data loss.")
                return 1
        else:
            vault.load_vault()
        context = build_environment_context()
        from .consolidator import consolidator
        res = consolidator.consolidate(context, dry_run=args.dry_run, force=True)
        if not vault._load_failed:
            vault.save_vault()
        return 0 if res.get("status") in ("success", "already_consolidated") else 1

    if args.ask_master:
        print(f"\n[Sending Telegram message to my master ({config.master_telegram_handle})...]")
        success = notifier.ask_master(args.ask_master, context="Direct CLI request", dry_run=args.dry_run)
        if success:
            print("  Message sent / queued successfully.")
            return 0
        else:
            print("  Failed to deliver Telegram message.")
            return 1

    if args.daily_summary:
        context = build_environment_context()
        now_kst = get_seoul_datetime()

        if args.date:
            try:
                target_date = dt.date.fromisoformat(args.date)
            except Exception:
                print(f"[ERROR] Invalid date format: {args.date}. Expected YYYY-MM-DD.")
                return 1
            target_str = target_date.strftime("%Y-%m-%d")
            summary_data = memory_store.get_daily_activity_summary(target_date)
            is_catchup = target_date < now_kst.date()
            print(f"\n[Generating Daily Summary for {target_str} ({'catchup' if is_catchup else 'interim'})...]")
            report_text, model = generator.generate_daily_report(summary_data, context, is_catchup=is_catchup)
            print(f"  Model: {model}\n\n{report_text}\n")
            sent = notifier.send_daily_summary(report_text, summary_data, dry_run=args.dry_run)
            if sent and not args.dry_run:
                memory_store.set_last_daily_report_date(target_str)
                print(f"  Delivered and recorded for {target_str}.")
            return 0

        # General daily summary call: handles catch-up or today
        sent_catchup = notifier.check_and_send_evening_summary(context, dry_run=args.dry_run)
        if not sent_catchup:
            # If nothing was automatically triggered (e.g. today < 21:00 and yesterday was already recorded),
            # but user explicitly requested --daily-summary, generate today's interim summary
            today_str = now_kst.strftime("%Y-%m-%d")
            summary_data = memory_store.get_daily_activity_summary(now_kst.date())
            print(f"\n[Generating Interim Daily Summary for {today_str} ({context.seoul_time_display})...]")
            report_text, model = generator.generate_daily_report(summary_data, context, is_catchup=False)
            print(f"  Model: {model}\n\n{report_text}\n")
            sent = notifier.send_daily_summary(report_text, summary_data, dry_run=args.dry_run)
            if sent and not args.dry_run:
                memory_store.set_last_daily_report_date(today_str)
                print(f"  Delivered and recorded for {today_str}.")
        return 0

    if args.auto or args.dry_run or args.force_action:
        return run_tick(dry_run=args.dry_run, force_action=args.force_action)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
