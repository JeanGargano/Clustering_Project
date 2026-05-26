import React from 'react';
import { useNavigate } from 'react-router-dom';
import Hero from '../sections/Hero';
import FileUpload from '../sections/Dragzone';

const Home = () => {
  const navigate = useNavigate();

  // Esta función se pasa al FileUpload que hicimos antes
  const handleAnalysisComplete = (data) => {
    // Como los datos ya se guardaron en localStorage en tu Dragzone.jsx,
    // solo necesitamos cambiar de ruta.
    navigate('/dashboard');
  };

  return (
    <main>
      <Hero />
      <FileUpload onAnalysisComplete={handleAnalysisComplete} />
    </main>
  );
};

export default Home;