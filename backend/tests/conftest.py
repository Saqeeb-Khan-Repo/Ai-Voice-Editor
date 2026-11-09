import os
import shutil
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.core.config import settings
from app.database.session import init_db
from app.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    os.makedirs(settings.ORIGINALS_DIR, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    os.makedirs(settings.TEMPORARY_DIR, exist_ok=True)
    init_db()
    yield

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def synthetic_audio_factory():
    """Generates synthetic test signals for rigorous DSP and pipeline verification."""
    def _create(
        signal_type: str = "clean_vocal",
        duration: float = 2.0,
        sample_rate: int = 44100,
        stereo: bool = False
    ) -> np.ndarray:
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        if signal_type == "clean_vocal":
            sig = (
                0.4 * np.sin(2 * np.pi * 220 * t) +
                0.25 * np.sin(2 * np.pi * 440 * t) +
                0.15 * np.sin(2 * np.pi * 660 * t) +
                0.1 * np.sin(2 * np.pi * 880 * t)
            )
        elif signal_type == "noisy":
            vocal = 0.3 * np.sin(2 * np.pi * 261.63 * t)
            noise = 0.08 * np.random.randn(len(t))
            sig = vocal + noise
        elif signal_type == "quiet":
            sig = 0.01 * np.sin(2 * np.pi * 330 * t)
        elif signal_type == "clipped":
            clean = 1.8 * np.sin(2 * np.pi * 220 * t)
            sig = np.clip(clean, -1.0, 1.0)
        elif signal_type == "silent":
            sig = np.zeros(len(t))
        elif signal_type == "rumble":
            vocal = 0.3 * np.sin(2 * np.pi * 220 * t)
            sub_rumble = 0.3 * np.sin(2 * np.pi * 35 * t)
            sig = vocal + sub_rumble
        elif signal_type == "sibilant":
            vocal = 0.3 * np.sin(2 * np.pi * 220 * t)
            sibilance = 0.25 * np.sin(2 * np.pi * 7000 * t)
            sig = vocal + sibilance
        else:
            sig = 0.3 * np.sin(2 * np.pi * 440 * t)

        sig = sig.astype(np.float32)
        if stereo:
            sig_r = np.roll(sig, 10)
            return np.column_stack([sig, sig_r])
        return sig

    return _create
