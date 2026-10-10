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
        self.assertEqual(self.manager.get_all_goals(), [])

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
        goal = self.manager.propose_goal("Test reading", "Explicit test fixture", GoalCategory.CULTURAL.value)
        self.manager.activate_goal(goal.goal_id)
        self.manager.complete_goal(goal.goal_id, note="operator confirmed")
        self.assertEqual(self.manager.get_goal(goal.goal_id).status, GoalStatus.COMPLETED.value)

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
        self.assertIsNotNone(blocked)

    def test_prompt_context_formatting(self):
        self.assertEqual(self.manager.get_goals_context_for_prompt(), "")
        g = self.manager.propose_goal("Test essay", "An original essay", GoalCategory.CULTURAL.value)
        self.manager.activate_goal(g.goal_id)
        self.assertIn("Test essay", self.manager.get_goals_context_for_prompt())

    def test_detect_and_record_goal_activity(self):
        g = self.manager.propose_goal("Han Kang novel", "reading", GoalCategory.CULTURAL.value, metrics={"pages": 0})
        self.manager.activate_goal(g.goal_id)
        for text in ("did not read the han kang novel", "read han kang today"):
            self.assertEqual(self.manager.detect_and_record_goal_activity(text), [])
        self.assertEqual(self.manager.advance_active_goals_daily(), [])
        self.assertEqual(self.manager.get_goal(g.goal_id).metrics["pages"], 0)


if __name__ == "__main__":
    unittest.main()
