"""
tests/test_goal_manager.py — Unit Tests for GoalManager & Pursuit Engine.

Verifies:
  1. Goal creation, activation, progress, pausing, and completion lifecycles.
  2. Persistence to active_goals.json and state recovery across instances.
  3. Strict anti-cliché quota: prevents pilates/coffee goals from exceeding 10%.
  4. Prompt context generation for LLM grounding.
  5. Automatic keyword activity detection advancing active goals.
"""

import json
import pathlib
import shutil
import tempfile
import unittest

from agent.goal_manager import (
    Goal,
    GoalCategory,
    GoalManager,
    GoalPriority,
    GoalStatus,
)


class TestGoalManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp())
        self.goals_file = self.test_dir / "active_goals.json"
        self.manager = GoalManager(storage_file=self.goals_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initial_seed_goals_loaded(self):
        """Verifies initial seed goals are loaded automatically."""
        goals = self.manager.get_all_goals()
        self.assertGreaterEqual(len(goals), 3)
        active_goals = self.manager.get_active_goals()
        self.assertTrue(any(g.goal_id == "g_novel_han_kang_202610" for g in active_goals))

    def test_propose_and_activate_goal(self):
        """Verifies proposing a new goal and activating it."""
        goal = self.manager.propose_goal(
            title="Translating French design interview",
            description="Working through a 4-page interview with an independent graphic designer.",
            category=GoalCategory.CULTURAL.value,
            priority=GoalPriority.MEDIUM.value,
        )
        self.assertIsNotNone(goal)
        self.assertEqual(goal.status, GoalStatus.PROPOSED.value)

        # Activate it
        success = self.manager.activate_goal(goal.goal_id)
        self.assertTrue(success)

        reloaded = self.manager.get_goal(goal.goal_id)
        self.assertEqual(reloaded.status, GoalStatus.ACTIVE.value)

    def test_record_progress_and_metrics_update(self):
        """Verifies progress events and metric updates persist."""
        goal = self.manager.propose_goal(
            title="Restoring wooden spice rack",
            description="Sanding and oiling a secondhand pine shelf.",
            category=GoalCategory.DOMESTIC.value,
            metrics={"step": 1, "total_steps": 4},
        )
        self.manager.activate_goal(goal.goal_id)

        # Record progress event
        self.manager.record_progress(
            goal_id=goal.goal_id,
            note="Finished fine-grit sanding. Ready for mineral oil coat.",
            event_type="progress",
            metrics_update={"step": 2, "percent": 50.0},
            post_uri="at://test/post/123",
        )

        updated = self.manager.get_goal(goal.goal_id)
        self.assertEqual(updated.status, GoalStatus.IN_PROGRESS.value)
        self.assertEqual(len(updated.progress_events), 1)
        self.assertEqual(updated.progress_events[0]["note"], "Finished fine-grit sanding. Ready for mineral oil coat.")
        self.assertEqual(updated.metrics["step"], 2)
        self.assertEqual(updated.metrics["percent"], 50.0)

    def test_complete_goal(self):
        """Verifies completing a goal marks it and records completion event."""
        goal_id = "g_novel_han_kang_202610"
        self.manager.complete_goal(goal_id, note="Finished the final chapter late at night.")

        completed = self.manager.get_goal(goal_id)
        self.assertEqual(completed.status, GoalStatus.COMPLETED.value)
        self.assertEqual(completed.completion_notes, "Finished the final chapter late at night.")
        # Completed goals should not appear in get_active_goals()
        active = self.manager.get_active_goals()
        self.assertFalse(any(g.goal_id == goal_id for g in active))

    def test_pause_and_abandon_goal(self):
        """Verifies pausing and abandoning goals."""
        goal = self.manager.propose_goal(
            title="Indoor mushroom kit",
            description="Trying to grow oyster mushrooms in the hallway.",
            category=GoalCategory.DOMESTIC.value,
        )
        self.manager.activate_goal(goal.goal_id)

        self.manager.pause_goal(goal.goal_id, reason="Apartment humidity too low.")
        self.assertEqual(self.manager.get_goal(goal.goal_id).status, GoalStatus.PAUSED.value)

        self.manager.abandon_goal(goal.goal_id, reason="Mold took over the substrate.")
        self.assertEqual(self.manager.get_goal(goal.goal_id).status, GoalStatus.ABANDONED.value)

    def test_anti_cliche_quota_enforcement(self):
        """Verifies pilates/coffee goals are rejected if they exceed 10% of total goals."""
        # Current seeded goals = 3 (none are pilates/coffee)
        # 1 pilates goal out of 4 total = 25% > 10% -> MUST be blocked!
        blocked = self.manager.propose_goal(
            title="Mastering new Pilates reformer ladder sequence",
            description="Pilates teaching practice for studio sessions.",
            category=GoalCategory.PERSONAL_CRAFT.value,
        )
        self.assertIsNone(blocked)

    def test_prompt_context_formatting(self):
        """Verifies formatted goals prompt is concise and contains active pursuits."""
        ctx = self.manager.get_goals_context_for_prompt()
        self.assertIn("Current ongoing personal pursuits", ctx)
        self.assertIn("Finishing Han Kang's 'We Do Not Part'", ctx)
        self.assertIn("kitchen ivy", ctx)

    def test_detect_and_record_goal_activity(self):
        """Verifies keywords in generated text automatically advance matching goals."""
        text = "spent forty minutes on line 2 reading three chapters of the han kang novel."
        advanced_ids = self.manager.detect_and_record_goal_activity(text, post_uri="at://test/post/999")
        self.assertIn("g_novel_han_kang_202610", advanced_ids)

        goal = self.manager.get_goal("g_novel_han_kang_202610")
        self.assertTrue(any("han kang novel" in ev.get("note", "") for ev in goal.progress_events))


if __name__ == "__main__":
    unittest.main()
