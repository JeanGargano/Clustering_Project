import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)

MODELS_DIR = Path("/app/models")
MODEL_NAME = "kmeans.pkl"          # modelo único empaquetado


def _load_model():
    path = MODELS_DIR / MODEL_NAME
    if not path.exists():
        raise FileNotFoundError(f"Modelo no encontrado en {path}.")
    logger.info(f"Modelo cargado: {path}")
    return joblib.load(path)


_model = _load_model()


def run_clustering(df: pd.DataFrame) -> dict:
    logger.info(f"Ejecutando clustering — shape: {df.shape}")

    labels    = _model.predict(df.values)
    metrics   = _compute_metrics(df.values, labels)
    centroids = _model.cluster_centers_.tolist()

    df_result          = df.copy()
    df_result["cluster"] = labels

    return {
        "df_with_labels": df_result,
        "metrics":        metrics,
        "centroids":      centroids,
    }


def _compute_metrics(X: np.ndarray, labels: np.ndarray) -> dict:
    metrics = {}

    if len(set(labels)) > 1:
        metrics["silhouette"] = round(silhouette_score(X, labels, sample_size=5000), 4)

    metrics["inertia"] = round(float(_model.inertia_), 4)

    unique, counts = np.unique(labels, return_counts=True)
    metrics["cluster_distribution"] = {
        int(k): int(v) for k, v in zip(unique, counts)
    }

    return metrics