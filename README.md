# Clustering Project — Análisis de Ciberataques IoT

Sistema de microservicios para análisis de ciberataques en dispositivos IoT mediante clustering multivariado e interpretación semántica con LLM.

---

## Tabla de contenidos

1. Visión General
3. Servicios                        
4. Infraestructura     
5. Flujo completo del sistema
8. Levantar el proyecto
9. API Reference — Para el frontend
10. Modelos de clustering disponibles
11. Esquema de datos en Redis

---

## Visión general

El sistema recibe datasets CSV con tráfico de red de dispositivos IoT, los procesa a través de un pipeline de limpieza, ejecuta algoritmos de clustering para identificar patrones de ciberataques y opcionalmente genera un análisis semántico usando un LLM (Llama 3.3 70B via Groq).

Cada etapa del proceso está desacoplada en microservicios independientes que se comunican a través de Kafka y comparten estado a través de Redis.

---

## Servicios

### Gateway `puerto 8001`
Punto de entrada único del sistema. Recibe todas las peticiones del frontend, las valida y las redirige al servicio correspondiente. Lee el estado de los jobs directamente desde Redis.

### Data Service `puerto 8002`
Recibe el dataset CSV del gateway y ejecuta el pipeline de preprocesamiento:
- Eliminación de duplicados
- Imputación de valores faltantes (mediana para numéricas, moda para categóricas)
- Análisis numérico y de correlación
- Eliminación de datos ruidosos
- One-Hot Encoding de variables categóricas
- Reducción dimensional con PCA (retiene 95% de varianza)

Al finalizar sube el CSV limpio a MinIO y actualiza Redis.
Publica evento en kafka, dataset.ready

### Clustering Service `puerto 8003`
Consume el tópico `dataset.ready` de Kafka. Descarga el dataset limpio desde MinIO, ejecuta el modelo de clustering seleccionado, calcula métricas de evaluación y guarda los resultados en MinIO. Actualiza Redis con el estado y las métricas.

EL modelos está empaquetado dentro del contenedor Docker como archivos `.pkl` entrenado en Colab.

### Agent Service `puerto 8004`
Consume el tópico `clustering.done` de Kafka. Descarga los resultados del clustering desde MinIO, construye un prompt con las estadísticas por cluster y llama a Llama 3.3 70B via Groq para generar un análisis semántico de los patrones encontrados. Guarda el análisis en Redis.

---

## Infraestructura

### Kafka
Broker de mensajería para comunicación asíncrona entre servicios. Opera en modo KRaft (sin Zookeeper).


### MinIO
Almacenamiento de objetos S3-compatible para archivos pesados.

| Bucket    | Contenido                | Escribe            | Lee                |
|-----------|--------------------------|--------------------|                    |
| `raw`     | CSV original del usuario | Data Service       |                    |
| `clean`   | CSV después del pipeline | Data Service       | Clustering Service |
| `results` | CSV con columna `cluster`| Clustering Service | Agent Service      |

Consola web disponible en `http://localhost:9001`

### Redis
Store en memoria para el estado de los jobs. Actúa como pizarra compartida entre todos los servicios.

Disponible en `localhost:6379`

### Kafka UI
Interfaz web para inspeccionar tópicos y mensajes de Kafka.

Disponible en `http://localhost:8080`

---

## Flujo completo del sistema

```
1. Usuario sube un CSV
       POST /api/ingest
           │
           └── Gateway → Data Service (/ingest)
               ├── Ejecuta pipeline de limpieza
               ├── Sube CSV limpio → MinIO (clean/{job_id}/clean.csv)
               ├── Crea job en Redis → { status_cleaning: "done", status: "queued" }
               └── Publica en Kafka (dataset.ready) → { job_id, minio_path }

2. Clustering Service consume dataset.ready automáticamente
           │
           └── Kafka (dataset.ready) → Clustering Service
               ├── Actualiza Redis → { status: "running" }
               ├── Descarga CSV limpio desde MinIO
               ├── Ejecuta modelo .pkl empaquetado en el contenedor
               ├── Sube results.csv → MinIO (results/{job_id}/results.csv)
               ├── Actualiza Redis → { status: "done", metrics: {...}, centroids: [...] }
               └── Publica en Kafka (clustering.done) → { job_id, result_path, metrics }

3. Frontend hace polling hasta que el clustering esté listo
       GET /api/jobs/{job_id}/status
           └── Gateway lee Redis directamente y retorna el estado actual

4. Agent Service consume clustering.done automáticamente
           │
           └── Kafka (clustering.done) → Agent Service
               ├── Actualiza Redis → { analysis_status: "running" }
               ├── Descarga results.csv desde MinIO
               ├── Construye prompt con estadísticas por cluster
               ├── Llama a Llama 3.3 70B via Groq (retry automático x3)
               └── Actualiza Redis → { analysis_status: "done", analysis: "..." }

5. Frontend obtiene el análisis
       GET /api/jobs/{job_id}/analysis
           └── Gateway lee Redis
               ├── Si analysis_status != "done" → retorna 202 (aún no disponible)
               └── Si analysis_status == "done" → retorna el texto del LLM
```


---

## Levantar el proyecto

### Requisitos previos
- Docker y Docker Compose instalados
- Archivo `.pkl` del modelo en `services/clustering_service/model/`
- Archivo `.env` configurado en la raíz

### Comandos

```bash
# Levantar todos los servicios
docker compose up -d

# Ver logs de un servicio específico
docker compose logs -f gateway
docker compose logs -f clustering_service

# Detener todo
docker compose down
```

### Verificar que todo está corriendo

| Servicio                           | URL                        |
|------------------------------------|----------------------------|
| Gateway (API)                      | http://localhost:8001      |
| Documentación automática (Swagger) | http://localhost:8001/docs |
| Kafka UI                           | http://localhost:8080      |
| MinIO consola                      | http://localhost:9001      |

---

## API Reference — Para el frontend

> Base URL: `http://localhost:8001`

---

### Endpoints

## 1. POST /api/ingest

Recibe un CSV, lo limpia y dispara el clustering. Retorna un `job_id`.

**Body** `multipart/form-data`

| Campo | Tipo | Requerido |
|-------|------|-----------|
| file  | File |    Sí     |

**Response 200**
\```json
{
    "job_id":   "3f7a1c22-84b1-4e2d-a9f0-123456789abc",
    "filename": "dataset.csv",
    "status":   "queued"
}
\```

---

## 2. GET /api/jobs/{job_id}/status

Polling del estado del clustering.

**Params**

| Parámetro | Tipo   | Descripción                         |
|-----------|--------|-------------------------------------|
| job_id    | string | UUID retornado por `/api/ingest`    |

**Response 200**
\```json
{
    "job_id":          "3f7a1c22-84b1-4e2d-a9f0-123456789abc",
    "status_cleaning": "",
    "status":          "running"
}
\```

**Estados posibles**

| status  | Descripción                        |
|---------|------------------------------------|
| queued  | En cola                            |
| running | Clustering ejecutándose            |
| done    | Completado                         |
| failed  | Error durante el proceso           |


---

## 3. GET /api/jobs/{job_id}/analysis

Retorna el análisis semántico generado por Llama 3.3 70B.
Solo disponible cuando `status: done`.

**Params**

| Parámetro | Tipo   | Descripción                      |
|-----------|--------|----------------------------------|
| job_id    | string | UUID retornado por `/api/ingest` |

**Response 200 — listo**
\```json
{
    "job_id":   "3f7a1c22-84b1-4e2d-a9f0-123456789abc",
    "status":   "done",
    "analysis": "## Análisis de Clustering IoT\n\n**Cluster 0** representa tráfico normal..."
}
\```

---

