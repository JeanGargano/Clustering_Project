import React, { useState, useRef } from 'react';
import './styles/dragzone.css';

const FileUpload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Manejadores de eventos de arrastre
  const handleDragOver = (e) => {
    e.preventDefault(); // Necesario para permitir el "drop"
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  // Manejador del input tradicional
  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  // Validación básica para asegurar que es un CSV
  const validateAndSetFile = (file) => {
    if (file.name.endsWith('.csv') || file.type === 'text/csv') {
      setSelectedFile(file);
    } else {
      alert('Por favor, sube un archivo con extensión .csv');
    }
  };

  // Simulación de envío al backend
  const handleAnalyze = () => {
    if (!selectedFile) return;
    console.log('Enviando archivo para clustering:', selectedFile.name);
    // Aquí iría tu lógica de fetch/axios hacia el backend en Python
  };

  return (
    <section className="upload-section">
      <div 
        className={`drop-zone ${isDragging ? 'drag-active' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <input 
          type="file" 
          accept=".csv" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          className="hidden-input"
        />
        
        {/* Ícono SVG minimalista */}
        <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>

        {selectedFile ? (
          <div className="file-info">
            <p className="file-name">{selectedFile.name}</p>
            <p className="file-size">{(selectedFile.size / 1024).toFixed(2)} KB</p>
          </div>
        ) : (
          <div className="upload-text">
            <p className="text2">Arrastra tu dataset <span>.csv</span> aquí</p>
            <p className="text3">o haz clic para explorar en tus archivos</p>
          </div>
        )}
      </div>

      <button 
        className="btn-analyze" 
        disabled={!selectedFile}
        onClick={handleAnalyze}
      >
        Comenzar Análisis Multivariado
      </button>
    </section>
  );
};

export default FileUpload;