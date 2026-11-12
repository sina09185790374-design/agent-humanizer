"""Tests for agent-humanizer. Run: python3 -m unittest discover -s tests"""

import json
import subprocess
import sys
import unittest

from agent_humanizer.humanize import check, detect_lang, humanize

EN_SLOPPY = (
    "Great question! In today's fast-paced world, Kubernetes liveness probes "
    "are a powerful mechanism that enables the kubelet to determine whether a "
    "container is healthy — and it's not just a health check, it's your first "
    "line of defense. Moreover, it is crucial to leverage this cutting-edge, "
    "seamless mechanism to unlock robust performance. However, it's important "
    "to note that misconfigured probes could potentially cause cascading restarts."
)

FA_SLOPPY = (
    "لازم به ذکر است که در دنیای امروز، این ابزار بی‌نظیر است و به طور کلی "
    "می‌تواند به شما کمک کند تا کارهای خود را به صورت فوق‌العاده انجام دهید."
)


class TestTells(unittest.TestCase):
    def test_en_opener_dropped(self):
        out, _, _ = humanize("It's important to note that the cache is full.")
        self.assertNotIn("important to note", out.lower())
        self.assertIn("cache is full", out)

    def test_en_fast_paced_world_dropped(self):
        out, _, _ = humanize("In today's fast-paced world, teams ship daily.")
        self.assertNotIn("fast-paced", out)
        self.assertIn("Teams ship daily", out)

    def test_en_verb_replaced(self):
        out, _, _ = humanize("We leverage this tool to facilitate work.")
        self.assertIn("use this tool", out)
        self.assertIn("help work", out)

    def test_en_great_question_dropped(self):
        out, _, _ = humanize("Great question! The answer is yes.")
        self.assertNotIn("great question", out.lower())

    def test_en_not_only_flattened(self):
        out, _, _ = humanize("It is not only fast but also cheap.")
        self.assertNotIn("not only", out)
        self.assertNotIn("but also", out)
        self.assertIn("fast", out)
        self.assertIn("cheap", out)

    def test_fa_opener_dropped(self):
        out, _, _ = humanize("لازم به ذکر است که قیمت‌ها تغییر کرده است.")
        self.assertNotIn("لازم به ذکر", out)
        self.assertIn("قیمت‌ها تغییر کرده است", out)

    def test_fa_superlative_softened(self):
        out, _, _ = humanize("این گوشی بی‌نظیر است.")
        self.assertNotIn("بی‌نظیر", out)
        self.assertIn("خوب است", out)

    def test_fa_digital_age_dropped(self):
        out, _, _ = humanize("در عصر دیجیتال، همه آنلاین هستند.")
        self.assertNotIn("عصر دیجیتال", out)
        self.assertIn("همه آنلاین هستند", out)


class TestRebuild(unittest.TestCase):
    def test_long_sentence_split(self):
        text = ("The probe checks the container every ten seconds and it restarts "
                "the container when the check fails because a stuck container "
                "blocks the whole service and nobody wants that on a Friday.")
        out, _, after = humanize(text)
        self.assertGreater(out.count("."), 1)
        self.assertEqual(after["long_sentences"], 0)

    def test_em_dash_becomes_sentence(self):
        out, _, _ = humanize("Probes are a health check — and they restart bad containers.")
        self.assertNotIn("—", out)
        self.assertGreater(out.count("."), 1)

    def test_passive_past_rewritten(self):
        out, _, _ = humanize("The report was written by Sara.")
        self.assertEqual(out, "Sara wrote the report.")

    def test_passive_irregular_rewritten(self):
        out, _, _ = humanize("The house was built by the team.")
        self.assertEqual(out, "The team built the house.")

    def test_passive_present_singular_left_alone(self):
        # Ambiguous 3rd-person -s: flagged in the report, not mangled.
        out, _, after = humanize("The system is used by thousands of people.")
        self.assertEqual(out, "The system is used by thousands of people.")
        self.assertEqual(after["passives"], 1)

    def test_passive_future_rewritten(self):
        out, _, _ = humanize("The container will be restarted by the kubelet.")
        self.assertEqual(out, "The kubelet will restart the container.")

    def test_passive_modal_rewritten(self):
        out, _, _ = humanize("The report should be reviewed by Sara.")
        self.assertEqual(out, "Sara should review the report.")

    def test_passive_adverb_kept(self):
        out, _, _ = humanize(
            "The container will be automatically restarted by the kubelet.")
        self.assertEqual(
            out, "The kubelet will restart the container automatically.")
        out, _, _ = humanize("They are paid by the company.")
        self.assertEqual(out, "The company pays them.")

    def test_passive_long_agent_left_alone(self):
        # A by-phrase with a trailing adverbial must not be reordered.
        out, _, after = humanize("They are paid by the company every month.")
        self.assertEqual(out, "They are paid by the company every month.")
        self.assertEqual(after["passives"], 1)

    def test_hedge_removed(self):
        out, _, _ = humanize("This could potentially cause restarts.")
        self.assertNotIn("potentially", out)
        self.assertIn("could cause restarts", out)

    def test_clean_text_unchanged(self):
        text = "The probe checks the container. It restarts it when the check fails."
        out, _, _ = humanize(text)
        self.assertEqual(out, text)

    def test_idempotent(self):
        once, _, _ = humanize(EN_SLOPPY)
        twice, _, _ = humanize(once)
        self.assertEqual(once, twice)


class TestCheck(unittest.TestCase):
    def test_clean_text_scores_high(self):
        report = check("The probe checks the container. It restarts it when the check fails.")
        self.assertGreaterEqual(report["score"], 90)
        self.assertEqual(report["tell_count"], 0)

    def test_sloppy_text_scores_low(self):
        report = check(EN_SLOPPY)
        self.assertLess(report["score"], 70)
        self.assertGreater(report["tell_count"], 0)
        self.assertGreater(report["long_sentences"], 0)

    def test_humanize_improves_score(self):
        _, before, after = humanize(EN_SLOPPY)
        self.assertGreater(after["score"], before["score"])
        self.assertEqual(after["tell_count"], 0)

    def test_fa_report(self):
        report = check(FA_SLOPPY)
        self.assertGreater(report["tell_count"], 0)
        self.assertLess(report["score"], 90)

    def test_detect_lang(self):
        self.assertEqual(detect_lang("سلام دنیا"), "fa")
        self.assertEqual(detect_lang("hello world"), "en")


class TestCli(unittest.TestCase):
    def _run(self, *args, input_text=None):
        return subprocess.run(
            [sys.executable, "-m", "agent_humanizer", *args],
            input=input_text, capture_output=True, text=True, timeout=30)

    def test_humanize_stdin(self):
        proc = self._run("humanize", input_text="It's important to note that the cache is full.")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("cache is full", proc.stdout)
        self.assertIn("after: score", proc.stdout)

    def test_humanize_json(self):
        proc = self._run("humanize", "--json",
                         input_text="Great question! The cache is full.")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertIn("text", data)
        self.assertIn("before", data)
        self.assertIn("after", data)
        self.assertNotIn("great question", data["text"].lower())

    def test_check_clean_exits_zero(self):
        proc = self._run("check", input_text="The probe checks the container.")
        self.assertEqual(proc.returncode, 0)

    def test_check_sloppy_exits_one(self):
        proc = self._run("check", input_text=EN_SLOPPY)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("score", proc.stdout)

    def test_empty_input_exits_one(self):
        proc = self._run("humanize", input_text="   \n")
        self.assertEqual(proc.returncode, 1)

    def test_strict_passes_when_no_tell_survives(self):
        proc = self._run("humanize", "--strict",
                         input_text="It's important to note that the cache is full.")
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
