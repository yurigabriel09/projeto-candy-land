import { useState } from "react";

function AddressCoordinates({ latitude, longitude, onChange, title = "Coordenadas do endereço" }) {
    const [locationError, setLocationError] = useState("");
    const [locating, setLocating] = useState(false);

    function updateCoordinate(field, rawValue) {
        const parsed = rawValue === "" ? null : Number(rawValue);
        onChange({
            latitude: field === "latitude" ? parsed : latitude,
            longitude: field === "longitude" ? parsed : longitude,
        });
    }

    function useCurrentLocation() {
        setLocationError("");
        if (!navigator.geolocation) {
            setLocationError("Este navegador não oferece geolocalização.");
            return;
        }
        setLocating(true);
        navigator.geolocation.getCurrentPosition(
            (position) => {
                onChange({
                    latitude: Number(position.coords.latitude.toFixed(6)),
                    longitude: Number(position.coords.longitude.toFixed(6)),
                });
                setLocating(false);
            },
            (error) => {
                const messages = {
                    1: "Permita o acesso à localização ou informe as coordenadas manualmente.",
                    2: "A localização não está disponível. Tente informar as coordenadas manualmente.",
                    3: "A consulta da localização expirou. Tente novamente.",
                };
                setLocationError(messages[error.code] || "Não foi possível obter a localização.");
                setLocating(false);
            },
            { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 },
        );
    }

    return (
        <section className="address-coordinates" aria-label={title}>
            <h4>{title}</h4>
            <p>Informe as coordenadas do endereço cadastrado. Use a localização atual somente se estiver no local correto; também é possível preencher manualmente.</p>
            <div className="form-grid-two">
                <div className="form-field">
                    <label htmlFor={`${title.replace(/\W+/g, "-").toLowerCase()}-latitude`}>Latitude</label>
                    <input
                        id={`${title.replace(/\W+/g, "-").toLowerCase()}-latitude`}
                        type="number"
                        min="-90"
                        max="90"
                        step="any"
                        value={latitude ?? ""}
                        onChange={(event) => updateCoordinate("latitude", event.target.value)}
                        placeholder="Ex.: -23.550520"
                    />
                </div>
                <div className="form-field">
                    <label htmlFor={`${title.replace(/\W+/g, "-").toLowerCase()}-longitude`}>Longitude</label>
                    <input
                        id={`${title.replace(/\W+/g, "-").toLowerCase()}-longitude`}
                        type="number"
                        min="-180"
                        max="180"
                        step="any"
                        value={longitude ?? ""}
                        onChange={(event) => updateCoordinate("longitude", event.target.value)}
                        placeholder="Ex.: -46.633308"
                    />
                </div>
            </div>
            <button type="button" className="secondary-button" onClick={useCurrentLocation} disabled={locating}>
                {locating ? "Obtendo localização..." : "Usar localização atual"}
            </button>
            {locationError && <p className="field-error" role="alert">{locationError}</p>}
        </section>
    );
}

export default AddressCoordinates;
