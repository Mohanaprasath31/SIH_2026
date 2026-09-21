import React, { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Force Leaflet to recalculate its size
function MapResizeHandler({ positions }) {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();

      if (positions.length === 1) {
        map.setView(positions[0], 15);
      } else if (positions.length > 1) {
        const bounds = L.latLngBounds(positions);

        map.fitBounds(bounds, {
          padding: [50, 50],
        });
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [map, positions]);

  return null;
}

export function TrajectoryMap({ points = [] }) {
  const validPoints = points.filter((point) => {
    const coordinates = point?.location?.coordinates;

    return (
      Array.isArray(coordinates) &&
      coordinates.length >= 2 &&
      Number.isFinite(Number(coordinates[0])) &&
      Number.isFinite(Number(coordinates[1]))
    );
  });

  if (validPoints.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "500px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0f172a",
          color: "#94a3b8",
          borderRadius: "12px",
        }}
      >
        No trajectory points available
      </div>
    );
  }

  // GeoJSON: [longitude, latitude]
  // Leaflet: [latitude, longitude]
  const positions = validPoints.map((point) => [
    Number(point.location.coordinates[1]),
    Number(point.location.coordinates[0]),
  ]);

  return (
    <div
      style={{
        width: "100%",
        height: "500px",
        minHeight: "500px",
        position: "relative",
        overflow: "hidden",
        borderRadius: "12px",
      }}
    >
      <MapContainer
        center={positions[0]}
        zoom={13}
        scrollWheelZoom={true}
        style={{
          width: "100%",
          height: "500px",
          minHeight: "500px",
          background: "#e5e7eb",
        }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapResizeHandler positions={positions} />

        {/* Route */}
        {positions.length > 1 && (
          <Polyline
            positions={positions}
            pathOptions={{
              color: "#0284c7",
              weight: 6,
              opacity: 0.9,
            }}
          />
        )}

        {/* Camera markers */}
        {validPoints.map((point, index) => (
          <Marker
            key={`${point.camera_id}-${point.timestamp}-${index}`}
            position={positions[index]}
          >
            <Popup>
              <div style={{ minWidth: "200px" }}>
                <h3
                  style={{
                    margin: "0 0 10px 0",
                    fontWeight: "bold",
                  }}
                >
                  Camera {index + 1}
                </h3>

                <div>
                  <strong>Camera ID:</strong>
                  <br />
                  {point.camera_id || "N/A"}
                </div>

                <br />

                <div>
                  <strong>Timestamp:</strong>
                  <br />
                  {point.timestamp
                    ? new Date(point.timestamp).toLocaleString()
                    : "N/A"}
                </div>

                <br />

                <div>
                  <strong>OCR Confidence:</strong>
                  <br />
                  {point.confidence != null
                    ? `${Math.round(point.confidence * 100)}%`
                    : "N/A"}
                </div>

                <br />

                <div>
                  <strong>Location:</strong>
                  <br />
                  Latitude: {positions[index][0].toFixed(5)}
                  <br />
                  Longitude: {positions[index][1].toFixed(5)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}