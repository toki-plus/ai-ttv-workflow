import os
import asyncio
import edge_tts
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from ..utils.data_manager import DataManager
from ..config import Config

class AsyncioRunner(QThread):
    def run(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            print(f"AsyncioRunner 发生错误: {e}")

    def schedule(self, coro):
        if self.isRunning() and hasattr(self, 'loop'):
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None

    def stop_loop(self):
        if self.isRunning() and hasattr(self, 'loop'):
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.wait(2000)

class TaskSignals(QObject):
    voices_ready = pyqtSignal(list)
    voices_error = pyqtSignal(str)
    tts_finished = pyqtSignal(str, str)
    tts_error = pyqtSignal(str)
    task_progress = pyqtSignal(str)

class TTSService:
    def __init__(self, runner: AsyncioRunner, signals: TaskSignals):
        self.runner = runner
        self.signals = signals

    def fetch_voices(self):
        self.runner.schedule(self._async_fetch_voices())

    def run_tts(self, text: str, voice: str, rate: str, volume: str, pitch: str, generate_srt: bool, audio_path: str):
        self.runner.schedule(self._async_run_tts(text, voice, rate, volume, pitch, generate_srt, audio_path))

    async def _async_fetch_voices(self):
        cached_voices = DataManager.load_json(Config.VOICES_CACHE_FILE)
        if cached_voices:
            self.signals.voices_ready.emit(cached_voices)
            return

        try:
            self.signals.task_progress.emit("正在从网络获取可用语音列表...")
            voices = await edge_tts.list_voices()
            DataManager.save_json(voices, Config.VOICES_CACHE_FILE)
            self.signals.voices_ready.emit(voices)
        except Exception as e:
            self.signals.voices_error.emit(f"无法加载语音列表: {e}")

    async def _async_run_tts(self, text: str, voice: str, rate: str, volume: str, pitch: str, generate_srt: bool, audio_path: str):
        try:
            self.signals.task_progress.emit("正在初始化TTS引擎...")
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
            sub_maker = edge_tts.SubMaker()
            srt_path = ""

            self.signals.task_progress.emit("正在生成音频流...")
            with open(audio_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        sub_maker.feed(chunk)

            if generate_srt:
                self.signals.task_progress.emit("正在生成字幕文件...")
                srt_name = os.path.basename(audio_path).replace("audio_", "subtitles_").rsplit('.', 1)[0] + ".srt"
                srt_path = os.path.join(os.path.dirname(audio_path), srt_name)
                with open(srt_path, "w", encoding="utf-8") as srt_file:
                    srt_file.write(sub_maker.get_srt())

            self.signals.tts_finished.emit(audio_path, srt_path)
        except Exception as e:
            self.signals.tts_error.emit(f"音频生成失败: {e}")