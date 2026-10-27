"""Text-to-speech. Offline engine (pyttsx3) first, online gTTS as fallback. Fails gracefully."""
import os, re, subprocess, sys, tempfile


def clean_for_speech(text):
    text = re.sub(r"[=\-*#_]{3,}", " ", text)
    text = text.replace("&", " and ").replace("/", " or ")
    return re.sub(r"\s+", " ", text).strip()


class Speaker:
    def __init__(self, enabled=False, rate=160, lang="en"):
        self.enabled, self.rate, self.lang = enabled, rate, lang
        self.engine_name = None
        self._engine = None
        self._init()

    def _init(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self.engine_name = "pyttsx3 (offline)"
            return
        except Exception:
            self._engine = None
        try:
            import gtts  # noqa: F401
            self.engine_name = "gTTS (online)"
        except Exception:
            self.engine_name = None

    @property
    def available(self):
        return self.engine_name is not None

    def speak(self, text):
        if not self.enabled:
            return False
        text = clean_for_speech(text)
        if not self.available:
            print("[TTS] No TTS engine found. Run: pip install pyttsx3  (or gTTS)")
            return False
        try:
            if self._engine is not None:
                self._engine.say(text)
                self._engine.runAndWait()
                return True
            path = os.path.join(tempfile.gettempdir(), "first_aid_tts.mp3")
            self.save(text, path)
            self._play(path)
            return True
        except Exception as e:
            print(f"[TTS] Could not speak: {e}")
            return False

    def save(self, text, path):
        """Save speech to an audio file (mp3 via gTTS, wav/aiff via pyttsx3)."""
        text = clean_for_speech(text)
        if self._engine is not None and not path.endswith(".mp3"):
            self._engine.save_to_file(text, path)
            self._engine.runAndWait()
            return path
        from gtts import gTTS
        gTTS(text=text, lang=self.lang).save(path)
        return path

    @staticmethod
    def _play(path):
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.call(["afplay", path])
        else:
            subprocess.call(["xdg-open", path])
