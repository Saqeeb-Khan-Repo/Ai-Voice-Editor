from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, Tuple

class PipelineStage(ABC):
    """
    Abstract base class for all audio enhancement pipeline stages.
    Every stage must have:
    - Clear responsibility
    - Input validation
    - Configurable parameters
    - Error handling & logging
    - Unit testability
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process(
        self, audio: np.ndarray, sample_rate: int, config: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Processes audio array.
        Returns:
            processed_audio: np.ndarray with same shape/channels or specified transformation
            stage_metadata: Dict with stage-specific diagnostics
        """
        pass

    def validate_audio(self, audio: np.ndarray) -> None:
        if not isinstance(audio, np.ndarray):
            raise TypeError(f"Stage {self.name}: Audio must be a numpy ndarray")
        if np.any(np.isnan(audio)):
            raise ValueError(f"Stage {self.name}: Audio contains NaN values")
        if np.any(np.isinf(audio)):
            raise ValueError(f"Stage {self.name}: Audio contains Infinite values")
