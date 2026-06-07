"""Configuration loader using Pydantic for type validation.

Pydantic v2 compatible — uses field_validator instead of the deprecated @validator.
Falls back to safe defaults if config.yaml is missing (supports demo/API-only mode).
"""

import os
from pathlib import Path
from typing import Optional, List

import yaml
from pydantic import BaseModel, Field, field_validator


class DataConfig(BaseModel):
    """Data configuration model."""
    sample_rate: int = 16000
    n_mfcc: int = 40
    n_fft: int = 2048
    hop_length: int = 512
    duration: int = 3


class CNNConfig(BaseModel):
    """CNN configuration model."""
    channels: List[int] = [32, 64, 128]
    kernel_size: int = 3
    dropout: float = 0.3


class LSTMConfig(BaseModel):
    """LSTM configuration model."""
    hidden_size: int = 128
    num_layers: int = 2
    dropout: float = 0.3


class ModelConfig(BaseModel):
    """Model configuration model."""
    type: str = "ensemble"
    cnn: CNNConfig = Field(default_factory=CNNConfig)
    lstm: LSTMConfig = Field(default_factory=LSTMConfig)


class TrainingConfig(BaseModel):
    """Training configuration model."""
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = "bce_with_logits"
    validation_split: float = 0.2
    early_stopping_patience: int = 10


class EvaluationConfig(BaseModel):
    """Evaluation configuration model."""
    metrics: List[str] = ["auc", "eer", "f1"]
    threshold: float = 0.5


class PathsConfig(BaseModel):
    """Paths configuration model."""
    data_dir: str = "./data"
    model_dir: str = "./models"
    logs_dir: str = "./logs"

    @property
    def data_raw(self):       return Path(self.data_dir) / "raw"
    @property
    def data_processed(self): return Path(self.data_dir) / "processed"
    @property
    def data_features(self):  return Path(self.data_dir) / "features"
    @property
    def model_weights(self):  return Path(self.model_dir) / "weights"


class Config(BaseModel):
    """Main configuration model."""
    data: DataConfig = Field(default_factory=DataConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    seed: int = 42

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        """Validate seed value."""
        if not isinstance(v, int) or v < 0:
            raise ValueError("Seed must be a non-negative integer")
        return v


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.
    Falls back to default Config() if the yaml file is not found —
    this allows the API and agent to run without a full training setup.

    Args:
        config_path: Path to config YAML file. If None, uses default path.

    Returns:
        Config object with validated settings.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"

    if not os.path.exists(config_path):
        # Graceful fallback — return defaults (API-only / demo mode)
        return Config()

    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f) or {}

    return Config(**config_dict)


# Alias so both names work
get_config = load_config
