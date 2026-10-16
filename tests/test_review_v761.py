"""V7.6.1 review tools: the UX inventory follows the real server and the calendar check
stays inside the out-of-sample window."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]
import review_v761 as r  # noqa: E402

COTAHIST = (r.RECOVERY / "cotahist/COTAHIST_A2026.ZIP").exists()


class UxInventory(unittest.TestCase):
    def test_inventory_covers_every_served_page_and_shell_link(self):
        inv = r.ux_inventory()
        self.assertEqual(set(inv["pages"]), set(inv["routes"].values()))
        self.assertEqual(inv["shell_targets_unserved"], [])
        self.assertEqual(
            inv["shell_links_total"], sum(len(v) for v in inv["shell_groups"].values())
        )
        self.assertEqual(
            json.dumps(inv, sort_keys=True), json.dumps(r.ux_inventory(), sort_keys=True)
        )

    def test_negated_labels_are_not_paid(self):
        self.assertEqual(r.intent("Simular proposta sem executar"), "READ_ONLY")
        self.assertEqual(
            r.intent("2. Preparar snapshot e Risk · sem Gemini"), "WRITE_OR_PREPARE"
        )
        self.assertEqual(r.intent("3. Confirmar e executar este lote"), "PAID_INFERENCE")


@unittest.skipUnless(COTAHIST, "cached COTAHIST absent (clean checkout)")
class CalendarCheck(unittest.TestCase):
    def test_selected_sessions_checked_by_date_only(self):
        c = r.calendar_check()
        self.assertEqual(c["source_sha256"], c["source_sha256_recorded_by_radar_inputs"])
        self.assertEqual(c["selected_missing_in_cotahist"], [])
        self.assertEqual(len(c["selected_sessions"]), 10)
        self.assertIn("earlier records skipped", c["read_scope"])


if __name__ == "__main__":
    unittest.main()
