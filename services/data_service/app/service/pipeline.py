import logging
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de preprocesamiento.
    Las etapas independientes corren en paralelo con ThreadPoolExecutor.
    """
    logger.info(f"Pipeline iniciado — shape: {df.shape}")

    # Etapas secuenciales (cada una depende de la anterior)
    df = _remove_duplicates(df)
    df = _handle_missing(df)

    # Etapas independientes en paralelo
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_num  = executor.submit(_numeric_analysis, df)
        future_corr = executor.submit(_correlation_analysis, df)
        future_num.result()   # solo logging, no modifica df
        future_corr.result()  # solo logging, no modifica df

    df = _remove_noisy(df)
    df = _encode_categoricals(df)
    df = _apply_pca(df)

    logger.info(f"Pipeline finalizado — shape: {df.shape}")
    return df


# ── Etapas

def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Duplicados eliminados: {before - len(df)}")
    return df.reset_index(drop=True)


def _handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        logger.info("Sin valores faltantes.")
        return df

    logger.info(f"Valores faltantes:\n{missing}")

    num_cols = df.select_dtypes(include=np.number).columns
    cat_cols = df.select_dtypes(include="object").columns

    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df[cat_cols] = df[cat_cols].fillna(df[cat_cols].mode().iloc[0])
    return df


def _numeric_analysis(df: pd.DataFrame) -> None:
    num_df = df.select_dtypes(include=np.number)
    logger.info(f"Análisis numérico:\n{num_df.describe().T[['mean','std','min','max']]}")


def _correlation_analysis(df: pd.DataFrame) -> None:
    num_df = df.select_dtypes(include=np.number)
    corr = num_df.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    high_corr = [(c, r, round(upper.loc[r, c], 3))
                 for c in upper.columns
                 for r in upper.index
                 if pd.notna(upper.loc[r, c]) and upper.loc[r, c] > 0.95]
    if high_corr:
        logger.info(f"Pares altamente correlacionados (>0.95): {high_corr}")


def _remove_noisy(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=np.number).columns
    before = len(df)
    z_scores = np.abs((df[num_cols] - df[num_cols].mean()) / df[num_cols].std())
    df = df[(z_scores < 3).all(axis=1)]

    logger.info(f"Filas ruidosas eliminadas (z-score > 3): {before - len(df)}")
    return df.reset_index(drop=True)


def _encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if not cat_cols:
        logger.info("Sin columnas categóricas para encodear.")
        return df

    logger.info(f"One-Hot Encoding en: {cat_cols}")
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True, dtype=np.float32)
    return df


def _apply_pca(df: pd.DataFrame, variance_threshold: float = 0.95) -> pd.DataFrame:
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)

    pca = PCA(n_components=variance_threshold, svd_solver="full")
    reduced = pca.fit_transform(scaled)

    n_components = pca.n_components_
    logger.info(f"PCA: {df.shape[1]} → {n_components} componentes ({int(variance_threshold*100)}% varianza)")

    cols = [f"pc_{i+1}" for i in range(n_components)]
    return pd.DataFrame(reduced, columns=cols)