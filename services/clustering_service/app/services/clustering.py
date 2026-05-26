import logging
import pandas as pd

from app.services.gmm import (
    train_gmm,
    predict_gmm,
    compute_metrics
)

logger = logging.getLogger(__name__)


def run_clustering(df: pd.DataFrame) -> dict:

    logger.info(
        f"Ejecutando clustering — shape: {df.shape}"
    )

    # PCA dataset → ndarray
    X = df.values

    # ── Entrenamiento temporal
    model = train_gmm(
        X=X,
        n_components=4
    )

    # Predicciones
    labels = predict_gmm(model, X)

    # Métricas
    metrics = compute_metrics(X, labels)

    # Centroides GMM 
    centroids = model.means_.tolist()

    # Resultado final
    df_result = df.copy()

    df_result["cluster"] = labels

    logger.info("Clustering finalizado.")

    return {
        "df_with_labels": df_result,
        "metrics": metrics,
        "centroids": centroids,
    }