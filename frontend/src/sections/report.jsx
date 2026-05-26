import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// IMPORTANTE: Esto es necesario para que las fórmulas LaTeX se vean bonitas
import 'katex/dist/katex.min.css'; 

import './styles/report.css'; // Nuestro CSS puro para los colores y el layout

const Report = ({ markdownContent }) => {
  // Estado vacío elegante si aún no hay reporte
  if (!markdownContent) {
    return (
      <div className="report-empty-state">
        <p>El análisis de Inteligencia Artificial aparecerá aquí...</p>
      </div>
    );
  }

  return (
    <div className="report-container">
      <div className="report-header">
        <h3 className='title1'>Análisis Contextual de Amenazas</h3>
        <span className="badge text3">Llama 3.3 Generado</span>
      </div>
      
      {/* Contenedor con scroll para textos largos */}
      {/* Contenedor con scroll para textos largos */}
      <div className="report-body custom-scrollbar">
        
        {/* ✅ ENVOLVEMOS EL MARKDOWN EN UN DIV CON LA CLASE */}
        <div className="markdown-content"> 
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            // (Ya no usamos className aquí adentro)
            components={{
              h1: ({node, ...props}) => <h1 className="text1" {...props} />,
              h2: ({node, ...props}) => <h2 className="text2" {...props} />,
              a: ({node, ...props}) => <a target="_blank" rel="noopener noreferrer" className="text2" {...props} />, 
              p: ({node, ...props}) => <p className="text3" {...props} />
            }}
          >
            {markdownContent}
          </ReactMarkdown>
        </div>

      </div>
    </div>
  );
};

export default Report;