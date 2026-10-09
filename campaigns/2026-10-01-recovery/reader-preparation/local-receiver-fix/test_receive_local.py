"""Captured live Pod identity and exact admission exception; no network or transfer."""
import copy
import json
from pathlib import Path
import unittest

import receive_local

HERE = Path(__file__).resolve().parent
PREP = HERE.parent
LAB = PREP.parents[2]
FROZEN = PREP / "frozen/cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e"
CAPTURE = PREP.parent / "captures/reader-run-20261001T0540Z"


class AdmissionGuard(unittest.TestCase):
    def setUp(self):
        self.original = receive_local.load_original(FROZEN / "preparation.json", receive_local.PREPARATION_SHA)
        self.job = json.loads((FROZEN / "job.json").read_bytes())
        self.cm = json.loads((FROZEN / "configmap.json").read_bytes())
        self.access = {"job": json.loads((CAPTURE / "observation-03/job.json").read_bytes()),
                       "pod": json.loads((CAPTURE / "observation-03/pods.json").read_bytes())["items"][0],
                       "pvc": json.loads((CAPTURE / "pvc.json").read_bytes()),
                       "configmap": json.loads((CAPTURE / "configmap.json").read_bytes())}
        self.uid = json.loads((FROZEN / "preparation.json").read_bytes())["pvc_uid"]

    def check(self, access):
        return receive_local.validate_with_admission(self.original.validate_access, self.job, self.cm, access, self.uid)

    def test_actual_captured_pod_passes_without_mutating_objects(self):
        before = copy.deepcopy(self.access)
        with self.assertRaises(AssertionError):
            self.original.validate_access(self.job, self.cm, self.access, self.uid)
        result = self.check(self.access)
        self.assertEqual(result["pod_uid"], "09bf9a9f-405e-42b7-b8df-cde90e236fe9")
        self.assertEqual(result["admission_environment_exception"]["observed"], receive_local.ALLOWED_POD_ENV)
        self.assertEqual(before, self.access)

    def test_other_environment_forms_are_rejected(self):
        variants = [[{"name": "NVIDIA_VISIBLE_DEVICES", "value": "all"}],
                    [{"name": "OTHER", "value": "void"}],
                    [{"name": "NVIDIA_VISIBLE_DEVICES", "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}}}],
                    [{"name": "NVIDIA_VISIBLE_DEVICES", "value": "void", "valueFrom": {}}],
                    receive_local.ALLOWED_POD_ENV * 2,
                    receive_local.ALLOWED_POD_ENV + [{"name": "EXTRA", "value": "x"}]]
        for env in variants:
            bad = copy.deepcopy(self.access)
            bad["pod"]["spec"]["containers"][0]["env"] = env
            with self.subTest(env=env), self.assertRaises(AssertionError):
                self.check(bad)

    def test_other_identity_and_security_checks_remain_enforced(self):
        for variant in ("job_env", "envFrom", "pod_owner", "pvc_uid", "write_mount", "image", "resources"):
            bad = copy.deepcopy(self.access)
            container = bad["pod"]["spec"]["containers"][0]
            if variant == "job_env": bad["job"]["spec"]["template"]["spec"]["containers"][0]["env"] = receive_local.ALLOWED_POD_ENV
            elif variant == "envFrom": container["envFrom"] = [{"secretRef": {"name": "other"}}]
            elif variant == "pod_owner": bad["pod"]["metadata"]["ownerReferences"][0]["uid"] = "other"
            elif variant == "pvc_uid": bad["pvc"]["metadata"]["uid"] = "other"
            elif variant == "write_mount": container["volumeMounts"][0]["readOnly"] = False
            elif variant == "image": container["image"] = "other"
            elif variant == "resources": container["resources"]["limits"]["cpu"] = "2"
            with self.subTest(variant=variant), self.assertRaises(AssertionError):
                self.check(bad)


if __name__ == "__main__":
    unittest.main()
