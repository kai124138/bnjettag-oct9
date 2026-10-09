"""Pilot program W&B stages (patch 0038): pilot-r1/r2/r3 key the run id and the group suffix."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bnhgq2.wandb_util import STAGE_GROUP_SUFFIX, run_stage, stage_group, stage_run_id  # noqa: E402


class PilotStages(unittest.TestCase):
    def test_group_and_id(self):
        self.assertEqual(stage_group('chang-n64-20261005', 'pilot-r1'), 'chang-n64-20261005-pilot-r1')
        ids = {stage_run_id('pilot1005-h1-e-350k-c-s1', s) for s in ('pilot-r1', 'pilot-r2', 'pilot-r3', 'production')}
        self.assertEqual(len(ids), 4)

    def test_existing_stages_unchanged(self):
        self.assertEqual({k: STAGE_GROUP_SUFFIX[k] for k in ('canary', 'pilot', 'pilot-b', 'pilot-c', 'production')},
                         {'canary': '-canary', 'pilot': '-canary', 'pilot-b': '-pilot-b', 'pilot-c': '-pilot-c',
                          'production': ''})

    def test_run_stage_accepts_rounds_only(self):
        old = os.environ.get('BNJ_STAGE')
        try:
            os.environ['BNJ_STAGE'] = 'pilot-r1'
            self.assertEqual(run_stage(required=True), 'pilot-r1')
            os.environ['BNJ_STAGE'] = 'pilot-r4'
            with self.assertRaises(ValueError):
                run_stage(required=True)
        finally:
            if old is None:
                os.environ.pop('BNJ_STAGE', None)
            else:
                os.environ['BNJ_STAGE'] = old


if __name__ == '__main__':
    unittest.main(verbosity=2)
