"""Regression checks for observed preflight evidence-integrity defects; no ML."""
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import tempfile
import unittest

import numpy as np

SPEC=importlib.util.spec_from_file_location('preflight_merge',Path(__file__).with_name('preflight_merge.py'))
runner=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runner)


class EvidenceGuards(unittest.TestCase):
    def test_nonzero_nested_pass_fails(self):
        receipt={'status':'PASS','result':[{'id':'fixture','status':'PASS'}]}
        failed=runner.process_outcome(receipt,1)
        self.assertEqual(failed['status'],'FAIL')
        self.assertEqual(runner.comparison_status([failed,receipt],True),'FAIL')
        timed=runner.process_outcome(receipt,-signal.SIGKILL,'wall limit')
        self.assertEqual(runner.comparison_status([timed,receipt],True),'TIMEOUT')

    def test_prediction_isolation_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'original.npy',Path(tmp)/'candidate.npy'
            np.save(a,np.array([0.,1.]));np.save(b,np.array([0.,1.001]))
            row=lambda p:{'output_file':str(p),'output_file_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            self.assertGreater(runner.compare_outputs(row(a),row(b)),1e-7)
            with self.assertRaises(AssertionError):runner.compare_outputs(row(a),row(a))
            old=row(a);np.save(a,np.array([2.,3.]))
            with self.assertRaises(AssertionError):runner.compare_outputs(old,row(b))

    def test_existing_output_or_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output,evidence=Path(tmp)/'report.json',Path(tmp)/'evidence'
            runner.refuse_reuse(output,evidence)
            evidence.mkdir()
            with self.assertRaises(FileExistsError):runner.refuse_reuse(output,evidence)
            evidence.rmdir();output.write_text('{}')
            with self.assertRaises(FileExistsError):runner.refuse_reuse(output,evidence)

    def test_exception_receipt_preserves_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner.ACTIVE_OUTPUT=Path(tmp)/'receipt.json';runner.ACTIVE_RECEIPT={'rows':[{'id':'completed','status':'PASS'}]}
            runner.record_exception(AssertionError('input changed'))
            result=json.loads(runner.ACTIVE_OUTPUT.read_text())
            self.assertEqual(result['status'],'MERGE_ENGINEERING_INVALID')
            self.assertEqual(result['rows'][0]['id'],'completed')
            runner.ACTIVE_OUTPUT=runner.ACTIVE_RECEIPT=None

    def test_preprocessing_participates_in_reload_identity(self):
        self.assertNotEqual(runner.digest(['config',1,'checkpoint','stdA']),runner.digest(['config',1,'checkpoint','stdB']))


if __name__=='__main__':unittest.main()
