"""Local synthetic audio fixture tools. Validation proves format, never ASR quality."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import wave


def load_wav(path):
    """Return metadata and transient PCM for a nonempty, nonzero 0.1–10s fixture."""
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
            raise ValueError("Expected uncompressed mono PCM16LE 16kHz WAV")
        frames = wav.getnframes()
        if not 1600 <= frames <= 160000:
            raise ValueError("Expected 0.1–10 seconds of audio")
        pcm = wav.readframes(frames)
    if len(pcm) != frames * 2:
        raise ValueError("Incomplete PCM frames")
    nonzero = sum(value != 0 for value, in struct.iter_unpack("<h", pcm))
    if not nonzero:
        raise ValueError("Silent fixture")
    return {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "frames": frames, "rate": 16000, "channels": 1, "sampleBytes": 2,
            "nonzeroSamples": nonzero}, pcm


def synthesize(phrase, voice, output):
    """Use the installed macOS say voice. Never overwrite an existing fixture."""
    if not phrase.strip() or not voice.strip():
        raise ValueError("Explicit nonempty phrase and installed voice are required")
    output = Path(output)
    if os.path.lexists(output):
        raise FileExistsError("Fixture already exists")
    with tempfile.TemporaryDirectory(prefix="speech-fixture-", dir=output.parent) as temp:
        candidate = Path(temp) / "fixture.wav"
        # Text goes through stdin, never a shell command or an option argument.
        result = subprocess.run(["say", "-v", voice, "--file-format=WAVE", "--data-format=LEI16@16000",
                                 "-r", "145", "-o", str(candidate)], input=phrase, text=True,
                                capture_output=True, timeout=60)
        if result.returncode:
            raise ValueError("Local speech synthesis failed")
        metadata, _ = load_wav(candidate)
        candidate.chmod(0o600)
        # Atomic no-overwrite publication on the same filesystem.
        os.link(candidate, output)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    validate = actions.add_parser("validate")
    validate.add_argument("--wav", required=True)
    synth = actions.add_parser("synthesize")
    synth.add_argument("--phrase", required=True)
    synth.add_argument("--voice", required=True)
    synth.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = load_wav(args.wav)[0] if args.action == "validate" else synthesize(args.phrase, args.voice, args.output)
    except (OSError, ValueError, EOFError, wave.Error, subprocess.SubprocessError):
        parser.exit(1, "Audio fixture operation failed; check format, local voice and a new output path.\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
