import React, { useState, useRef, useEffect } from 'react';
import './styles/dragzone.css';

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
  }, []);

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
      setErrorMsg(null); 
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
      const response = await fetch('http://localhost:8001/api/clustering', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

      const data = await response.json();
      console.log('Ingesta exitosa. Job ID:', data.job_id);
      
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

  // 2. FASE DE MONITOREO UNIFICADA
// 2. FASE DE MONITOREO UNIFICADA
  const pollJobStatus = async (currentJobId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/jobs/${currentJobId}/status`);
      if (!response.ok) throw new Error('Fallo al consultar el estado del trabajo.');
      
      const data = await response.json();

      // 1. Buscamos si ALGÚN algoritmo falló
      const hasFailedRun = data.runs && Object.values(data.runs).some(run => run.status === 'failed');
      if (hasFailedRun) {
        throw new Error('Error interno: Un algoritmo de clustering falló en el servidor.');
      }

      // 2. Buscamos dinámicamente cuál algoritmo tiene el análisis LLM terminado
      const completedAnalysisRun = data.runs 
        ? Object.values(data.runs).find(run => run.analysis_status === 'done') 
        : null;

      // 3. Verificamos si encontramos el análisis
      if (completedAnalysisRun) {
        setStatusText('¡Análisis completado exitosamente!');
        setIsProcessing(false);
        
        // Guardamos todo el JSON en localStorage
        localStorage.setItem('clustering_result', JSON.stringify(data));
        console.log("Debug [Exito]: Reporte guardado en memoria.");
        
        sessionStorage.removeItem('active_clustering_job');
        setJobId(null);
        
        if (onAnalysisComplete) {
           onAnalysisComplete(data);
        }
      } else {
        // --- FEEDBACK VISUAL DETALLADO MIENTRAS ESPERA ---
        // Verificamos si al menos un algoritmo de clustering ya terminó de agrupar
        const isClusteringDone = data.runs && Object.values(data.runs).some(run => run.status === 'done');

        if (!data.runs && data.status_cleaning !== 'done') {
            setStatusText('Limpiando y preparando el dataset...');
        } else if (!isClusteringDone) {
            setStatusText('Ejecutando algoritmo de clustering multivariado...');
        } else {
            setStatusText('Generando reporte semántico con IA (esto tomará unos segundos)...');
        }

        // Consultar de nuevo en 1 segundo
        setTimeout(() => pollJobStatus(currentJobId), 1000);
      }
    } catch (err) {
      console.error("Debug [Polling]:", err);
      setErrorMsg(err.message);
      setIsProcessing(false);
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

      <div className="feedback-container">
        {isProcessing && (
          <div className="status-wrapper">
            <p className="text2">{statusText}</p>
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