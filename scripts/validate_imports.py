import sys
sys.path.insert(0, '.')
errors = []

# Test 1: Config loader (pydantic v2 fix)
try:
    from src.utils.config_loader import get_config
    cfg = get_config()
    print('  PASS: config_loader - defaults loaded')
except Exception as e:
    print('  FAIL: config_loader -', e)
    errors.append('config_loader')

# Test 2: DB models
try:
    from api.database.connection import SessionLocal, engine
    from api.database.models import AudioCase
    print('  PASS: database models - AudioCase table ready')
except Exception as e:
    print('  FAIL: database models -', e)
    errors.append('db_models')

# Test 3: CRUD
try:
    from api.database import crud
    print('  PASS: crud module imports')
except Exception as e:
    print('  FAIL: crud -', e)
    errors.append('crud')

# Test 4: Torch models
try:
    import torch
    from src.utils.config_loader import get_config as _get_config
    from src.models.cnn import CNNModel, build_cnn
    from src.models.lstm import LSTMModel, build_lstm
    from src.models.ensemble import EnsembleModel, BiometricsMLP, build_ensemble
    _cfg = _get_config()
    cnn  = build_cnn(_cfg)
    lstm = build_lstm(_cfg)
    ens  = build_ensemble(_cfg)
    bio  = BiometricsMLP(22, 2, 0.3)
    print('  PASS: CNN, LSTM, Ensemble, BiometricsMLP all instantiate')
except Exception as e:
    print('  FAIL: models -', e)
    errors.append('models')

# Test 5: EpisodicMemory
try:
    from agent.memory.episodic import EpisodicMemory
    em = EpisodicMemory()
    print('  PASS: EpisodicMemory instantiates')
except Exception as e:
    print('  FAIL: EpisodicMemory -', e)
    errors.append('episodic_memory')

# Test 6: RiskScorer
try:
    from agent.tools.risk_scorer import RiskScorer
    rs = RiskScorer()
    result = rs.compute({'is_fake': True, 'confidence': 0.9}, 'PATTERN ALERT — coordinated')
    s = result['score']
    l = result['level']
    print('  PASS: RiskScorer - score=' + str(s) + ' level=' + str(l))
except Exception as e:
    print('  FAIL: RiskScorer -', e)
    errors.append('risk_scorer')

# Test 7: Seed cases
try:
    from scripts.seed_demo_data import SEED_CASES
    assert len(SEED_CASES) == 2
    assert SEED_CASES[0]['case_id'] == 'DEMO0001'
    print('  PASS: seed_demo_data - ' + str(len(SEED_CASES)) + ' cases defined')
except Exception as e:
    print('  FAIL: seed_demo_data -', e)
    errors.append('seed_demo_data')

print()
if errors:
    print('FAILED:', errors)
else:
    print('ALL CHECKS PASSED')
