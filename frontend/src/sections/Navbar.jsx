import React from 'react';
import './styles/navbar.css';

const Navbar = () => {
  return (
    <div className="navbar">
      
      
      <a href="/" className="brand-title">
        <h1 className="brand-title">
          ClusterBoard
        </h1>
      </a>

      
      <nav>
        <ul className="navbar-links">
          <li><a href="/" className="nav-item ">Análisis</a></li>
          <li><a href="/dashboard" className="nav-item">Dashboard</a></li>
        </ul>
      </nav>


    </div>
  );
};

export default Navbar;