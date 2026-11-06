"""Host boundary fakes only. No emulator, TTS voice, real RPC, microphone or ASR."""
import itertools
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audio_fixture as fixture
import emulator_audio as audio


def make_wav(path, *, frames=1600, channels=1, width=2, rate=16000, nonzero=True):
    with wave.open(str(path), "wb") as wav:
        wav.setparams((channels, width, rate, 0, "NONE", "not compressed"))
        wav.writeframes((struct.pack("<h", 1 if nonzero else 0) * frames * channels) if width == 2 else bytes([1]) * frames)


class FakeRpc:
    def __init__(self, packets):
        self.packets = packets
        self.is_cancelled = False
    def cancel(self): self.is_cancelled = True
    def cancelled(self): return self.is_cancelled
    def done(self): return self.is_cancelled


class FakeBackend:
    def __init__(self):
        self.mic_calls = 0
        self.closed = False
        self.fail_mic = False
        self.fail_inject = False
        self.rpc = None
    def mic_off(self):
        self.mic_calls += 1
        if self.fail_mic: raise RuntimeError("synthetic failure")
    def inject(self, packets, timeout):
        if self.fail_inject: raise RuntimeError("synthetic failure")
        self.rpc = FakeRpc(packets)
        return self.rpc
    def close(self): self.closed = True


class Harness:
    def __init__(self, root):
        self.root = root
        self.discovery = root / "pid_12345.ini"
        self.avd_dir = root / "owned.avd"
        self.avd_dir.mkdir()
        self.boot = "11111111-2222-3333-4444-555555555555"
        self.kernel = "1"
        self.avd = "OwnedAudio"
        self.listener = "127.0.0.1:8590"
        self.commands = []
        self.backend = FakeBackend()
        self.values = {"avd.name": "OwnedAudio", "avd.dir": str(self.avd_dir),
                       "port.serial": "5580", "grpc.port": "8590", "grpc.token": "synthetic-test-token",
                       "cmdline": "emulator -grpc-use-token"}
        self.write_discovery()
        self.wav = root / "fixture.wav"
        make_wav(self.wav)
    def write_discovery(self):
        self.discovery.write_text("\n".join(f"{k}={v}" for k, v in self.values.items()))
        self.discovery.chmod(0o600)
    def owner(self, **kwargs):
        values = dict(sdk=self.root / "sdk", target="emulator-5580", avd="OwnedAudio",
                      avd_dir=self.avd_dir, discovery=self.discovery,
                      stubs_dir=self.root / "stubs", marker_dir=self.root / "markers")
        values.update(kwargs)
        return audio.OwnedEmulatorAudio(**values)
    def run(self, *args):
        args = tuple(map(str, args)); self.commands.append(args)
        if args[0] == "lsof": return "p12345\nf12\nn" + self.listener + "\n"
        tail = args[3:]
        if tail == ("shell", "getprop", "ro.kernel.qemu"): return self.kernel
        if tail == ("emu", "avd", "name"): return self.avd + "\nOK\n"
        if tail == ("shell", "cat", "/proc/sys/kernel/random/boot_id"): return self.boot
        if tail == ("emu", "kill"): return "OK"
        raise AssertionError("Unexpected system boundary")
    def killed(self): return any(c[-2:] == ("emu", "kill") for c in self.commands)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def test_format_and_nonzero_metadata_without_asr_thresholds(self):
        p = self.root / "audio.wav"; make_wav(p)
        metadata, pcm = fixture.load_wav(p)
        self.assertEqual((metadata["frames"], len(pcm), metadata["nonzeroSamples"]), (1600, 3200, 1600))
        self.assertNotIn("realAsr", metadata)
    def test_wrong_channels_width_rate_duration_and_silence_fail(self):
        for index, values in enumerate(({"channels": 2}, {"width": 1}, {"rate": 8000}, {"frames": 1599},
                                        {"frames": 160001}, {"nonzero": False})):
            p = self.root / f"bad{index}.wav"; make_wav(p, **values)
            with self.assertRaises(ValueError): fixture.load_wav(p)
    def test_truncated_pcm_fails(self):
        p = self.root / "truncated.wav"; make_wav(p)
        p.write_bytes(p.read_bytes()[:-2])
        with self.assertRaises(ValueError): fixture.load_wav(p)
    def test_synthesis_uses_stdin_and_never_overwrites(self):
        target = self.root / "new.wav"
        def say(args, **kwargs):
            self.assertNotIn("--an-option; command", args)
            self.assertEqual(kwargs["input"], "--an-option; command")
            self.assertNotIn("shell", kwargs)
            make_wav(Path(args[-1]))
            return type("Result", (), {"returncode": 0})()
        with patch.object(fixture.subprocess, "run", side_effect=say):
            fixture.synthesize("--an-option; command", "InstalledVoice", target)
            original = target.read_bytes()
            with self.assertRaises(FileExistsError): fixture.synthesize("other", "InstalledVoice", target)
        self.assertEqual(original, target.read_bytes())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
    def test_failed_synthesis_cannot_publish_audio(self):
        with patch.object(fixture.subprocess, "run", return_value=type("Result", (), {"returncode": 1})()):
            with self.assertRaises(ValueError): fixture.synthesize("text", "Voice", self.root / "bad.wav")
        self.assertFalse((self.root / "bad.wav").exists())


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.h = Harness(Path(self.temp.name))
        self.run_patch = patch.object(audio, "_run", side_effect=self.h.run); self.run_patch.start(); self.addCleanup(self.run_patch.stop)
        self.connect_patch = patch.object(audio, "_connect", return_value=self.h.backend); self.connect = self.connect_patch.start(); self.addCleanup(self.connect_patch.stop)
        self.kill = patch.object(audio.os, "kill", side_effect=ProcessLookupError); self.kill.start(); self.addCleanup(self.kill.stop)
    def test_rejects_implicit_and_physical_targets_without_cleanup_dispatch(self):
        for target in (None, "", "device-serial", "emulator-0"):
            with self.assertRaises(audio.AudioTransportError):
                with self.h.owner(target=target): pass
        self.assertEqual(self.h.commands, [])
        self.assertFalse(self.h.killed())
    def test_physical_kernel_never_connects_or_kills(self):
        self.h.kernel = "0"
        with self.assertRaises(audio.AudioTransportError):
            with self.h.owner(): pass
        self.connect.assert_not_called(); self.assertFalse(self.h.killed())
    def test_foreign_avd_or_nonprivate_discovery_never_connects_or_kills(self):
        self.h.avd = "Other"
        with self.assertRaises(audio.AudioTransportError):
            with self.h.owner(): pass
        self.h.avd = "OwnedAudio"; self.h.discovery.chmod(0o644)
        with self.assertRaises(audio.AudioTransportError):
            with self.h.owner(): pass
        self.connect.assert_not_called(); self.assertFalse(self.h.killed())
    def test_symlink_discovery_is_rejected(self):
        link = self.h.root / "pid_45678.ini"; link.symlink_to(self.h.discovery)
        with self.assertRaises(audio.AudioTransportError):
            with self.h.owner(discovery=link): pass
        self.connect.assert_not_called(); self.assertFalse(self.h.killed())
    def test_path_serial_auth_and_listener_mismatches_fail_before_connect_or_kill(self):
        for key, value in (("avd.dir", "/not-the-owned-avd"), ("port.serial", "5554"),
                           ("cmdline", "emulator"), ("grpc.token", ""), ("grpc.port", "0")):
            original = self.h.values[key]; self.h.values[key] = value; self.h.write_discovery()
            with self.assertRaises(audio.AudioTransportError):
                with self.h.owner(): pass
            self.h.values[key] = original
        self.h.write_discovery(); self.h.listener = "0.0.0.0:8590"
        with self.assertRaises(audio.AudioTransportError):
            with self.h.owner(): pass
        self.connect.assert_not_called(); self.assertFalse(self.h.killed())
    def test_current_capture_acknowledgment_and_valid_duration_are_required(self):
        with self.h.owner() as owner:
            with self.assertRaises(audio.AudioTransportError): owner.start_injection(self.h.wav, capture_ready=False)
            for seconds in (0, .5, 41, float("nan"), True):
                with self.assertRaises(audio.AudioTransportError): owner.start_injection(self.h.wav, capture_ready=True, max_seconds=seconds)
        self.assertIsNone(self.h.backend.rpc)
        self.assertTrue(owner.cleanup["cleanup_ok"])
    def test_packet_format_progress_and_bounded_silence_do_not_claim_asr(self):
        with self.h.owner() as owner:
            handle = owner.start_injection(self.h.wav, capture_ready=True, max_seconds=2)
            self.assertFalse(handle.wait_fixture_offered(.001))  # RPC has not consumed anything.
            with patch.object(owner.stop, "wait", return_value=False):
                packets = list(itertools.islice(self.h.backend.rpc.packets, 56))
            self.assertTrue(handle.wait_fixture_offered(.001))
            self.assertEqual(len(packets[0]), 640)
            self.assertEqual(packets[0], struct.pack("<h", 1) * 320)
            self.assertTrue(all(packet == bytes(640) for packet in packets[5:]))
            self.assertFalse(self.h.backend.rpc.done())  # Silence remains alive after the offered event.
            with self.assertRaises(ValueError): handle.wait_fixture_offered(43)
        self.assertEqual(owner.cleanup, {"rpc": "cancelled", "host_mic_off": True,
                                         "emulator_stopped": True, "cleanup_ok": True})
        self.assertNotIn("ASR", json.dumps(owner.cleanup))
    def test_generator_hard_deadline_ends_even_without_cleanup(self):
        with self.h.owner() as owner:
            handle = owner.start_injection(self.h.wav, capture_ready=True, max_seconds=2)
            with patch.object(audio.time, "monotonic", side_effect=[0, 0, 3]), patch.object(owner.stop, "wait", return_value=False):
                self.assertEqual(len(list(self.h.backend.rpc.packets)), 1)
            self.assertFalse(handle.wait_fixture_offered(.001))
    def test_one_injection_per_boot_marker_survives_new_owner_and_rpc_start_failure(self):
        self.h.backend.fail_inject = True
        with self.h.owner() as owner:
            with self.assertRaises(audio.AudioTransportError): owner.start_injection(self.h.wav, capture_ready=True)
        self.h.backend.fail_inject = False
        with self.h.owner() as owner:
            with self.assertRaisesRegex(audio.AudioTransportError, "already consumed"):
                owner.start_injection(self.h.wav, capture_ready=True)
        self.assertEqual(len(list((self.h.root / "markers").glob("*.consumed"))), 1)
    def test_boot_or_discovery_replacement_blocks_injection_and_foreign_cleanup(self):
        owner = self.h.owner(); owner.__enter__()
        self.h.boot = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        with self.assertRaises(audio.AudioTransportError): owner.start_injection(self.h.wav, capture_ready=True)
        owner.close()
        self.assertFalse(self.h.killed()); self.assertFalse(owner.cleanup["cleanup_ok"])
    def test_discovery_replacement_blocks_cleanup_even_if_boot_matches(self):
        owner = self.h.owner(); owner.__enter__()
        self.h.discovery.unlink(); self.h.write_discovery()
        owner.close()
        self.assertFalse(self.h.killed()); self.assertFalse(owner.cleanup["cleanup_ok"])
    def test_body_failure_still_cancels_rpc_restores_host_gate_and_stops_owner(self):
        with self.assertRaisesRegex(ValueError, "adapter failed"):
            with self.h.owner() as owner:
                owner.start_injection(self.h.wav, capture_ready=True)
                raise ValueError("adapter failed")
        self.assertTrue(owner.cleanup["cleanup_ok"])
        self.assertTrue(self.h.backend.closed)
    def test_gate_failure_is_reported_but_still_attempts_owned_process_stop(self):
        owner = self.h.owner(); owner.__enter__(); self.h.backend.fail_mic = True
        with self.assertRaises(audio.AudioTransportError): owner.__exit__(None, None, None)
        self.assertTrue(self.h.killed()); self.assertTrue(owner.cleanup["emulator_stopped"])
        self.assertFalse(owner.cleanup["host_mic_off"]); self.assertFalse(owner.cleanup["cleanup_ok"])
    def test_connection_failure_after_full_binding_still_stops_only_validated_owner(self):
        with patch.object(audio, "_connect", side_effect=RuntimeError("synthetic connect failure")):
            with self.assertRaises(RuntimeError):
                with self.h.owner(): pass
        self.assertTrue(self.h.killed())

class PreparePreflightTests(unittest.TestCase):
    """Execute actual shell preflight; a sentinel blocks every venv/install boundary."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sdk = self.root / "sdk"; (self.sdk / "emulator/lib").mkdir(parents=True)
        (self.sdk / "emulator/lib/emulator_controller.proto").write_text("synthetic protocol")
        self.cache = self.root / "cache"; self.cache.mkdir(mode=0o700)
        self.sentinel = self.root / "venv-invoked"
        self.bin = self.root / "bin"; self.bin.mkdir()
        import shlex
        (self.bin / "python3").write_text('#!/bin/sh\nif [ "$1" = "-m" ]; then touch ' +
            shlex.quote(str(self.sentinel)) + '; exit 97; fi\nexec ' + shlex.quote(sys.executable) + ' "$@"\n')
        (self.bin / "python3").chmod(0o700)
    def prepare(self):
        import os, subprocess
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        return subprocess.run(["bash", str(Path(__file__).resolve().parents[1] / "scripts/prepare.sh"),
                               str(self.sdk), str(self.cache)], env=env, capture_output=True, text=True)
    def test_existing_child_symlinks_fail_before_venv_or_stub_writes(self):
        for child in ("python", "stubs"):
            with self.subTest(child=child):
                target = self.root / ("external-" + child); target.mkdir()
                (target / "preserved").write_text("unchanged")
                link = self.cache / child; link.symlink_to(target)
                result = self.prepare()
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.sentinel.exists(), "venv must not run after a redirected child")
                self.assertEqual(list(target.iterdir()), [target / "preserved"])
                self.assertEqual((target / "preserved").read_text(), "unchanged")
                link.unlink()
    def test_dangling_symlink_and_nondirectory_child_are_rejected_before_venv(self):
        child = self.cache / "stubs"; child.symlink_to(self.root / "absent")
        self.assertNotEqual(self.prepare().returncode, 0); self.assertFalse(self.sentinel.exists())
        child.unlink(); child.write_text("not a directory")
        self.assertNotEqual(self.prepare().returncode, 0); self.assertFalse(self.sentinel.exists())
    def test_fresh_private_cache_reaches_only_the_venv_sentinel(self):
        self.assertEqual(self.prepare().returncode, 97)
        self.assertTrue(self.sentinel.exists())


if __name__ == "__main__":
    unittest.main()
