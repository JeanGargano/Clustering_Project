import React from 'react'
import globe from '../assets/globe.png'
import './styles/hero.css'

const Hero = () => {
  return (
    <div className="hero">
        <div className='description'>
            <h1 className='title1'>Análisis Geoespacial de Ciberataques IoT</h1>
            <p className='text1'>Descubre la relación entre el entorno físico y las vulnerabilidades de red. Carga tu dataset (.csv) 
                                    para identificar patrones de amenazas mediante clustering multivariado y obtén un análisis 
                                    automatizado en lenguaje natural.</p>
        </div>
        <div className='image-container'>
            <img src={globe} alt="Globe" className='hero-image' />
        </div>
    </div>
  );
};

export default Hero;