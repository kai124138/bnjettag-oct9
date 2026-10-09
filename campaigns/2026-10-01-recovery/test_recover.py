import base64
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("recover", Path(__file__).with_name("recover.py"))
recover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recover)


class RecoveryTests(unittest.TestCase):
    def test_stored_bundles_match_without_running_code(self):
        manifest = recover.recovery_manifest()
        self.assertEqual(len(manifest["runs"]), 17)
        self.assertEqual(len(manifest["caches"]), 3)
        for bundle in manifest["frozen_bundles"]:
            self.assertEqual(bundle["status"], "stored_bytes_verified_no_execution")

    def test_archive_tampering_and_path_escape_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cm, manifest = root / "cm.json", root / "manifest.json"
            for name in ("code/a.py", "code/../escape.py"):
                stream = io.BytesIO()
                with tarfile.open(fileobj=stream, mode="w:gz") as archive:
                    member = tarfile.TarInfo(name)
                    member.size = 4
                    archive.addfile(member, io.BytesIO(b"test"))
                raw = stream.getvalue()
                cm.write_text(json.dumps({"metadata": {"name": "test"}, "binaryData": {"hgq2.tar.gz": base64.b64encode(raw).decode()}}))
                manifest.write_text(json.dumps({"sha256": recover.sha(raw), "files": {"a.py": "wrong_hash"}}))
                with patch.object(recover, "LAB", root), self.assertRaises(ValueError):
                    recover.frozen_bundle(cm, manifest)

    def test_metadata_drops_inline_env_and_last_applied(self):
        original = {"metadata": {"name": "j", "annotations": {"kubectl.kubernetes.io/last-applied-configuration": "SENSITIVE"}},
                    "spec": {"containers": [{"env": [{"name": "WANDB_API_KEY", "value": "SENSITIVE"}]}]}}
        self.assertNotIn("SENSITIVE", json.dumps(recover.safe_object(original)))

    def test_pod_ownership_and_job_uid(self):
        pod = {"metadata": {"labels": {"user": "kai", "job-name": "j"},
                             "ownerReferences": [{"kind": "Job", "name": "j", "uid": "one"}]}}
        self.assertTrue(recover.owned_pod(pod, "j", "one"))
        self.assertFalse(recover.owned_pod(pod, "j", "two"))
        pod["metadata"]["labels"]["user"] = "other"
        self.assertFalse(recover.owned_pod(pod, "j"))

    def test_redaction(self):
        raw = "WANDB_API_KEY=abc123 Bearer abcdef ghp_example " + "a" * 40
        clean = recover.redact(raw)
        for token in ("abc123", "abcdef", "ghp_example", "a" * 40):
            self.assertNotIn(token, clean)

    def test_bearer_headers_and_structural_json_secrets_are_redacted(self):
        headers = ('Authorization: Bearer fixture_bearer', 'Authorization=Basic fixture_basic',
                   'request {"api_key": "fixture_quoted value"}')
        for raw in headers:
            self.assertNotIn("fixture_", recover.redact(raw))
        raw = json.dumps({"api_key": "fixture_json", "nested": [{"WANDB_API_KEY": "fixture_nested"}],
                          "status": {"message": "request rejected: Authorization: Bearer fixture_status; retry"}})
        cleaned = recover.redact(raw)
        self.assertNotIn("fixture_", cleaned)
        self.assertEqual(json.loads(cleaned)["api_key"], "[REDACTED]")
        obj = recover.safe_object({"metadata": {"name": "p"}, "status": {
            "message": 'request rejected: {"api_key": "fixture_embedded"}', "authorization": "Bearer fixture_direct"}})
        self.assertNotIn("fixture_", json.dumps(obj))
        self.assertIsInstance(json.loads(json.dumps(obj)), dict)

    def test_cache_metadata_is_required_and_mismatch_is_explicit(self):
        expected = {"expected_array_sha256": {"x_train": "abc"}, "expected_n_train": 10}
        self.assertEqual(recover.cache_identity({}, expected)["status"], "identity_unavailable_or_mismatched")
        self.assertEqual(recover.cache_identity({"array_sha256": {"x_train": "abc"}, "n_train": 10}, expected)["failures"], [])

    def test_collection_reads_only_and_no_logs_for_unowned_pods(self):
        commands = []
        def fake_run(command, **kwargs):
            commands.append(command)
            if command[1:3] == ["config", "get-contexts"]:
                return subprocess.CompletedProcess(command, 0, "approved-context\n", "")
            name = recover.JOBS[0]
            obj = {"metadata": {"name": "foreign", "uid": "u", "labels": {"user": "other", "job-name": name},
                                 "ownerReferences": [{"kind": "Job", "name": name, "uid": "u"}]},
                   "spec": {"containers": [{"name": "train"}]}}
            return subprocess.CompletedProcess(command, 0, json.dumps({"items": [obj]}), "")
        with tempfile.TemporaryDirectory() as tmp, patch.object(recover.subprocess, "run", side_effect=fake_run):
            out = Path(tmp) / "capture"
            recover.collect_cluster(out, "approved-context")
            self.assertEqual(len(commands), 4)
            self.assertTrue(all(c[6] == "get" for c in commands[1:]))
            self.assertTrue(all(c[1:6] == ["--context", "approved-context", "-n", "cms-ml", "--request-timeout=20s"] for c in commands[1:]))
            self.assertFalse(any("logs" in c for c in commands))
            with self.assertRaises(FileExistsError):
                recover.collect_cluster(out, "approved-context")

    def capture_cluster_fixture(self, job_case, pod_uid="uid-live"):
        commands = []
        current_job = None
        def fake_run(command, **kwargs):
            nonlocal current_job
            commands.append(command)
            if command[1:3] == ["config", "get-contexts"]:
                return subprocess.CompletedProcess(command, 0, "approved-context\n", "")
            if command[6:8] == ["get", "jobs"]:
                current_job = command[command.index("--field-selector") + 1].split("=", 1)[1]
                if job_case == "failed":
                    return subprocess.CompletedProcess(command, 1, "", "credential-bearing stderr is not saved")
                if job_case == "bad_json":
                    return subprocess.CompletedProcess(command, 0, "not json", "")
                if job_case == "malformed":
                    value = {}
                elif job_case == "absent":
                    value = {"items": []}
                else:
                    metadata = {"name": current_job, "labels": {"user": "kai"}}
                    if job_case != "no_uid":
                        metadata["uid"] = "uid-live"
                    value = {"items": [{"kind": "Job", "metadata": metadata}]}
            elif command[6:8] == ["get", "pods"]:
                value = {"items": [{"metadata": {"name": current_job + "-pod", "labels": {"user": "kai", "job-name": current_job},
                            "ownerReferences": [{"kind": "Job", "name": current_job, "uid": pod_uid}]},
                            "spec": {"containers": [{"name": "train"}]}}]}
            else:
                return subprocess.CompletedProcess(command, 0, "safe log", "")
            return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
        with tempfile.TemporaryDirectory() as tmp, patch.object(recover.subprocess, "run", side_effect=fake_run):
            out = Path(tmp) / "capture"
            recover.collect_cluster(out, "approved-context")
            return commands, json.loads((out / "receipt.json").read_text())

    def test_failed_malformed_or_uidless_jobs_never_downgrade_binding(self):
        for case in ("failed", "bad_json", "malformed", "no_uid"):
            with self.subTest(case=case):
                commands, receipt = self.capture_cluster_fixture(case)
                self.assertEqual(len(commands), 4)
                self.assertFalse(any(c[6:8] == ["get", "pods"] or c[6:7] == ["logs"] for c in commands))
                self.assertEqual({r["status"] for r in receipt["ownership_checks"]}, {"job_read_unavailable_or_invalid"})
                self.assertTrue(all(r["job_uid"] is None for r in receipt["ownership_checks"]))

    def test_absent_jobs_are_explicit_and_orphan_logs_are_not_collected(self):
        commands, receipt = self.capture_cluster_fixture("absent")
        self.assertEqual(len(commands), 4)
        self.assertEqual({r["status"] for r in receipt["ownership_checks"]}, {"job_observed_absent"})

    def test_logs_require_positively_matched_job_owner_uid(self):
        commands, receipt = self.capture_cluster_fixture("valid", pod_uid="uid-old")
        self.assertFalse(any(c[6:7] == ["logs"] for c in commands))
        commands, receipt = self.capture_cluster_fixture("valid", pod_uid="uid-live")
        self.assertEqual(sum(c[6:7] == ["logs"] for c in commands), 6)
        self.assertEqual({r["job_uid"] for r in receipt["ownership_checks"]}, {"uid-live"})

    def test_missing_context_or_kubectl_prevents_cluster_queries(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(recover.subprocess, "run", side_effect=FileNotFoundError):
            out = Path(tmp) / "capture"
            with self.assertRaisesRegex(ValueError, "context unavailable"):
                recover.collect_cluster(out, "approved-context")
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(ValueError, "explicit existing"):
                recover.collect_cluster(out, "")

    def test_output_is_immutable_and_pvc_escape_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "record.json"
            recover.write_new(output, {"original": True})
            with self.assertRaises(FileExistsError):
                recover.write_new(output, {"replacement": True})
            with self.assertRaises(ValueError):
                recover.source_path(root, "/data/../secret")
            (root / "link").symlink_to(output)
            with self.assertRaises(ValueError):
                recover.source_path(root, "/data/link")

    def test_empty_pvc_is_missing_evidence_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            out = Path(tmp) / "export"
            recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            self.assertTrue(receipt["files"])
            self.assertEqual({r["status"] for r in receipt["files"]}, {"missing"})

    def pvc_fixture(self, root):
        run = root / "fixture/runs/arm"
        run.mkdir(parents=True)
        manifest = {"caches": [], "runs": [{"run_dir": "/data/fixture/runs/arm", "name": "arm", "kind": "confirmation"}],
                    "log_dirs": [], "b5_readout_dir": "/data/fixture/readout"}
        for epoch in ("epoch-0001", "epoch-0002"):
            generation = run / "checkpoints" / epoch
            generation.mkdir(parents=True)
            (generation / "state.json").write_text(json.dumps({"generation": epoch}))
        (run / "latest.json").write_text('{"checkpoint": "epoch-0001"}')
        return run, manifest

    def test_pointer_advance_copies_generation_from_accepted_pointer_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            raw_pointer = (run / "latest.json").read_bytes()
            read_original = recover.read_source_bytes
            def advance(path):
                result = read_original(path)
                if path == run / "latest.json":
                    path.write_text('{"checkpoint": "epoch-0002"}')
                return result
            with patch.object(recover, "recovery_manifest", return_value=manifest), patch.object(recover, "read_source_bytes", side_effect=advance):
                recover.export_pvc(root, out)
            destination = out / "fixture/runs/arm"
            self.assertEqual((destination / "latest.json").read_bytes(), raw_pointer)
            self.assertTrue((destination / "checkpoints/epoch-0001/state.json").exists())
            self.assertFalse((destination / "checkpoints/epoch-0002").exists())
            selection = json.loads((out / "export-receipt.json").read_text())["checkpoint_selections"][0]
            self.assertEqual(selection["generation"], "epoch-0001")
            self.assertEqual(selection["pointer_sha256"], recover.sha(raw_pointer))

    def test_disappearing_generation_is_incomplete_and_never_substituted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            read_original = recover.read_source_bytes
            def remove_generation(path):
                result = read_original(path)
                if path == run / "latest.json":
                    path.unlink()
                    (run / "checkpoints/epoch-0001/state.json").unlink()
                    (run / "checkpoints/epoch-0001").rmdir()
                return result
            with patch.object(recover, "recovery_manifest", return_value=manifest), patch.object(recover, "read_source_bytes", side_effect=remove_generation):
                recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            selection = receipt["checkpoint_selections"][0]
            self.assertEqual(selection["generation"], "epoch-0001")
            self.assertEqual(selection["checkpoints"][0]["status"], "incomplete_or_source_changed")
            self.assertFalse((out / "fixture/runs/arm/checkpoints/epoch-0002").exists())

    def test_changing_generation_file_is_explicit_partial_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            read_original = recover.read_source_bytes
            def changed(path):
                raw, state = read_original(path)
                return raw, "changed_or_disappeared" if path.name == "state.json" else state
            with patch.object(recover, "recovery_manifest", return_value=manifest), patch.object(recover, "read_source_bytes", side_effect=changed):
                recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            self.assertEqual(receipt["checkpoint_selections"][0]["checkpoints"][0]["status"], "incomplete_or_source_changed")
            self.assertIn("copied_source_changed", {r["status"] for r in receipt["files"]})

    def test_source_reader_detects_modification_or_disappearance_after_read(self):
        for action in ("change", "delete"):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "state.json"
                path.write_bytes(b'{"old": true}')
                original_read = Path.read_bytes
                def changing_read(current):
                    raw = original_read(current)
                    if current == path:
                        if action == "change":
                            current.write_bytes(b'{"new": "longer value"}')
                        else:
                            current.unlink()
                    return raw
                with patch.object(Path, "read_bytes", changing_read):
                    raw, status = recover.read_source_bytes(path)
                self.assertEqual(raw, b'{"old": true}')
                self.assertEqual(status, "changed_or_disappeared")

    def test_refused_json_pointer_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            (run / "latest.json").write_text('{"checkpoint": "epoch-0001", "api_key": "fixture_credential"}')
            with patch.object(recover, "recovery_manifest", return_value=manifest):
                recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            selection = receipt["checkpoint_selections"][0]
            self.assertEqual(selection["pointer_status"], "refused_possible_credential")
            self.assertIsNone(selection["generation"])
            self.assertFalse((out / "fixture/runs/arm/checkpoints").exists())
            self.assertNotIn("fixture_credential", (out / "export-receipt.json").read_text())

    def test_unexpected_export_interruption_still_writes_partial_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            with patch.object(recover, "recovery_manifest", return_value=manifest), patch.object(recover, "read_source_bytes", side_effect=RuntimeError):
                with self.assertRaises(RuntimeError):
                    recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            self.assertEqual(receipt["interrupted_by"], "RuntimeError")
            self.assertTrue(receipt["files"])

    def test_terminal_source_and_preprocessing_records_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "source", Path(tmp) / "export"
            run, manifest = self.pvc_fixture(root)
            names = ("source_manifest.json", "input_std.json", "COMPLETE.json", "TRAINING_COMPLETE.json", "VERIFIED_COMPLETE.json", "screen_result.json")
            for name in names:
                (run / name).write_text(json.dumps({"fixture": name}))
            with patch.object(recover, "recovery_manifest", return_value=manifest):
                recover.export_pvc(root, out)
            receipt = json.loads((out / "export-receipt.json").read_text())
            for name in names:
                self.assertEqual((out / "fixture/runs/arm" / name).read_bytes(), (run / name).read_bytes())
                row = next(r for r in receipt["files"] if r["pvc_path"].endswith("/" + name))
                self.assertEqual(row["status"], "copied")


if __name__ == "__main__":
    unittest.main()
