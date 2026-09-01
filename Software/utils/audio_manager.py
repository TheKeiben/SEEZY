import subprocess
import queue
import logging
from PyQt6.QtCore import QThread

logger = logging.getLogger("SEEZY")

class AudioManager(QThread):
    def __init__(self):
        super().__init__()
        self.speech_queue = queue.Queue()
        self.running = True

    def speak(self, text: str):
        """Adds a phrase to the speech queue."""
        self.speech_queue.put(text)

    def run(self):
        """Background loop that processes the speech queue."""
        while self.running:
            try:
                # Wait for 0.5 seconds for a new phrase
                text = self.speech_queue.get(timeout=0.5)
                # Call the native espeak engine safely
                subprocess.run(['espeak', '-v', 'en', '-s', '150', text], stderr=subprocess.DEVNULL)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[Audio] TTS Error: {e}")

    def stop(self):
        """Safely shuts down the audio thread."""
        self.running = False
        self.quit()
        self.wait()