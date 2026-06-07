# VoiceGuard — Customer Support Intelligence Agent

**Problem Statement #7:** Customers expect organisations to remember previous interactions and receive consistent, personalised support — not repeat themselves every time they contact you.

VoiceGuard is an **agentic support system with three memory layers**:

| Memory | What it stores | Why it matters |
|--------|----------------|----------------|
| **Episodic** (SQLite) | Every ticket: customer, team, issue, outcome | "You've contacted us about this before" |
| **Semantic** (ChromaDB) | Policies, known issues, resolution playbooks | Instant access to the right answer |
| **Pattern** (engine) | Repeat tickets, escalation trends by team | Spots recurring issues before they explode |

Audio analysis (CNN/LSTM ensemble) is a **background signal** the agent uses when voice recordings are submitted — not the product. The product is **memory-driven support that gets smarter with every interaction**.

### Quick demo

```bash
bash scripts/setup_env.sh
uvicorn api.main:app --reload --port 8000
# Open http://127.0.0.1:8000
```

### Pitch (60 seconds)

> "Upload a support ticket with an audio attachment. VoiceGuard recalls prior interactions for that team, searches the knowledge base, detects repeat-issue patterns, and the agent delivers a personalised resolution — without making the customer explain everything again. Without memory, you have a chatbot. With memory, you have an agent that learns."

---

## 📋 Project Structure

```
deepfake-audio-detector/
├── configs/config.yaml          ← All hyperparameters in one place
├── src/
│   ├── features/                ← MFCC, spectrograms, audio processing
│   ├── models/                  ← CNN, LSTM, ensemble architectures
│   ├── training/                ← Training loops, dataloaders
│   ├── evaluation/              ← EER, AUC, F1 metrics
│   └── utils/
│       ├── config_loader.py     ← Typed config via Pydantic
│       ├── logger.py            ← Loguru centralized logging
│       └── seed.py              ← Reproducibility helper
├── api/                         ← FastAPI backend service
├── frontend/                    ← Web UI
├── docker/docker-compose.yml    ← One command spins all services
├── scripts/setup_env.bat        ← Windows one-click setup
├── .github/workflows/ci.yml     ← Auto lint + test on every push
└── .pre-commit-config.yaml      ← Black + isort + flake8 on commit
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git
- Docker (optional)

### Windows Setup

Run the one-click setup script:

```bash
scripts\setup_env.bat
```

This will:

1. Create a virtual environment
2. Install all dependencies
3. Set up pre-commit hooks

### Manual Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

## 🏗️ Team Responsibilities

- **Person A**: Machine Learning (features, models, training, evaluation)
- **Person B**: API Backend
- **Person C**: Frontend UI

## ⚙️ Configuration

All hyperparameters are centralized in `configs/config.yaml`:

- Data preprocessing settings
- Model architecture
- Training hyperparameters
- Evaluation metrics

Edit this file to experiment with different configurations.

## 📦 Main Components

### Features Module (`src/features/`)

- Audio preprocessing
- MFCC extraction
- Spectrogram generation
- Feature normalization

### Models Module (`src/models/`)

- CNN architecture
- LSTM architecture
- Ensemble models

### Training Module (`src/training/`)

- DataLoader setup
- Training loops
- Validation logic
- Checkpoint management

### Evaluation Module (`src/evaluation/`)

- EER (Equal Error Rate)
- AUC metrics
- F1 score calculation
- ROC curve plotting

## 🔧 Development Workflow

### Code Quality

- **Black**: Code formatting (auto-fix with `black .`)
- **isort**: Import sorting (auto-fix with `isort .`)
- **Flake8**: Linting (`flake8 .`)
- **mypy**: Type checking (`mypy src/`)

Pre-commit hooks run automatically on `git commit`.

### Testing

```bash
pytest tests/ -v --cov=src
```

### CI/CD

GitHub Actions automatically run on every push:

- Black formatting check
- isort import check
- Flake8 linting
- mypy type checking
- pytest tests
- Coverage reporting

## 🐳 Docker

Run all services with one command:

```bash
docker-compose up
```

This starts:

- Backend API (port 8000)
- Frontend (port 3000)
- PostgreSQL database (port 5432)

## 📝 Logging

Uses **loguru** for centralized logging:

- Console output: Color-coded, formatted messages
- File output: `logs/app.log` with rotation

Configure in `src/utils/logger.py`.

## 🎯 Reproducibility

Set seed globally:

```python
from src.utils import set_seed
set_seed(42)
```

This ensures reproducible results across:

- Python random
- NumPy
- PyTorch
- CUDA operations

## 📚 Configuration Loading

Load config with type validation:

```python
from src.utils import load_config

config = load_config()  # Loads from configs/config.yaml
print(config.training.batch_size)  # 32
```

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Code is auto-formatted and linted
4. Run tests: `pytest`
5. Push and create PR

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

For issues or questions, open a GitHub issue or contact the team.
