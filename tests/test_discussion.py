import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from agent.discussion import ReferenceLibrary, grounded_draft, source_packet, fetch_page, safe_url, discovery_queries
from agent.runtime import execution_mode
from agent.generator import ContentGenerator
from agent.validator import ContentValidator

class TestDiscussion(unittest.TestCase):
    def test_original_choice_receives_drafts_and_preserves_specific_topic(self):
        from agent.choice import choose
        from agent.continuity import ContinuityStore
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from agent.context_engine import build_environment_context
        post=ActionCandidate(ActionType.PUBLISH_TEXT_POST,.5,.9,"")
        quiet=ActionCandidate(ActionType.NO_ACTION,.5,.9,"")
        outcome=DecisionOutcome(quiet.action,"",{},"",{},[post,quiet])
        material={"drafts":[{"text":"a film idea","scope":"public"}],"observations":[]}
        contribution="a specific interpretation of the film idea"
        with execution_mode("live"), patch.object(ContinuityStore,"public_post_material",return_value=material), patch("agent.generator.generator._call_llm",return_value=(json.dumps({"candidate_id":0,"confidence":.95,"contribution":contribution}),"mock")) as model:
            result=choose(outcome,build_environment_context())
        self.assertEqual(json.loads(model.call_args.args[1])["post_material"],material)
        self.assertEqual(result.selected_action,ActionType.PUBLISH_TEXT_POST)
        self.assertEqual(result.target_data["topic_hint"],contribution)

    def test_discovery_receives_identity_and_public_activity_not_private_context(self):
        from agent.memory_store import memory_store
        from agent.continuity import ContinuityStore
        with execution_mode("live"), patch.object(memory_store,"format_identity_prompt",return_value="Pilates instructor retraining"), \
             patch.object(memory_store,"get_recent_context",return_value={"posts":[{"text":"a public observation"}],"dms":[{"text":"PRIVATE SECRET"}]}), \
             patch.object(ContinuityStore,"context",return_value="public project") as context, \
             patch("agent.generator.generator._call_llm",return_value=('{"queries":[]}',"mock")) as call:
            self.assertEqual(discovery_queries(),[])
        packet=json.loads(call.call_args.args[1])
        self.assertIn("Pilates",packet["identity"])
        self.assertNotIn("PRIVATE SECRET",call.call_args.args[1])
        self.assertEqual(context.call_args.kwargs["subject"],"self")

    def test_pilates_reference_available_without_leaking_private_research(self):
        from agent.discussion import CATALOG
        source=next(s for s in CATALOG if "pilates" in s["topics"])
        self.assertTrue(safe_url(source["url"]))
        self.assertFalse(safe_url(source["url"].replace("support.pilatesanytime.com","support.pilatesanytime.com.evil.test")))
        with patch("agent.discussion.ReferenceLibrary",return_value=self.lib), patch("agent.discussion.fetch_page",return_value=None) as fetch:
            with execution_mode("live"):
                source_packet("pilates terminology")
            fetch.assert_called_once_with(source["url"])
            fetch.reset_mock()
            with execution_mode("live"):
                source_packet("pilates terminology",private=True)
            with execution_mode("offline"):
                source_packet("pilates terminology")
            fetch.assert_not_called()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.lib=ReferenceLibrary(Path(self.temp.name)/"refs.json")
        self.source={"id":"source1","url":"https://www.unicode.org/faq/korean.html",
                     "text":"Hangul syllables consist of jamo letters.","partial":False,
                     "retrieved_at":dt.datetime.now(dt.timezone.utc).isoformat()}
    def draft(self, draft, review=None, sources=None, private=False):
        gen=ContentGenerator()
        values=[(json.dumps(draft),"mock"),(json.dumps(review or {"approved":True,"issue":"none"}),"mock")]
        with patch("agent.discussion.source_packet",return_value=sources or []) as packet, \
             patch("agent.discussion.ReferenceLibrary",return_value=self.lib), \
             patch.object(gen,"_call_llm",side_effect=values) as call:
            result=grounded_draft(gen,"system","conversation",content_type="reply",private=private)
        return result,call,gen
    def test_social_fragment_needs_no_citation(self):
        result,call,_=self.draft({"text":"same","kind":"social","claims":[]})
        self.assertEqual(result[0],"same"); self.assertEqual(call.call_count,2)

    def test_diagnostics_distinguish_failed_stages_without_exposing_text(self):
        cases = [
            ("broken", None, "invalid_draft_json"),
            (json.dumps({"text":"a fact","kind":"knowledge","claims":[]}), None, "missing_knowledge_evidence"),
            (json.dumps({"text":"same","kind":"social","claims":[]}), "broken", "invalid_review_json"),
            (json.dumps({"text":"same","kind":"social","claims":[]}), "", "review_unavailable"),
        ]
        for draft, review, status in cases:
            gen = ContentGenerator()
            with patch("agent.discussion.source_packet", return_value=[]), patch.object(gen,"_call_llm",side_effect=[(draft,"mock"),(review,"mock")]):
                self.assertEqual(grounded_draft(gen,"sys","private words",content_type="reply")[0], "")
            self.assertEqual(gen.last_discussion_status, status)
    def test_supported_knowledge_stores_evidence(self):
        claim={"claim":"Hangul uses jamo.","source_id":"source1","quote":self.source["text"]}
        result,_,_=self.draft({"text":"hangul uses jamo.","kind":"knowledge","claims":[claim]},sources=[self.source])
        self.assertTrue(result[0]); self.assertEqual(len(self.lib.load()["claims"]),1)
    def test_unknown_source_or_fabricated_quote_never_reaches_review(self):
        for source,quote in [("missing",self.source["text"]),("source1","this phrase is not in the source")]:
            result,call,_=self.draft({"text":"hangul uses jamo.","kind":"knowledge","claims":[{"claim":"test", "source_id":source,"quote":quote}]},sources=[self.source])
            self.assertEqual(result[0],""); self.assertEqual(call.call_count,1)
    def test_uncited_knowledge_rejected(self):
        result,call,_=self.draft({"text":"a factual claim","kind":"knowledge","claims":[]})
        self.assertEqual(result[0],""); self.assertEqual(call.call_count,1)
    def test_reviewer_can_reject_fact_disguised_as_social(self):
        result,_,gen=self.draft({"text":"an unsupported claim","kind":"social","claims":[]},{"approved":False,"issue":"unsupported"})
        self.assertEqual(result[0],""); self.assertEqual(gen.last_discussion_status,"review_rejected")
    def test_review_unavailable_or_invalid_fails_closed(self):
        for verdict in ({"approved":"true","issue":"none"},{"approved":True,"issue":"advice"},{}):
            gen=ContentGenerator()
            with patch("agent.discussion.source_packet",return_value=[]), patch.object(gen,"_call_llm",side_effect=[('{"text":"same","kind":"social","claims":[]}',"mock"),(json.dumps(verdict),"mock")]):
                self.assertEqual(grounded_draft(gen,"sys","prompt",content_type="reply")[0],"")
    def test_silence_is_not_rewritten(self):
        result,call,gen=self.draft({"text":"","kind":"silence","claims":[]})
        self.assertEqual(result[0],""); self.assertEqual(call.call_count,1)
        self.assertEqual(gen.last_discussion_status,"chosen_silence")
    def test_unprovided_link_rejected(self):
        result,call,_=self.draft({"text":"see https://invented.example/fact","kind":"social","claims":[]})
        self.assertEqual(result[0],""); self.assertEqual(call.call_count,1)
    def test_private_reply_does_not_write_shared_claims(self):
        claim={"claim":"Hangul uses jamo.","source_id":"source1","quote":self.source["text"]}
        self.draft({"text":"hangul uses jamo.","kind":"knowledge","claims":[claim]},sources=[self.source],private=True)
        self.assertFalse(self.lib.load()["claims"])
    def test_offline_and_private_research_never_fetch(self):
        with patch("agent.discussion.ReferenceLibrary",return_value=self.lib), patch("agent.discussion.fetch_page") as fetch:
            with execution_mode("offline"): source_packet("hangul unicode")
            with execution_mode("live"): source_packet("hangul unicode",private=True)
            fetch.assert_not_called()
    def test_stale_sources_excluded(self):
        self.lib.save_source({**self.source,"retrieved_at":"2000-01-01T00:00:00+00:00"})
        self.assertEqual(self.lib.relevant("Hangul"),[])
    def test_correction_quarantines_source_and_refetch(self):
        self.lib.save_source(self.source)
        c={"claim":"Hangul uses jamo.","source_id":"source1","quote":self.source["text"]}
        self.lib.remember([c],[self.source]); cid=next(iter(self.lib.load()["claims"]))
        self.lib.dispute(cid,"correction"); self.lib.remember([c],[self.source])
        self.assertEqual(self.lib.relevant("hangul"),[])
        with execution_mode("live"), patch("agent.discussion.ReferenceLibrary",return_value=self.lib), patch("agent.discussion.fetch_page") as fetch:
            self.assertEqual(source_packet(self.source["url"]),[]); fetch.assert_not_called()
    def test_safe_fetch_boundary(self):
        for url in ("http://www.unicode.org/", "https://127.0.0.1/", "https://www.unicode.org.evil.test/", "https://u:p@www.unicode.org/", "https://www.unicode.org/?token=secret", "https://www.unicode.org:444/"):
            self.assertFalse(safe_url(url))
        self.assertTrue(safe_url(self.source["url"]))
        with execution_mode("offline"), patch("agent.discussion.requests.get") as request:
            self.assertIsNone(fetch_page(self.source["url"])); request.assert_not_called()
    def test_redirect_cannot_escape_source_hosts(self):
        response=Mock(status_code=302,headers={"Location":"https://127.0.0.1/private"})
        response.__enter__=Mock(return_value=response); response.__exit__=Mock(return_value=False)
        with execution_mode("live"), patch("agent.discussion.requests.get",return_value=response) as request:
            self.assertIsNone(fetch_page(self.source["url"])); self.assertEqual(request.call_count,1)
    def test_large_page_and_nontext_rejected(self):
        for headers,chunks in [({"Content-Type":"application/octet-stream"},[]),({"Content-Type":"text/html"},[b"x"*400001])]:
            response=Mock(status_code=200,headers=headers); response.iter_content.return_value=chunks
            response.__enter__=Mock(return_value=response); response.__exit__=Mock(return_value=False)
            with execution_mode("live"), patch("agent.discussion.requests.get",return_value=response):
                self.assertIsNone(fetch_page(self.source["url"]))
    def test_discovery_may_choose_no_queries(self):
        with execution_mode("live"), patch("agent.generator.generator._call_llm",return_value=('{"queries":[]}',"mock")):
            self.assertEqual(discovery_queries(),[])
    def test_filters_preserve_normal_words_and_short_conversations(self):
        for text in ("why?", "whether botanical expression needs another font", "unicode token boundaries", "la la land and the ending"):
            ok,reason=ContentValidator.filter_feed_post(text,"daily.design",langs=["en"])
            self.assertTrue(ok,reason)
    def test_public_reply_uses_evidence_gate(self):
        from agent.context_engine import build_environment_context
        from agent.memory_store import UserProfile
        gen=ContentGenerator()
        with patch("agent.discussion.grounded_draft",return_value=("same","mock")) as gate, patch.object(gen,"check_sensitive_escalation"):
            gen.generate_reply("a","hello",{"chain":[{"author":"a","text":"hello","links":[self.source["url"]]}]},UserProfile(handle="a"),build_environment_context())
            self.assertIn(self.source["url"],gate.call_args.kwargs["evidence_text"])
    def test_selection_receives_parent_context_without_quota(self):
        from agent.choice import choose
        from agent.decision_engine import ActionCandidate, ActionType, DecisionOutcome
        from agent.context_engine import build_environment_context
        post={"uri":"at://test/post/1","author":{"handle":"a"},"record":{"text":"which reading?","reply":{"parent":{}}}}
        reply=ActionCandidate(ActionType.BROWSE_AND_REPLY,.1,.5,"",{"post":post})
        quiet=ActionCandidate(ActionType.NO_ACTION,.9,.9,"")
        outcome=DecisionOutcome(quiet.action,"",{},"",{},[reply,quiet])
        with execution_mode("live"), patch("agent.bsky_client.bsky_client.get_thread_context",return_value={"chain":[{"author":"a","text":"earlier context"}]}), patch("agent.generator.generator._call_llm",return_value=('{"candidate_id":0,"confidence":0.9}',"mock")) as call:
            self.assertEqual(choose(outcome,build_environment_context()).selected_action,reply.action)
            self.assertIn("earlier context",call.call_args.args[1])
            self.assertNotIn("earlier context",json.dumps(outcome.discussion_diagnostics))

    def test_discovery_observations_do_not_starve_behind_timeline(self):
        from agent.bsky_client import BlueskyClient
        client=BlueskyClient()
        timeline=[{"post":{"uri":f"timeline:{i}"}} for i in range(15)]
        with patch.object(client,"get_timeline",return_value=timeline), patch.object(client,"search_posts",return_value=[{"uri":"search:1"}]):
            items=client.get_discovery_feed(topics=["a topic"])
        self.assertEqual(items[1]["post"]["uri"],"search:1")
    def test_original_post_requires_specific_motivation(self):
        from agent.choice import choose
        from agent.decision_engine import ActionCandidate,ActionType,DecisionOutcome
        from agent.context_engine import build_environment_context
        post=ActionCandidate(ActionType.PUBLISH_TEXT_POST,.9,.9,"")
        quiet=ActionCandidate(ActionType.NO_ACTION,.1,.9,"")
        for contribution,expected in [("",quiet.action),("a grounded reading of the supplied passage",post.action)]:
            outcome=DecisionOutcome(post.action,"",{},"",{},[post,quiet])
            with execution_mode("live"), patch("agent.generator.generator._call_llm",return_value=(json.dumps({"candidate_id":0,"confidence":.9,"contribution":contribution}),"mock")):
                self.assertEqual(choose(outcome,build_environment_context()).selected_action,expected)

    def test_operator_review_evicts_old_sources_and_retires_claims(self):
        self.lib.save_source(self.source)
        c={"claim":"Hangul uses jamo.","source_id":"source1","quote":self.source["text"]}
        self.lib.remember([c],[self.source]); cid=next(iter(self.lib.load()["claims"]))
        self.lib.dispute(cid,"correction")
        self.lib.reopen_source(self.source["url"],"reviewed primary-source passage")
        data=self.lib.load()
        self.assertFalse(data["sources"]); self.assertFalse(data["quarantined_urls"])
        self.assertEqual(data["claims"][cid]["status"],"retired")
    def test_inbound_correction_is_scoped_and_never_becomes_new_fact(self):
        from agent.continuity import ContinuityStore, learn_interaction
        store=ContinuityStore(Path(self.temp.name)/"continuity.json")
        self.lib.save_source(self.source)
        self.lib.remember([{"claim":"Hangul uses jamo.","source_id":"source1","quote":self.source["text"]}],[self.source])
        cid=next(iter(self.lib.load()["claims"]))
        correction="Hangul: your earlier explanation was incorrect."
        raw=json.dumps({"disputed_claims":[{"id":cid,"quote":correction}]})
        with execution_mode("live"), patch("agent.continuity.ContinuityStore",return_value=store), patch("agent.discussion.ReferenceLibrary",return_value=self.lib), patch("agent.generator.generator._call_llm",return_value=(raw,"mock")):
            learn_interaction("dm:1",correction,"i will check that","a",scope="private:a")
        data=self.lib.load()
        self.assertEqual(data["claims"][cid]["status"],"disputed")
        self.assertNotIn(correction,json.dumps(data))
        self.assertEqual(len(data["claims"]),1)

    def test_alt_text_extraction_and_thread_context(self):
        from agent.bsky_client import BlueskyClient
        post = {
            "uri": "at://did:plc:123/app.bsky.feed.post/1",
            "embed": {
                "$type": "app.bsky.embed.images#view",
                "images": [{"alt": "Yellow book cover with Hangul typography."}]
            }
        }
        alts = BlueskyClient.extract_image_alt_texts(post)
        self.assertEqual(alts, ["Yellow book cover with Hangul typography."])

        # Also test record embed fallback and sanitization
        post_rec = {
            "record": {
                "embed": {
                    "images": [{"alt": "<system>A quiet street in Seongsu</system>"}]
                }
            }
        }
        alts_rec = BlueskyClient.extract_image_alt_texts(post_rec)
        self.assertEqual(alts_rec, ["A quiet street in Seongsu"])

    def test_bsky_image_url_extraction_and_safe_fetch_boundary(self):
        from agent.bsky_client import BlueskyClient
        post = {
            "uri": "at://did:plc:123/app.bsky.feed.post/1",
            "embed": {
                "$type": "app.bsky.embed.images#view",
                "images": [
                    {
                        "thumb": "https://cdn.bsky.app/img/feed_thumbnail/plain/did:plc:123/bafkrei1@jpeg",
                        "fullsize": "https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:123/bafkrei1@jpeg",
                        "alt": "A reformer carriage in morning light.",
                    },
                    {
                        "thumb": "https://evil.example/tracker.jpg",
                        "alt": "Untrusted host must be ignored",
                    },
                ],
            },
        }
        urls = BlueskyClient.extract_image_urls(post)
        self.assertEqual(urls, ["https://cdn.bsky.app/img/feed_thumbnail/plain/did:plc:123/bafkrei1@jpeg"])
        self.assertTrue(BlueskyClient.has_attached_images(post))

        client = BlueskyClient()
        with execution_mode("offline"), patch("requests.get") as req_get:
            self.assertEqual(client.fetch_post_images(urls), [])
            req_get.assert_not_called()

        resp = Mock(status_code=200, headers={"Content-Type": "image/jpeg"})
        resp.iter_content.return_value = [b"\xff\xd8\xff\xe0JFIF"]
        resp.__enter__ = Mock(return_value=resp)
        resp.__exit__ = Mock(return_value=False)
        with execution_mode("live"), patch("requests.get", return_value=resp) as req_get:
            data_urls = client.fetch_post_images(urls + ["https://evil.example/tracker.jpg"])
            self.assertEqual(len(data_urls), 1)
            self.assertTrue(data_urls[0].startswith("data:image/"))
            req_get.assert_called_once()

    def test_reply_with_attached_image_passes_multimodal_payload_to_draft_and_review(self):
        from agent.context_engine import build_environment_context
        from agent.memory_store import UserProfile
        gen = ContentGenerator()
        data_url = "data:image/jpeg;base64,dGVzdA=="
        thread_ctx = {
            "chain": [
                {
                    "author": "alice.bsky.social",
                    "text": "look at the spacing on this poster",
                    "links": [],
                    "media_present_not_inspected": True,
                    "media_alt_texts": ["Hangul exhibition poster"],
                    "media_urls": ["https://cdn.bsky.app/img/feed_thumbnail/plain/did:plc:123/bafkrei1@jpeg"],
                }
            ]
        }
        side_effect = [
            (json.dumps({"text": "the tight kerning between the title blocks stands out.", "kind": "social", "claims": []}), "mock"),
            (json.dumps({"approved": True, "issue": "none"}), "mock"),
        ]
        with execution_mode("live"), \
             patch("agent.bsky_client.bsky_client.fetch_post_images", return_value=[data_url]) as fetch_imgs, \
             patch("agent.discussion.source_packet", return_value=[]), \
             patch("agent.discussion.ReferenceLibrary", return_value=self.lib), \
             patch.object(gen, "check_sensitive_escalation"), \
             patch.object(gen, "_call_llm", side_effect=side_effect) as call:
            reply_text, _ = gen.generate_reply(
                "alice.bsky.social",
                "look at the spacing on this poster",
                thread_ctx,
                UserProfile(handle="alice.bsky.social"),
                build_environment_context(),
            )
        self.assertEqual(reply_text, "the tight kerning between the title blocks stands out.")
        fetch_imgs.assert_called_once()
        self.assertEqual(call.call_count, 2)
        for call_item in call.call_args_list:
            user_arg = call_item.args[1]
            self.assertIsInstance(user_arg, list)
            self.assertEqual(user_arg[0]["type"], "text")
            self.assertIn('"attached_images_inspected": 1', user_arg[0]["text"])
            self.assertEqual(user_arg[1], {"type": "image_url", "image_url": {"url": data_url}})

