import unittest

from experience_router import Experience, ExperienceRouter


class ExperienceRouterTests(unittest.TestCase):
    def test_full_rollout_is_enabled(self):
        router = ExperienceRouter([Experience("home", rollout_percent=100)])
        self.assertTrue(router.enabled_for("home", subject_id="u1"))

    def test_zero_rollout_is_disabled(self):
        router = ExperienceRouter([Experience("beta", rollout_percent=0)])
        self.assertFalse(router.enabled_for("beta", subject_id="u1"))

    def test_disabled_flag_wins(self):
        router = ExperienceRouter([Experience("beta", enabled=False)])
        self.assertFalse(router.enabled_for("beta", subject_id="u1"))

    def test_required_traits(self):
        router = ExperienceRouter([
            Experience("partner", required_traits=frozenset({"partner"}))
        ])
        self.assertFalse(router.enabled_for("partner", subject_id="u1"))
        self.assertTrue(router.enabled_for("partner", subject_id="u1", traits=["partner"]))

    def test_rollout_is_stable(self):
        router = ExperienceRouter([Experience("trial", rollout_percent=37)])
        first = router.enabled_for("trial", subject_id="stable-user")
        for _ in range(10):
            self.assertEqual(first, router.enabled_for("trial", subject_id="stable-user"))

    def test_route_is_sorted(self):
        router = ExperienceRouter([
            Experience("zeta"),
            Experience("alpha"),
        ])
        self.assertEqual(router.route(subject_id="u"), ["alpha", "zeta"])

    def test_manifest_hash_independent_of_registration_order(self):
        a = ExperienceRouter([Experience("a"), Experience("b", rollout_percent=20)])
        b = ExperienceRouter([Experience("b", rollout_percent=20), Experience("a")])
        self.assertEqual(a.manifest_hash(), b.manifest_hash())

    def test_unknown_experience_raises(self):
        with self.assertRaises(KeyError):
            ExperienceRouter().enabled_for("missing", subject_id="u")

    def test_invalid_rollout_rejected(self):
        with self.assertRaises(ValueError):
            Experience("bad", rollout_percent=101)


if __name__ == "__main__":
    unittest.main()
