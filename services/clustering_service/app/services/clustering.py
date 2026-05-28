import logging
import pickle
import pathlib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)

logger = logging.getLogger(__name__)

PIPELINE_DIR  = pathlib.Path("/app/models")
PIPELINE_NAME = "pipeline.pkl"


def _load_pipeline(path: pathlib.Path):
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró '{path}'. "
            "Asegúrate de que pipeline.pkl esté en /app/models/."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def run_clustering(
    df: pd.DataFrame,
    pipeline_path: pathlib.Path = PIPELINE_DIR / PIPELINE_NAME,
) -> dict:

    logger.info("Cargando pipeline desde '%s'", pipeline_path)
    pipeline = _load_pipeline(pipeline_path)

    logger.info("Ejecutando clustering — shape: %s", df.shape)

    labels = pipeline.fit_predict(df)

    X_transformed = pipeline[:-1].transform(df)

    metrics = {
        "silhouette_score":       float(silhouette_score(X_transformed, labels)),
        "davies_bouldin_score":   float(davies_bouldin_score(X_transformed, labels)),
        "calinski_harabasz_score": float(calinski_harabasz_score(X_transformed, labels)),
        "cluster_counts": {
            int(k): int(v)
            for k, v in zip(*np.unique(labels, return_counts=True))
        },
    }

    centroids = pipeline.named_steps["kmeans"].cluster_centers_.tolist()

    df_result = df.copy()
    df_result["cluster"] = labels

    logger.info("Clustering finalizado. Distribución: %s", metrics["cluster_counts"])

    return {
        "df_with_labels": df_result,
        "metrics":        metrics,
        "centroids":      centroids,
    }