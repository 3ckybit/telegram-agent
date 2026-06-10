import asyncio
import os
import tempfile
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel("small", device="cpu", compute_type="int8")


async def transcribe_audio(file_path: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, file_path)


def _transcribe_sync(file_path: str) -> str:
    model = _get_whisper_model()
    segments, _ = model.transcribe(file_path, beam_size=5)
    return " ".join(s.text for s in segments).strip()


async def download_and_transcribe(voice_file, bot) -> str:
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        tg_file = await bot.get_file(voice_file.file_id)
        await tg_file.download_to_drive(tmp_path)
        return await transcribe_audio(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
