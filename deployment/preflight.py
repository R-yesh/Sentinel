"""Run from repository root before serving. Checks assets; never calls Gemini."""
import hashlib
from pathlib import Path
import warnings

from sklearn.exceptions import InconsistentVersionWarning

from apps.api.app.services.datasets import DatasetRepository
from ml.drift.predictor import load_model, predict_168h

MODEL_SHA256 = '3364e86ea62626856530fd6bd48e3c5c5ec372144f978425c2e1433b60dd84de'


def check_runtime():
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        raise RuntimeError('Start Sentinel from repository root; the existing predictor uses a relative model path.')
    model_path = root / 'ml/drift/random_forest_model.joblib'
    if not model_path.is_file():
        raise RuntimeError('Required trained model missing. Package the existing artifact; do not retrain during deployment.')
    if hashlib.sha256(model_path.read_bytes()).hexdigest() != MODEL_SHA256:
        raise RuntimeError('Model checksum differs from the audited artifact; verify provenance before deployment.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', InconsistentVersionWarning)
        model = load_model()
        dataset = DatasetRepository().load('synthetic-burnin')
        if dataset.empty:
            raise RuntimeError('Dataset is empty.')
        predictions, uncertainty = predict_168h(dataset.iloc[:1])
    print(f'Runtime assets verified: {len(dataset)} components, {len(model.estimators_)} trees, prediction shape {predictions.shape}, uncertainty shape {uncertainty.shape}.')


if __name__ == '__main__':
    check_runtime()
