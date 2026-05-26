import React from 'react';
import Geo from '../sections/geo'; 
import Report from '../sections/report';
import Papa from 'papaparse';
import './styles/dashboard.css';
import { useState, useEffect } from 'react';

const Dashboard = () => {
    // En tu Dashboard.jsx, puedes probarlo así temporalmente:
const [llmText, setLlmText] = useState(`
# Reporte de Inteligencia de Amenazas: Clustering IoT

> **Nota del Sistema:** Análisis generado automáticamente utilizando *Llama 3.3* basado en agrupaciones espaciales multivariadas y variables contextuales.

## Resumen Ejecutivo
El modelo de *Machine Learning* ha identificado **3 clústeres principales** de actividad anómala en la infraestructura de red. La métrica de calidad de la agrupación (Coeficiente de Silhouette) alcanzó un valor óptimo que indica una alta cohesión interna y separación:

$$S(i) = \\frac{b(i) - a(i)}{\\max\\{a(i), b(i)\\}} \\approx 0.78$$

Esta separación matemática confirma que los ataques no son aleatorios, sino que están altamente correlacionados con el tipo de infraestructura física.

---

## Perfiles de Clúster Identificados

### 🔵 Clúster 0: Botnet y DDoS en Zonas Residenciales
- **Variables Dominantes:** Tráfico UDP masivo, alta densidad de dispositivos vulnerables (routers genéricos y cámaras IP).
- **Modelo de Propagación:** La infección sigue un modelo de decaimiento exponencial donde la tasa de peticiones se define como $f(t) = \\lambda e^{-kt}$.
- **Contexto Geoespacial:** Alta concentración en barrios periféricos con gran densidad poblacional. Se detectaron picos que superan los \`15,000 req/s\`.

### 🟣 Clúster 1: Escaneo de Puertos en Infraestructura Hospitalaria
- **Variables Dominantes:** Intentos repetidos de conexión a puertos de administración (\`22\`, \`23\`, \`3389\`).
- **Comportamiento Matemático:** El ataque utiliza un barrido sigiloso. La varianza del tráfico se puede representar mediante la matriz de covarianza $\\Sigma$ para evadir sistemas IDS/IPS tradicionales.
- **Riesgo:** **CRÍTICO**. Posible fase de reconocimiento (reconnaissance) previa a un ataque de Ransomware.

### 🟡 Clúster 2: Interferencia en Nodos de Transporte
- **Variables Dominantes:** Pérdida de paquetes inusualmente alta y latencia extrema.
- **Métrica de Distancia:** Los eventos se agrupan utilizando una distancia de Mahalanobis para aislar el ruido de la red:
  
$$D_M(\\vec{x}) = \\sqrt{(\\vec{x} - \\vec{\\mu})^T S^{-1} (\\vec{x} - \\vec{\\mu})}$$

## Recomendaciones de Seguridad (Mitigación)

Para contener las amenazas basadas en la distribución espacial actual, se sugieren las siguientes acciones automáticas:

1. **Aislamiento Dinámico:** Aislar los segmentos de red (\`VLANs\`) correspondientes a las coordenadas del Clúster 1.
2. **Rate-Limiting Geográfico:** Implementar reglas estrictas en el WAF para limitar peticiones originadas en los bloques IP asociados al Clúster 0.
3. **Auditoría de Firmware:** Forzar el parcheo del estándar *IEEE 802.11* en los nodos de transporte afectados en el Clúster 2.
`);


  const [geoData, setGeoData] = useState([
  { "lat": 4.6097, "lon": -74.0817, "cluster": 0, "infra_type": "Hospital" },
  { "lat": 10.3910, "lon": -75.4794, "cluster": 1, "infra_type": "Transporte" },
  { "lat": 3.4516, "lon": -76.5320, "cluster": 0, "infra_type": "Residencial" }
]);


  return (
    <div style={{ padding: '2rem', color: 'var(--text-main)' }}>
        <h1 className='title1'>Dashboard Analítico</h1>
    <div className="dashboard-grid">
            
            <Geo data={geoData} /> 
            <div className="card llm-card">
            <Report markdownContent={llmText} />
        </div>
    </div>

        
    </div>
  );
};

export default Dashboard;