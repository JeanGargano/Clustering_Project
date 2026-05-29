import React, { useState, useEffect } from 'react';
import Geo from '../sections/geo'; 
import Report from '../sections/report';
import Papa from 'papaparse';
import './styles/dashboard.css';

const Dashboard = () => {
  const [llmText, setLlmText] = useState('');
  const [geoData, setGeoData] = useState([]);
  const [isWaiting, setIsWaiting] = useState(true);

  useEffect(() => {
    // Función asíncrona para orquestar la obtención de datos
    const fetchDashboardData = async () => {
      try {
        // 1. Recuperamos el JSON que guardó el componente de carga (Dragzone)
        const savedData = localStorage.getItem('clustering_result');
        if (!savedData) {
          console.error("No se encontraron resultados previos en localStorage.");
          setIsWaiting(false);
          return;
        }

        const parsedData = JSON.parse(savedData);
        const currentJobId = parsedData.job_id;

        // Extraemos el texto del LLM buscando el run que tenga el análisis finalizado
        if (parsedData.runs) {
          const runWithAnalysis = Object.values(parsedData.runs).find(run => run.analysis_status === 'done');
          
          if (runWithAnalysis && runWithAnalysis.analysis) {
             setLlmText(runWithAnalysis.analysis);
          } else {
             setLlmText("No se encontró reporte de IA.");
          }
        }

        // 2. Hacemos el GET al endpoint de resultados usando el currentJobId
        const response = await fetch(`/api/jobs/${currentJobId}/results`);
        
        if (!response.ok) {
          throw new Error(`Error HTTP consultando resultados: ${response.status}`);
        }
        
        const resultsData = await response.json();

        // 3. Validamos que el backend nos entregó la URL firmada de MinIO
        if (resultsData.download_url) {
          
          // Redirigimos la petición interna hacia nuestro Reverse Proxy (Vite / Nginx)
          let csvUrl = resultsData.download_url;
          csvUrl = csvUrl.replace('http://minio:9000', '/minio-api');

          // 4. Descargamos y mapeamos el CSV final con PapaParse
          Papa.parse(csvUrl, {
            download: true,
            header: true,
            dynamicTyping: true, // Automáticamente convierte los textos "47.38" a números 47.38
            skipEmptyLines: true,
            complete: (results) => {
              console.log("Dataset descargado a través del Proxy:", results.data);
              
              // =======================================================
              // EXTRACCIÓN DE DATOS REALES PARA EL MAPA
              // =======================================================
              const realMappedData = results.data.map((point) => ({
                ...point,
                lat: point.Latitude,                       // Extrae la latitud real del CSV
                lon: point.Longitude,                      // Extrae la longitud real del CSV
                cluster: point.cluster,                    // Conserva el clúster calculado
                infra_type: point['Infrastructure Type'],  // Mapea la infraestructura para el tooltip del mapa
                attack_type: point['Cyber Attack Type']    // Opcional: Útil si quieres expandir tu mapa luego
              }));

              setGeoData(realMappedData);
              setIsWaiting(false); // Todo está listo, mostramos la interfaz
            },
            error: (err) => {
              console.error("Fallo al descargar el archivo CSV:", err);
              setIsWaiting(false);
            }
          });
        } else {
          console.error("El JSON recibido no contiene la propiedad 'download_url'.");
          setIsWaiting(false);
        }

      } catch (error) {
        console.error("Excepción en el flujo de carga del Dashboard:", error);
        setIsWaiting(false); // Apagamos el loader para no dejar al usuario atascado
      }
    };

    // Ejecutamos la orquestación una sola vez al cargar la vista
    fetchDashboardData();
  }, []);

  return (
    <div style={{ padding: '2rem', color: 'var(--text-main)' }}>
      <h1 className='title1'>Dashboard Analítico</h1>
      
      {isWaiting ? (
        <div style={{ textAlign: 'center', marginTop: '10vh' }}>
          <h2 className="title2" style={{ color: 'var(--accent-color)' }}>
            Obteniendo coordenadas y métricas...
          </h2>
          <p className="text3">
            Conectando con el Gateway para descargar el dataset resultante.
          </p>
        </div>
      ) : (
        <div className="dashboard-grid">
          <div className="card map-card">
            {/* El mapa ahora grafica las posiciones geoespaciales precisas */}
            <Geo data={geoData} /> 
          </div>
          <div className="card llm-card">
            {/* El reporte de IA se formatea con Markdown y LaTeX */}
            <Report markdownContent={llmText} />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;