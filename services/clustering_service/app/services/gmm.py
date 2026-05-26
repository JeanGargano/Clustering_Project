import logging
import numpy as np

from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


def train_gmm(
    X: np.ndarray,
    n_components: int = 4,
    random_state: int = 42
) -> GaussianMixture:

    logger.info(
        f"Entrenando GMM — shape: {X.shape}"
    )

    model = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        random_state=random_state
    )

    model.fit(X)

    logger.info("GMM entrenado correctamente.")

    return model


def predict_gmm(
    model: GaussianMixture,
    X: np.ndarray
) -> np.ndarray:

    logger.info(
        f"Generando predicciones GMM — shape: {X.shape}"
    )

    return model.predict(X)


def compute_metrics(
    X: np.ndarray,
    labels: np.ndarray
) -> dict:

    metrics = {}

    # ── Silhouette
    if len(set(labels)) > 1:

        sample_size = min(5000, len(X))

        metrics["silhouette"] = round(
            silhouette_score(
                X,
                labels,
                sample_size=sample_size
            ),
            4
        )

    # ── Distribución ─────────────────────────────
    unique, counts = np.unique(
        labels,
        return_counts=True
    )

    metrics["cluster_distribution"] = {
        int(k): int(v)
        for k, v in zip(unique, counts)
    }

    metrics["n_clusters"] = int(len(unique))

    return metrics