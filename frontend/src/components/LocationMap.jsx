import { useMemo } from "react";

function LocationMap({ latitude, longitude, label = "Localização", height = 250 }) {
    const ponto = useMemo(() => {
        const lat = Number(latitude);
        const lon = Number(longitude);
        if (latitude === "" || longitude === "" || latitude == null || longitude == null) return null;
        if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
        const margem = 0.006;
        return {
            lat,
            lon,
            src: `https://www.openstreetmap.org/export/embed.html?bbox=${lon - margem}%2C${lat - margem}%2C${lon + margem}%2C${lat + margem}&layer=mapnik&marker=${lat}%2C${lon}`,
            link: `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`,
        };
    }, [latitude, longitude]);

    if (!ponto) {
        return (
            <div className="location-map location-map-empty" role="status">
                <span className="location-map-empty-icon" aria-hidden="true">📍</span>
                <p>O mapa aparecerá assim que o endereço tiver coordenadas válidas.</p>
            </div>
        );
    }

    return (
        <section className="location-map" aria-label={`Mapa: ${label}`}>
            <iframe
                title={`Mapa da localização: ${label}`}
                src={ponto.src}
                width="100%"
                height={height}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                style={{ border: 0 }}
            />
            <div className="location-map-footer">
                <span>📍 {label}</span>
                <a href={ponto.link} target="_blank" rel="noreferrer">Abrir mapa maior</a>
            </div>
            <small className="location-map-attribution">Mapa © OpenStreetMap contributors</small>
        </section>
    );
}

export default LocationMap;
