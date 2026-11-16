import os
import sys
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(ROOT, "backend")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.transcription import _ensure_ffmpeg_on_path


class WhisperPyFfmpegPathTests(unittest.TestCase):
    """whisper-py shells out to a bare `ffmpeg`. The native install keeps its
    ffmpeg out of PATH and passes it as PODCLI_FFMPEG, so the directory has to
    be prepended before openai-whisper decodes anything."""

    def test_prepends_the_hermetic_ffmpeg_directory(self):
        env = {
            "PODCLI_FFMPEG": "/opt/podcli/runtime/ffmpeg/ffmpeg",
            "PATH": "/usr/bin:/bin",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("FFMPEG_PATH", None)
            _ensure_ffmpeg_on_path()
            self.assertEqual(
                os.environ["PATH"], "/opt/podcli/runtime/ffmpeg:/usr/bin:/bin"
            )

    def test_uses_ffmpeg_path_when_podcli_ffmpeg_is_absent(self):
        env = {
            "FFMPEG_PATH": "/opt/ffmpeg/ffmpeg",
            "PATH": "/usr/bin",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("PODCLI_FFMPEG", None)
            _ensure_ffmpeg_on_path()
            self.assertEqual(os.environ["PATH"], "/opt/ffmpeg:/usr/bin")

    def test_is_idempotent(self):
        env = {
            "PODCLI_FFMPEG": "/opt/ffmpeg/ffmpeg",
            "PATH": "/opt/ffmpeg:/usr/bin",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("FFMPEG_PATH", None)
            _ensure_ffmpeg_on_path()
            self.assertEqual(os.environ["PATH"], "/opt/ffmpeg:/usr/bin")

    def test_no_op_when_ffmpeg_is_unknown(self):
        with mock.patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=False):
            os.environ.pop("PODCLI_FFMPEG", None)
            os.environ.pop("FFMPEG_PATH", None)
            _ensure_ffmpeg_on_path()
            self.assertEqual(os.environ["PATH"], "/usr/bin")


if __name__ == "__main__":
    unittest.main()
