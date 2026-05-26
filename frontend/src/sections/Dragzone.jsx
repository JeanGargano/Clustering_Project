import React, { useState, useRef, useEffect } from 'react';
import './styles/dragzone.css';

// Añadimos onAnalysisComplete como prop para pasar el resultado final al componente padre (ej. App o Dashboard)
const FileUpload = ({ onAnalysisComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Estados para gestionar el ciclo asíncrono
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  
  // Estado para almacenar el ID del trabajo actual
  const [jobId, setJobId] = useState(null);

  // Efecto para recuperar un proceso si el usuario recarga la página
  useEffect(() => {
    const savedJobId = sessionStorage.getItem('active_clustering_job');
    if (savedJobId) {
      setJobId(savedJobId);
      setIsProcessing(true);
      setStatusText('Recuperando análisis en curso...');
      pollJobStatus(savedJobId);
    }
  }, []); // Se ejecuta solo una vez al montar el componente

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) validateAndSetFile(files[0]);
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) validateAndSetFile(files[0]);
  };

  const validateAndSetFile = (file) => {
    if (file.name.endsWith('.csv') || file.type === 'text/csv') {
      setSelectedFile(file);
      setErrorMsg(null); // Limpiar errores previos si seleccionan un buen archivo
    } else {
      alert('Por favor, sube un archivo con extensión .csv');
    }
  };

  // 1. FASE DE INGESTA
  const handleAnalyze = async () => {
    if (!selectedFile) return;
    
    setIsProcessing(true);
    setErrorMsg(null);
    setStatusText('Subiendo dataset al Gateway...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8001/api/ingest', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

      const data = await response.json();
      console.log('Ingesta exitosa. Job ID:', data.job_id);
      
      // Guardar el ID en el estado y en la sesión
      setJobId(data.job_id);
      sessionStorage.setItem('active_clustering_job', data.job_id);
      
      setStatusText('Dataset en cola. Iniciando pipeline de limpieza...');
      
      // Iniciar la fase 2
      pollJobStatus(data.job_id);

    } catch (err) {
      console.error("Debug [Ingesta]:", err);
      setErrorMsg('Error de conexión al enviar el archivo.');
      setIsProcessing(false);
    }
  };

  // 2. FASE DE MONITOREO
  const pollJobStatus = async (currentJobId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/jobs/${currentJobId}/status`);
      if (!response.ok) throw new Error('Fallo al consultar el estado del trabajo.');
      
      const data = await response.json();

      if (data.status === 'failed') {
        throw new Error('Error interno: El proceso de clustering falló en el servidor.');
      }

      if (data.status === 'done') {
        setStatusText('Clustering multivariado finalizado. Consultando a la IA...');
        // Iniciar fase 3
        fetchAnalysis(currentJobId);
      } else {
        // Continúa en 'queued' o 'running'
        if (data.status === 'running') {
            setStatusText('Ejecutando algoritmo de clustering espacial...');
        }
        // Esperar 3 segundos antes del próximo ciclo para no saturar el servidor
        setTimeout(() => pollJobStatus(currentJobId), 3000);
      }
    } catch (err) {
      console.error("Debug [Polling]:", err);
      setErrorMsg(err.message);
      setIsProcessing(false);
      
      // Limpiar sesión en caso de error para no quedar atrapados en un loop al recargar
      sessionStorage.removeItem('active_clustering_job');
      setJobId(null);
    }
  };

  // 3. FASE DE EXTRACCIÓN LLM
  const fetchAnalysis = async (currentJobId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/jobs/${currentJobId}/analysis`);
      
      if (response.status === 202) {
         console.log("Debug [Análisis]: LLM trabajando, reintentando en 3s...");
         setStatusText('Analizando patrones y redactando el reporte semántico (esto tomará unos segundos)...');
         setTimeout(() => fetchAnalysis(currentJobId), 3000);
         return;
      }
      
      if (!response.ok) throw new Error('Error al descargar los resultados del modelo.');

      const data = await response.json();
      
      // ==========================================
      // NUEVO: GUARDADO EN ALMACENAMIENTO PERSISTENTE
      // ==========================================
      localStorage.setItem('clustering_result', JSON.stringify(data));
      
      setStatusText('¡Análisis completado exitosamente!');
      setIsProcessing(false);
      
      console.log("Debug [Exito]: Reporte final obtenido y guardado en localStorage.");
      
      // Limpieza tras éxito
      sessionStorage.removeItem('active_clustering_job');
      setJobId(null);
      
      // Ejecutar la función callback si fue proveída para cambiar de vista o mostrar datos
      if (onAnalysisComplete) {
         onAnalysisComplete(data);
      }

    } catch (err) {
      console.error("Debug [Extracción]:", err);
      setErrorMsg(err.message);
      setIsProcessing(false);
      
      // Limpiar sesión en caso de error
      sessionStorage.removeItem('active_clustering_job');
      setJobId(null);
    }
  };

  return (
    <section className="upload-section">
      <div 
        className={`drop-zone ${isDragging ? 'drag-active' : ''} ${isProcessing ? 'processing' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        // Deshabilitar clic si está procesando
        onClick={() => !isProcessing && fileInputRef.current.click()}
      >
        <input 
          type="file" 
          accept=".csv" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          className="hidden-input"
          disabled={isProcessing}
        />
        
        {selectedFile ? (
          <div className="file-info">
            <p className="text2">{selectedFile.name}</p>
            <p className="text3">{(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>
        ) : (
          <div className="upload-text">
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p className="text2">Arrastra tu dataset <span>.csv</span> aquí</p>
            <p className="text3">o haz clic para explorar en tus archivos</p>
          </div>
        )}
      </div>

      {/* Mensajes de feedback visual de la consola a la interfaz */}
      <div className="feedback-container">
        {isProcessing && (
          <div className="status-wrapper">
            <p className="text2">{statusText}</p>
            {/* Mostramos el ID del proceso de forma sutil */}
            {jobId && <p className="text3" style={{ marginTop: '0.25rem', opacity: 0.7 }}>ID de proceso: {jobId.substring(0, 8)}</p>}
          </div>
        )}
        {errorMsg && <p className="text2">⚠️ {errorMsg}</p>}
      </div>

      <button 
        className="btn-analyze" 
        disabled={!selectedFile || isProcessing}
        onClick={handleAnalyze}
      >
        {isProcessing ? 'Procesando Datos...' : 'Comenzar Análisis Multivariado'}
      </button>
    </section>
  );
};

export default FileUpload;