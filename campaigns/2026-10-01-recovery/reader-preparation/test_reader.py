"""Bounded local fixtures: file allowlist, immutable selection and transport guards."""
import copy
import http.server
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

import reader
import receive
import launch


def scope():
    return {"runs": [{"name": "test", "run_dir": "/data/run/test", "kind": "confirmation"}],
            "caches": [], "log_dirs": ["/data/confirmation-20260923/logs"], "b5_readout_dir": "/data/readout"}


class ReaderGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pvc_root = self.root / "data"
        self.pvc_root.mkdir()
        self.pvc = reader.PVC(self.pvc_root)

    def tearDown(self):
        self.pvc.close()
        self.temp.cleanup()

    def write(self, relative, data):
        path = self.pvc_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def export(self):
        return reader.Export(self.pvc, self.root / "stage", scope(), "a" * 64, time.monotonic() + 15)

    def test_traversal_symlink_and_fifo_refused(self):
        for path in ("/etc/passwd", "/data/../secret", "/data/a//b", "/data/./a", "/data/a\\b"):
            with self.assertRaises(ValueError):
                self.pvc.open(path)
        target = self.write("regular.json", b"{}")
        (self.pvc_root / "link.json").symlink_to(target)
        (self.pvc_root / "parent").symlink_to(self.pvc_root, target_is_directory=True)
        os.mkfifo(self.pvc_root / "fifo.json")
        for path in ("/data/link.json", "/data/parent/regular.json", "/data/fifo.json"):
            with self.assertRaises((OSError, ValueError)):
                self.pvc.open(path)

    def test_credential_json_refused_and_logs_redacted(self):
        self.write("run/test/config.json", b'{"password":"synthetic-test-value"}')
        self.write("confirmation-20260923/logs/test-current.log", b"Authorization: Bearer synthetic-test-value\n")
        export = self.export()
        bad = export.copy("/data/run/test/config.json")
        log = export.copy("/data/confirmation-20260923/logs/test-current.log")
        self.assertFalse(bad["accepted"])
        self.assertTrue(log["accepted"])
        stored = (export.blobs / log["stored_sha256"]).read_bytes()
        self.assertNotIn(b"synthetic-test-value", stored)
        self.assertNotEqual(log["source_sha256"], log["stored_sha256"])

    def test_special_arrays_and_unselected_generation_not_allowlisted(self):
        sel = {"/data/run/test": {"generation": "epoch-7"}}
        for path in ("/data/run/test/X_train.npy", "/data/run/test/checkpoints/epoch-8/model.keras", "/data/arbitrary/config.json"):
            self.assertFalse(receive.allowed(path, scope(), sel))
        self.assertTrue(receive.allowed("/data/run/test/checkpoints/epoch-7/optimizer.npz", scope(), sel))

    def test_pointer_bound_to_staged_bytes_and_opaque_checkpoint_copy(self):
        original = self.write("run/test/latest.json", b'{"checkpoint":"epoch-7"}')
        for name, raw in (("state.json", b"{}"), ("model.keras", b"opaque-model-no-load"), ("optimizer.npz", b"opaque-optimizer-no-load")):
            self.write("run/test/checkpoints/epoch-7/" + name, raw)
        export = self.export()
        export.copy("/data/run/test/latest.json")
        original.write_bytes(b'{"checkpoint":"epoch-8"}')
        result = export.run()
        selected = result["checkpoint_selections"][0]
        self.assertEqual(selected["generation"], "epoch-7")
        self.assertEqual(selected["pointer_sha256"], reader.sha(b'{"checkpoint":"epoch-7"}'))
        self.assertTrue(export.copied["/data/run/test/checkpoints/epoch-7/model.keras"]["accepted"])
        self.assertFalse(any("epoch-8/" in row["pvc_path"] for row in result["files"]))

    def test_unsafe_pointer_and_source_mutation_refused(self):
        self.write("run/test/latest.json", b'{"checkpoint":"epoch-7/../../secret"}')
        export = self.export()
        export.run()
        self.assertEqual(export.receipt["checkpoint_selections"][0]["status"], "invalid_pointer_not_followed")
        self.write("run/test/config.json", b"{}")
        old = self.pvc.inspect
        self.pvc.inspect = lambda *a, **k: (0, 0, 0, 0, 0)
        try:
            # Fresh export so this path is not the previously missing cached row.
            other = reader.Export(self.pvc, self.root / "other", scope(), "a" * 64, time.monotonic() + 15)
            row = other.copy("/data/run/test/config.json")
            self.assertFalse(row["accepted"])
        finally:
            self.pvc.inspect = old

    def test_file_size_deadline_and_output_reuse_guards(self):
        path = self.write("oversized.json", b"")
        with path.open("wb") as f:
            f.truncate(reader.MAX_FILE[".json"] + 1)
        export = self.export()
        self.assertFalse(export.copy("/data/oversized.json")["accepted"])
        with self.assertRaises(FileExistsError):
            self.export()
        export.deadline = time.monotonic() - 1
        with self.assertRaises(TimeoutError):
            export.copy("/data/other.json")

    def test_rejected_bytes_consume_total_budget(self):
        self.write("run/test/config.json", b"invalid-json")
        self.write("run/test/data_info.json", b"invalid-json")
        old = reader.MAX_TOTAL
        reader.MAX_TOTAL = 20
        try:
            export = self.export()
            result = export.run()
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["interrupted_by"], "BudgetExceeded")
            self.assertEqual(result["source_bytes_read"], len(b"invalid-json"))
            self.assertEqual(export.copied["/data/run/test/data_info.json"]["status"], "budget_exceeded")
        finally:
            reader.MAX_TOTAL = old

    def test_http_hash_truncation_and_oversize_rejected(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *unused):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", "3")
                self.send_header("X-Content-SHA256", reader.sha(b"abc") if self.path != "/wrong" else "0" * 64)
                self.end_headers()
                self.wfile.write(b"a" if self.path == "/short" else b"abc")
        with http.server.HTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                port = server.server_port
                self.assertEqual(receive.get(port, "/ok", 3)[1], b"abc")
                for endpoint, limit in (("/wrong", 3), ("/short", 3), ("/ok", 2)):
                    with self.assertRaises((AssertionError, http.client.IncompleteRead)):
                        receive.get(port, endpoint, limit)
            finally:
                server.shutdown()
                thread.join()

    def test_bundle_hash_and_payload_tamper_rejected(self):
        (self.root / "scope.json").write_bytes(b"{}")
        raw = reader.encoded({"files": {"scope.json": reader.sha(b"{}")}, "authorization_status": "pending_explicit_recovery_exception"})
        bundle = self.root / "BUNDLE.json"
        bundle.write_bytes(raw)
        reader.verify_bundle(bundle, reader.sha(raw))
        (self.root / "scope.json").write_bytes(b"{ }")
        with self.assertRaises(ValueError):
            reader.verify_bundle(bundle, reader.sha(raw))

    def test_live_identity_and_readonly_mount_guards(self):
        directories = list((Path(__file__).parent / "frozen").iterdir())
        frozen = max(directories, key=lambda p: p.stat().st_mtime_ns)
        planned = json.loads((frozen / "job.json").read_bytes())
        cm = json.loads((frozen / "configmap.json").read_bytes())
        job = copy.deepcopy(planned)
        job["metadata"]["uid"] = "fixture-job-uid"
        pod = {"kind": "Pod", "metadata": {"namespace": "cms-ml", "name": "fixture-pod", "uid": "fixture-pod-uid",
              "ownerReferences": [{"kind": "Job", "name": job["metadata"]["name"], "uid": "fixture-job-uid", "controller": True}]},
              "spec": copy.deepcopy(planned["spec"]["template"]["spec"]), "status": {"phase": "Running"}}
        pvc = {"kind": "PersistentVolumeClaim", "metadata": {"name": "kai-data", "namespace": "cms-ml", "uid": "fixture-pvc"}, "status": {"phase": "Bound"}}
        observed_cm = copy.deepcopy(cm)
        observed_cm["metadata"]["uid"] = "fixture-cm"
        access = {"job": job, "pod": pod, "pvc": pvc, "configmap": observed_cm}
        receive.validate_access(planned, cm, access, "fixture-pvc")
        for mutation in ("pvc", "owner", "write", "subpath", "privileged", "fsgroup", "extra_container", "code"):
            bad = copy.deepcopy(access)
            if mutation == "pvc": bad["pvc"]["metadata"]["uid"] = "other"
            elif mutation == "owner": bad["pod"]["metadata"]["ownerReferences"][0]["uid"] = "other"
            elif mutation == "write": bad["pod"]["spec"]["containers"][0]["volumeMounts"][0]["readOnly"] = False
            elif mutation == "subpath": bad["pod"]["spec"]["containers"][0]["volumeMounts"][0]["subPath"] = "other"
            elif mutation == "privileged": bad["pod"]["spec"]["containers"][0]["securityContext"]["privileged"] = True
            elif mutation == "fsgroup": bad["pod"]["spec"]["securityContext"]["fsGroup"] = 0
            elif mutation == "extra_container": bad["pod"]["spec"]["containers"].append(copy.deepcopy(bad["pod"]["spec"]["containers"][0]))
            elif mutation == "code": bad["configmap"]["data"]["reader.py"] += "\n# changed\n"
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                receive.validate_access(planned, cm, bad, "fixture-pvc")

    def test_exception_requires_exact_hash_operations_and_reference(self):
        auth = {"approval_status": "approved", "approval_ref": "Synthetic unit-test approval", "preparation_sha256": "a" * 64,
                "exceptions": sorted(launch.EXCEPTIONS), "operations": sorted(launch.OPERATIONS),
                "context": "nautilus", "namespace": "cms-ml", "authorized_at_utc": "2026-10-01T05:00:00Z", "user_authorization_reference": "Synthetic test user message"}
        launch.authorization(auth, "a" * 64, auth["approval_ref"])
        for key, value in (("approval_ref", "other"), ("preparation_sha256", "b" * 64), ("operations", []), ("exceptions", []), ("context", "other")):
            bad = {**auth, key: value}
            with self.subTest(key=key), self.assertRaises(AssertionError):
                launch.authorization(bad, "a" * 64, auth["approval_ref"])
        for key, value in (("approval_status", "pending"), ("approval_ref", "PENDING"), ("user_authorization_reference", "TODO"), ("authorized_at_utc", "PENDING"), ("authorized_at_utc", "2026-10-01T05:00:00")):
            bad = {**auth, key: value}
            with self.subTest(key=key, value=value), self.assertRaises((AssertionError, ValueError)):
                launch.authorization(bad, "a" * 64, bad["approval_ref"])


if __name__ == "__main__":
    unittest.main()
