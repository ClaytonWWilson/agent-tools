import sys
import types
from pathlib import Path

from social_content_extractor.extractor import ContentExtractor


def _completed(returncode=0, stdout="", stderr=""):
    return types.SimpleNamespace(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_app_cache_dir_honors_env(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("SOCIAL_CONTENT_EXTRACTOR_CACHE_DIR", str(cache_dir))

    extractor = ContentExtractor(str(tmp_path / "out"))

    assert extractor._get_app_cache_dir() == cache_dir
    assert cache_dir.exists()


def test_transcribe_audio_passes_whisper_download_root(monkeypatch, tmp_path):
    calls = []

    class FakeWhisperModel:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

        def transcribe(self, video_path, beam_size, language):
            segment = types.SimpleNamespace(start=0.0, end=1.0, text=" add salt")
            return [segment], None

    fake_faster_whisper = types.ModuleType("faster_whisper")
    fake_faster_whisper.WhisperModel = FakeWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_faster_whisper)

    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("SOCIAL_CONTENT_EXTRACTOR_CACHE_DIR", str(cache_dir))

    extractor = ContentExtractor(str(tmp_path / "out"))
    monkeypatch.setattr(extractor, "_get_whisper_device", lambda: ("cpu", "int8"))

    assert extractor.transcribe_audio("video.mp4") is True
    assert calls[0][0] == ("small",)
    assert calls[0][1]["download_root"] == str(cache_dir / "faster-whisper")
    assert (tmp_path / "out" / "transcription.txt").read_text() == (
        "[0.00-1.00]  add salt"
    )


def test_prepare_video_for_ocr_transcodes_av1(monkeypatch, tmp_path):
    ffmpeg_calls = []

    def fake_run(cmd, capture_output, text, check):
        if cmd[0] == "ffprobe":
            return _completed(stdout="av1\n")
        if cmd[0] == "ffmpeg":
            ffmpeg_calls.append(cmd)
            Path(cmd[-1]).write_bytes(b"transcoded")
            return _completed()
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("subprocess.run", fake_run)

    extractor = ContentExtractor(str(tmp_path))
    ocr_path, cleanup_path = extractor._prepare_video_for_ocr("input.mp4")

    assert ocr_path != "input.mp4"
    assert cleanup_path == ocr_path
    assert Path(ocr_path).exists()
    assert ffmpeg_calls
    assert "libx264" in ffmpeg_calls[0]


def test_prepare_video_for_ocr_keeps_non_av1(monkeypatch, tmp_path):
    def fake_run(cmd, capture_output, text, check):
        if cmd[0] == "ffprobe":
            return _completed(stdout="h264\n")
        raise AssertionError("ffmpeg should not run for h264 input")

    monkeypatch.setattr("subprocess.run", fake_run)

    extractor = ContentExtractor(str(tmp_path))
    ocr_path, cleanup_path = extractor._prepare_video_for_ocr("input.mp4")

    assert ocr_path == "input.mp4"
    assert cleanup_path is None


def test_extract_ocr_text_transcode_failure_writes_error(monkeypatch, tmp_path):
    fake_cv2 = types.ModuleType("cv2")
    fake_easyocr = types.ModuleType("easyocr")
    fake_easyocr.Reader = object
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    monkeypatch.setitem(sys.modules, "easyocr", fake_easyocr)

    def fake_run(cmd, capture_output, text, check):
        if cmd[0] == "ffprobe":
            return _completed(stdout="av1\n")
        if cmd[0] == "ffmpeg":
            return _completed(returncode=1, stderr="no encoder")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("subprocess.run", fake_run)

    extractor = ContentExtractor(str(tmp_path))

    assert extractor.extract_ocr_text("input.mp4") is False
    assert "ffmpeg failed while transcoding AV1 video for OCR: no encoder" in (
        tmp_path / "ocr.txt"
    ).read_text()


def test_extract_ocr_text_uses_readable_video_path(monkeypatch, tmp_path):
    captured_paths = []

    class FakeVideoCapture:
        def __init__(self, path):
            captured_paths.append(path)
            self.read_count = 0

        def get(self, prop):
            return 1

        def set(self, prop, value):
            return None

        def read(self):
            self.read_count += 1
            return True, "frame"

        def release(self):
            return None

    class FakeReader:
        def __init__(self, languages, gpu):
            self.languages = languages
            self.gpu = gpu

        def readtext(self, frame, detail):
            return ["salt"]

    fake_cv2 = types.ModuleType("cv2")
    fake_cv2.CAP_PROP_FRAME_COUNT = 7
    fake_cv2.CAP_PROP_POS_FRAMES = 1
    fake_cv2.VideoCapture = FakeVideoCapture
    fake_easyocr = types.ModuleType("easyocr")
    fake_easyocr.Reader = FakeReader
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    monkeypatch.setitem(sys.modules, "easyocr", fake_easyocr)

    def fake_run(cmd, capture_output, text, check):
        if cmd[0] == "ffprobe":
            return _completed(stdout="h264\n")
        raise AssertionError("ffmpeg should not run for h264 input")

    monkeypatch.setattr("subprocess.run", fake_run)

    extractor = ContentExtractor(str(tmp_path))

    assert extractor.extract_ocr_text("input.mp4") is True
    assert captured_paths == ["input.mp4"]
    assert (tmp_path / "ocr.txt").read_text() == "TEXT FOUND:\nSALT"
