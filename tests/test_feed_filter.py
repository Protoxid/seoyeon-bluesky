import unittest

from agent.validator import ContentValidator


class TestFeedFilterBreadth(unittest.TestCase):
    def eligible(self, text):
        return ContentValidator.filter_feed_post(text, "someone.bsky.social", langs=["ko", "en"])[0]

    def test_ordinary_posts_are_not_filtered(self):
        for text in (
            "정당한 요구였는데 거절당함",               # 정당 as "justified"
            "청년 월세 정부지원 신청 드디어 함",          # housing support
            "a little collaboration with my sister on this zine",
            "our club president brought snacks",
            "saving for a reformer is my only investment this year",
        ):
            with self.subTest(text=text):
                self.assertTrue(self.eligible(text))

    def test_spam_scams_adult_and_electoral_politics_still_filtered(self):
        for text in (
            "free crypto airdrop, dm me",
            "18+ content here",
            "election day thoughts",
            "대통령 탄핵 속보",
        ):
            with self.subTest(text=text):
                self.assertFalse(self.eligible(text))


if __name__ == "__main__":
    unittest.main()

