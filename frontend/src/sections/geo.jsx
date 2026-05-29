import React, { useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
// Es obligatorio importar el CSS de Leaflet para que el mapa no se rompa
import 'leaflet/dist/leaflet.css';
import './styles/geo.css';

// Diccionario de colores para los clusters. 
// Estos colores deben hacer "match" con los que mencione el LLM en su reporte.
const CLUSTER_COLORS = {
  0: '#06b6d4', // Cian
  1: '#a855f7', // Púrpura
  2: '#f59e0b', // Ámbar
  3: '#ef4444', // Rojo
  4: '#10b981', // Esmeralda
  // Un color de fallback por si el modelo genera un cluster inesperado
  default: '#94a3b8' 
};

const Geo = ({ data }) => {
  // Validación de depuración: Si no hay datos, mostramos un estado vacío elegante
  if (!data || data.length === 0) {
    return (
      <div className="geo-empty-state">
        <p>Esperando datos geoespaciales para renderizar...</p>
      </div>
    );
  }

  // Calculamos el centro del mapa dinámicamente basado en el primer punto válido
  // para no empezar siempre en el océano.
  const mapCenter = useMemo(() => {
    const firstValidPoint = data.find(p => p.lat != null && p.lon != null);
    return firstValidPoint ? [firstValidPoint.lat, firstValidPoint.lon] : [20, 0];
  }, [data]);

  return (
    <div className="geo-container">
      <MapContainer 
        center={mapCenter} 
        zoom={3} 
        minZoom={2}
        className="leaflet-map"
        worldCopyJump={true} // Permite scroll infinito horizontal
      >
        {/* TileLayer de CartoDB Dark Matter para el modo oscuro */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {/* Mapeo de los puntos del dataset */}
        {data.map((point, index) => {
          // Filtro de seguridad: ignorar coordenadas corruptas
          if (point.lat == null || point.lon == null) {
            console.debug(`[Geo Debug] Punto descartado por coordenadas inválidas en índice ${index}`);
            return null;
          }

          const clusterColor = CLUSTER_COLORS[point.cluster] || CLUSTER_COLORS.default;

          return (
            <CircleMarker
              key={`cluster-point-${index}`}
              center={[point.lat, point.lon]}
              radius={6} // Tamaño del punto
              pathOptions={{
                color: clusterColor,
                fillColor: clusterColor,
                fillOpacity: 0.7,
                weight: 1 // Borde sutil
              }}
            >
              {/* Tooltip nativo de Leaflet que aparece al pasar el mouse */}
              <Tooltip className="custom-tooltip">
                <div className="tooltip-content">
                  <strong>Cluster {point.cluster}</strong>
                  <br />
                  <span>Lat: {point.lat.toFixed(4)}</span>
                  <br />
                  <span>Lon: {point.lon.toFixed(4)}</span>
                  {point.attack_type && (
                    <>
                      <br />
                      <span>Ataque: {point.attack_type}</span>
                    </>
                  )}
                  {point.infra_type && (
                    <>
                      <br />
                      <span>Infra: {point.infra_type}</span>
                    </>
                  )}
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default Geo;