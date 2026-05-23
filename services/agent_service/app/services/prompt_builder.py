import pandas as pd


def build_prompt(df: pd.DataFrame, metrics: dict) -> str:
    n_clusters    = df["cluster"].nunique()
    n_samples     = len(df)
    distribution  = metrics.get("cluster_distribution", {})
    silhouette    = metrics.get("silhouette", "N/A")
    inertia       = metrics.get("inertia", None)
    log_likelihood = metrics.get("log_likelihood", None)

    # Estadísticas por cluster
    cluster_stats = (
        df.groupby("cluster")
        .mean(numeric_only=True)
        .drop(columns=["cluster"], errors="ignore")
        .round(4)
        .to_string()
    )

    # Métricas del modelo
    model_metrics = f"- Silhouette Score: {silhouette}\n"
    if inertia:
        model_metrics += f"- Inercia (KMeans): {inertia}\n"
    if log_likelihood:
        model_metrics += f"- Log-Likelihood (GMM): {log_likelihood}\n"

    # Distribución por cluster
    dist_str = "\n".join(
        f"  Cluster {k}: {v} muestras ({round(v/n_samples*100, 1)}%)"
        for k, v in distribution.items()
    )

    return f"""
Analiza los siguientes resultados de clustering aplicado a tráfico de red de dispositivos IoT
con el objetivo de detectar patrones de ciberataques.

## Configuración del modelo
- Total de muestras analizadas: {n_samples}
- Número de clusters encontrados: {n_clusters}

## Métricas de evaluación
{model_metrics}

## Distribución de clusters
{dist_str}

## Estadísticas promedio por cluster
{cluster_stats}

## Instrucciones de análisis
1. Identifica cuáles clusters representan comportamiento normal y cuáles representan posibles ataques.
2. Describe las características principales de cada cluster basándote en las estadísticas.
3. Indica qué tipo de ataque podría representar cada cluster sospechoso (DDoS, port scanning, MITM, etc.).
4. Evalúa la calidad del clustering basándote en las métricas.
5. Da recomendaciones concretas de seguridad basadas en los patrones encontrados.
""".strip()