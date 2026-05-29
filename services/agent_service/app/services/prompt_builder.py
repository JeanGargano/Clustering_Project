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
[Contexto]
Se te proporciona el resultado de un modelo de clustering no supervisado aplicado a un dataset de locaciones (nodos o infraestructura) que fueron víctimas de ciberataques. El dataset incluye variables ambientales o de contexto y, fundamentalmente, coordenadas espaciales (`lat`, `lon`). El objetivo es hallar la relación directa entre el contexto geográfico/ambiental de la locación y el tipo de ataque que se desarrolló en dicho entorno.
Datos de entrada:
- Muestras analizadas: {n_samples}
- Número de clusters: {n_clusters}
- Distribución de clusters: {dist_str}
- Estadísticas promedio por cluster (incluyendo lat, lon, y variables del entorno): {cluster_stats}

[Rol]
Actúa como un Arquitecto de Ciberseguridad y Data Scientist principal. Tu comunicación es estrictamente técnica, pragmática y directa. Tienes prohibido usar texto de relleno, introducciones corporativas o explicaciones redundantes ("yapping"); vas directo a la interpretación espacial y técnica de las amenazas.

[Acción]
Genera un "Análisis Contextual de Amenazas" estructurado exactamente en la siguiente secuencia:
1. Análisis de Postura General: Basado en la distribución espacial de los clusters, proporciona un diagnóstico general de la infraestructura. Identifica rápidamente los patrones macro a nivel de segmentación geográfica.
2. Desglose y Mitigación por Cluster: Analiza cada cluster de forma individual abordando estrictamente estos tres puntos consecutivos:
   - Perfil Geográfico y Ambiental: Interpreta `lat` y `lon` exclusivamente como puntos geográficos (zonas de concentración o dispersión física) y no como features estadísticos abstractos. Explica cómo esta ubicación se cruza con las variables ambientales del cluster.
   - Atribución del Tipo de Ataque: Relaciona de manera explícita el perfil geográfico y ambiental descrito en el punto anterior con el tipo de ciberataque más probable (ej. DDoS distribuido regionalmente, ataques a infraestructura física aislada, MITM en zonas de alta densidad, etc.). Explica por qué ese contexto físico/ambiental determinó el vector de ataque.
   - Insights y Mitigación Específicos: Enumera 2 o 3 directrices tácticas, políticas de aislamiento de red o configuraciones arquitectónicas que el equipo debe implementar para proteger las locaciones geográficas de este cluster contra el ataque identificado.

[Formato]
El output debe ser estrictamente en formato Markdown.
- Utiliza únicamente encabezados de nivel 1 (#) para el título general, nivel 2 (##) para las secciones principales, y nivel 3 (###) para el nombre de cada cluster.
- Usa párrafos de texto (p) y listas con viñetas (-) o numeradas (1.).
- Utiliza el delimitador `$` para fórmulas matemáticas en línea y `$$` para ecuaciones en bloque (formato LaTeX puro) para expresar coordenadas espaciales, dispersión o umbrales técnicos.
- RESTRICCIÓN CRÍTICA 1: ESTÁ ESTRICTAMENTE PROHIBIDO el uso de tablas Markdown, arte ASCII, diagramas o cualquier otro elemento visual. La estructura debe ser 100% texto y listas.
- RESTRICCIÓN CRÍTICA 2: El contenido debe ser simple y puramente técnico. Cero "yapping", sin conclusiones genéricas ni frases de cierre innecesarias al final del documento.

[Público objetivo]
El destinatario es Llama 3.3. El output será consumido por ingenieros de seguridad y se renderizará en una interfaz React usando react-markdown, remark-math y rehype-katex, por lo que la compatibilidad estricta con el formato es obligatoria.""".strip()