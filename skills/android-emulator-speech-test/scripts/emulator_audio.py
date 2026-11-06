"""Owned emulator injection primitives, NOT an application or ASR test runner.

The caller supplies and verifies current app recording readiness, stops capture,
observes the app result and validates actual input/transcript before context exit.
A successful RPC is never evidence that the app received or recognized speech.
"""
import configparser
import importlib
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import threading
import time

from audio_fixture import load_wav


class AudioTransportError(RuntimeError):
    """Fixed metadata-only error; never includes credentials or raw device output."""


def _run(*args):
    try:
        return subprocess.check_output(list(map(str, args)), text=True, timeout=15,
                                       stderr=subprocess.PIPE)
    except (OSError, subprocess.SubprocessError):
        raise AudioTransportError("System boundary command failed") from None


def _connect(stubs_dir, port, token):
    """Load clients generated locally from the selected installed SDK."""
    try:
        sys.path.insert(0, str(stubs_dir))
        import grpc
        messages = importlib.import_module("emulator_controller_pb2")
        services = importlib.import_module("emulator_controller_pb2_grpc")
        from google.protobuf.empty_pb2 import Empty
    finally:
        sys.path.remove(str(stubs_dir))
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    client = services.EmulatorControllerStub(channel)
    metadata = [("authorization", "Bearer " + token)]

    class Backend:
        def mic_off(self):
            try:
                client.setMicrophoneState(messages.MicrophoneState(realAudioEnabled=False), metadata=metadata, timeout=3)
                if client.getMicrophoneState(Empty(), metadata=metadata, timeout=3).realAudioEnabled:
                    raise AudioTransportError("Host microphone disable was not confirmed")
            except Exception:
                raise AudioTransportError("Host microphone disable was not confirmed") from None

        def inject(self, packets, timeout):
            format_ = messages.AudioFormat(samplingRate=16000, channels=messages.AudioFormat.Mono,
                format=messages.AudioFormat.AUD_FMT_S16, mode=messages.AudioFormat.MODE_UNSPECIFIED)
            def encoded():
                for frame in packets:
                    yield messages.AudioPacket(format=format_, audio=frame, timestamp=int(time.time() * 1e6))
            return client.injectAudio.future(encoded(), metadata=metadata, timeout=timeout)

        def close(self):
            channel.close()
            metadata.clear()

    return Backend()


class InjectionHandle:
    """Generator progress only. This is NOT guest input delivery or ASR evidence."""
    def __init__(self, metadata, offered):
        self.metadata = metadata
        self._offered = offered

    def wait_fixture_offered(self, timeout_seconds):
        """Wait at most 42s for WAV + 1s silence offered to RPC; false is not readiness."""
        if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 42:
            raise ValueError("Explicit positive wait bound of at most 42 seconds required")
        return self._offered.wait(timeout_seconds)


class OwnedEmulatorAudio:
    """One owned boot, one bounded injection; context exit stops that owned emulator.

    All directories must be explicit absolute paths. marker_dir is durable private
    LOCAL cache, not temporary-per-attempt: keep it across calls on the same boot.
    No app installation, permission, launch, model download or UI is performed here.
    """
    def __init__(self, *, sdk, target, avd, avd_dir, discovery, stubs_dir, marker_dir):
        self.sdk, self.avd_dir, self.discovery = map(Path, (sdk, avd_dir, discovery))
        self.stubs_dir, self.marker_dir = map(Path, (stubs_dir, marker_dir))
        self.target, self.avd = target, avd
        self.backend = self.rpc = None
        self.stop = threading.Event()
        self.owned = self.entered = self.closed = False
        self.pid = self.port = self.boot = self.discovery_identity = None
        self.cleanup = {"rpc": "not_started", "host_mic_off": None,
                        "emulator_stopped": None, "cleanup_ok": False}

    def _device(self, *args):
        return _run(self.sdk / "platform-tools/adb", "-s", self.target, *args)

    def _read_discovery(self):
        try:
            fd = os.open(self.discovery, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd) as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError()
                data = stream.read(65537)
                if len(data) > 65536:
                    raise ValueError()
            config = configparser.ConfigParser(interpolation=None)
            config.read_string("[emulator]\n" + data)
            return config["emulator"], (info.st_dev, info.st_ino, info.st_mtime_ns)
        except (OSError, ValueError, configparser.Error):
            raise AudioTransportError("Expected private owned regular current discovery file") from None

    def _listener(self):
        result = _run("lsof", "-nP", "-a", "-p", self.pid, f"-iTCP:{self.port}", "-sTCP:LISTEN", "-Fn")
        names = [line[1:] for line in result.splitlines() if line.startswith("n")]
        if names != [f"127.0.0.1:{self.port}"]:
            raise AudioTransportError("Expected exact PID loopback-only gRPC listener")

    def _current_owner(self):
        _, identity = self._read_discovery()
        if identity != self.discovery_identity or self._device("shell", "cat", "/proc/sys/kernel/random/boot_id").strip() != self.boot:
            raise AudioTransportError("Owned emulator incarnation changed")
        self._listener()

    def __enter__(self):
        if self.entered or self.closed:
            raise AudioTransportError("Use a new context owner")
        self.entered = True
        try:
            if not isinstance(self.target, str) or not re.fullmatch(r"emulator-[1-9][0-9]*", self.target):
                raise AudioTransportError("Explicit emulator serial required")
            if not self.avd or not all(p.is_absolute() for p in (self.sdk, self.avd_dir, self.discovery, self.stubs_dir, self.marker_dir)):
                raise AudioTransportError("Explicit AVD and absolute paths required")
            match = re.fullmatch(r"pid_([1-9][0-9]*)\.ini", self.discovery.name)
            if not match:
                raise AudioTransportError("Exact PID discovery filename required")
            self.pid = int(match[1])
            if self._device("shell", "getprop", "ro.kernel.qemu").strip() != "1":
                raise AudioTransportError("Physical devices are forbidden")
            if self._device("emu", "avd", "name").splitlines()[0].strip() != self.avd:
                raise AudioTransportError("AVD name mismatch")
            emu, self.discovery_identity = self._read_discovery()
            try:
                self.port = int(emu["grpc.port"])
                token = emu["grpc.token"]
                bound = (emu["avd.name"] == self.avd and Path(emu["avd.dir"]).is_absolute()
                         and Path(emu["avd.dir"]).resolve() == self.avd_dir.resolve()
                         and emu["port.serial"] == self.target.split("-")[1]
                         and "-grpc-use-token" in shlex.split(emu["cmdline"])
                         and 1 <= self.port <= 65535 and 0 < len(token) < 8192
                         and "\n" not in token and "\r" not in token)
            except (KeyError, ValueError):
                bound = False
            if not bound:
                raise AudioTransportError("Discovery does not bind the requested owned emulator")
            self._listener()
            self.boot = self._device("shell", "cat", "/proc/sys/kernel/random/boot_id").strip()
            if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", self.boot):
                raise AudioTransportError("Unknown boot identity")
            # Only now may cleanup address this emulator. Partial validation cannot kill a foreign target.
            self.owned = True
            self.marker_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = self.marker_dir.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise AudioTransportError("Marker directory must be private and owned")
            self.backend = _connect(self.stubs_dir, self.port, token)
            self.backend.mic_off()
            return self
        except Exception:
            self.close()
            raise

    def start_injection(self, wav_path, *, capture_ready, max_seconds=20):
        """Start only AFTER caller proves current actual recording, not merely a ready button.

        capture_ready is a caller acknowledgement, not independently verified here.
        The stream sends WAV then silence until cancellation or the finite bound.
        Keep this context open while the adapter observes Finish/results and stops capture.
        """
        if not self.backend or self.closed or self.rpc is not None:
            raise AudioTransportError("No fresh connected injection context")
        if capture_ready is not True:
            raise AudioTransportError("Caller must verify actual current recording before injection")
        metadata, pcm = load_wav(wav_path)
        if type(max_seconds) not in (int, float) or not metadata["frames"] / 16000 + 1 <= max_seconds <= 40:
            raise AudioTransportError("Injection bound must include audio plus silence and be at most 40 seconds")
        self._current_owner()
        marker = self.marker_dir / f"{self.boot}.consumed"
        try:
            with marker.open("x") as consumed:
                consumed.write("consumed\n")
        except FileExistsError:
            raise AudioTransportError("Injection already consumed for this boot; do not remove the marker") from None
        self.backend.mic_off()
        offered = threading.Event()
        def packets():
            deadline, offset = time.monotonic() + max_seconds, 0
            fixture_packets = (len(pcm) + 639) // 640 + 50
            while not self.stop.is_set() and time.monotonic() < deadline:
                yield pcm[offset:offset + 640].ljust(640, b"\0") if offset < len(pcm) else bytes(640)
                offset += 640
                if offset // 640 >= fixture_packets:
                    offered.set()
                # Continue paced zeros after the event until caller cleanup/hard deadline.
                self.stop.wait(.02)
        try:
            self.rpc = self.backend.inject(packets(), timeout=max_seconds + 2)
        except Exception:
            raise AudioTransportError("Injection RPC could not start; boot marker remains consumed") from None
        return InjectionHandle(metadata, offered)

    def close(self):
        """Bounded cleanup; report only transport/host-gate/emulator ownership facts."""
        if self.closed:
            return self.cleanup
        self.closed = True
        self.stop.set()
        if self.rpc is not None:
            try:
                self.rpc.cancel()
                self.cleanup["rpc"] = "cancelled" if self.rpc.cancelled() else "completed" if self.rpc.done() else "unconfirmed"
            except Exception:
                self.cleanup["rpc"] = "unconfirmed"
        if self.owned:
            try:
                self._current_owner()
                owner_current = True
            except Exception:
                owner_current = False
                self.cleanup["emulator_stopped"] = False
            if owner_current:
                if self.backend:
                    try:
                        self.backend.mic_off()
                        self.cleanup["host_mic_off"] = True
                    except Exception:
                        self.cleanup["host_mic_off"] = False
                # Still attempt owned process teardown when host-gate cleanup fails.
                try:
                    self._device("emu", "kill")
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        try:
                            os.kill(self.pid, 0)
                        except ProcessLookupError:
                            self.cleanup["emulator_stopped"] = True
                            break
                        time.sleep(.2)
                    else:
                        self.cleanup["emulator_stopped"] = False
                except Exception:
                    self.cleanup["emulator_stopped"] = False
        if self.backend:
            try:
                self.backend.close()
            except Exception:
                self.cleanup["host_mic_off"] = False
        self.cleanup["cleanup_ok"] = (self.cleanup["rpc"] in ("not_started", "cancelled", "completed")
            and self.cleanup["host_mic_off"] is True and self.cleanup["emulator_stopped"] is True)
        return self.cleanup

    def __exit__(self, kind, value, traceback):
        report = self.close()
        if kind is None and not report["cleanup_ok"]:
            raise AudioTransportError("Transport cleanup incomplete; inspect the cleanup report")
        return False
