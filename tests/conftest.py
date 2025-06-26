import wave
import pytest


@pytest.fixture
def sample_wav(tmp_path):
    path = tmp_path / "sample.wav"
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit samples
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)  # 1 second of silence
    return path
