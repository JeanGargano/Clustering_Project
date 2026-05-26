import logging
import pandas as pd

logger = logging.getLogger(__name__)


COLUMNAS_PCA = [
    "PC1",
    "PC2",
    "PC3",
    "PC4",
    "PC5",
    "PC6",
    "PC7",
    "PC8",
    "PC9",
    "PC10",
    "PC11",
    "PC12",
    "PC13",
    "PC14",
    "PC15",
    "PC16",
    "PC17",
    "PC18",
    "PC19",
    "PC20",
]


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:

    logger.info(f"Pipeline iniciado — shape: {df.shape}")

    # Verificar columnas esperadas
    missing_cols = [
        col for col in COLUMNAS_PCA
        if col not in df.columns
    ]

    if missing_cols:
        raise ValueError(
            f"Faltan columnas PCA: {missing_cols}"
        )

    # Mantener orden correcto
    df = df[COLUMNAS_PCA]

    logger.info(f"Pipeline finalizado — shape: {df.shape}")

    return df