import { useEffect, useRef, useState } from "react";
import {
    geocodeAddress,
    getAddressComponent,
    getShortAddressComponent,
    getGoogleMapsLibrary,
    reverseGeocode,
} from "../services/googleMapsService";

const DEFAULT_CENTER = { lat: -23.55052, lng: -46.633308 };

function AddressMap({ address, latitude, longitude, onLocationChange, autoLocateKey }) {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markerRef = useRef(null);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [canLocate, setCanLocate] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function initializeMap() {
            try {
                const [{ Map }, { Marker }] = await Promise.all([
                    getGoogleMapsLibrary("maps"),
                    getGoogleMapsLibrary("marker"),
                ]);
                if (!mounted || !mapRef.current) return;

                const center = latitude != null && longitude != null
                    ? { lat: Number(latitude), lng: Number(longitude) }
                    : DEFAULT_CENTER;

                mapInstanceRef.current = new Map(mapRef.current, {
                    center,
                    zoom: latitude != null && longitude != null ? 17 : 12,
                    mapTypeControl: false,
                    streetViewControl: false,
                    fullscreenControl: true,
                });

                markerRef.current = new Marker({
                    map: mapInstanceRef.current,
                    position: center,
                    draggable: true,
                });

                mapInstanceRef.current.addListener("click", (event) => {
                    if (!event.latLng) return;
                    handleMapPosition(event.latLng.lat(), event.latLng.lng());
                });

                markerRef.current.addListener("dragend", (event) => {
                    if (!event.latLng) return;
                    handleMapPosition(event.latLng.lat(), event.latLng.lng());
                });

                setLoading(false);
            } catch (error) {
                if (mounted) {
                    setLoading(false);
                    setMessage(error.message || "Não foi possível carregar o mapa.");
                }
            }
        }

        initializeMap();

        return () => {
            mounted = false;
            markerRef.current?.setMap(null);
            mapInstanceRef.current = null;
            markerRef.current = null;
        };
    }, []);


    useEffect(() => {
        if (!autoLocateKey || !address?.trim()) return;

        localizarEndereco();
        // A localização automática acontece somente quando o chamador altera a chave.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [autoLocateKey]);

    useEffect(() => {
        if (!mapInstanceRef.current || !markerRef.current) return;
        if (latitude == null || longitude == null) return;

        const position = { lat: Number(latitude), lng: Number(longitude) };
        mapInstanceRef.current.setCenter(position);
        mapInstanceRef.current.setZoom(17);
        markerRef.current.setPosition(position);
    }, [latitude, longitude]);

    async function handleMapPosition(lat, lng) {
        setMessage("Identificando endereço...");

        markerRef.current?.setPosition({ lat, lng });
        mapInstanceRef.current?.panTo({ lat, lng });

        try {
            const result = await reverseGeocode(lat, lng);
            onLocationChange({
                latitude: lat,
                longitude: lng,
                address: getAddressComponent(result.components, "route"),
                number: getAddressComponent(result.components, "street_number"),
                cep: getAddressComponent(result.components, "postal_code"),
                neighborhood:
                    getAddressComponent(result.components, "sublocality_level_1") ||
                    getAddressComponent(result.components, "sublocality") ||
                    getAddressComponent(result.components, "neighborhood"),
                city:
                    getAddressComponent(result.components, "administrative_area_level_2") ||
                    getAddressComponent(result.components, "locality"),
                state: getShortAddressComponent(result.components, "administrative_area_level_1"),
            });
            setMessage("Endereço ajustado pelo ponto selecionado.");
        } catch (error) {
            setMessage(error.message || "Não foi possível identificar esse ponto.");
        }
    }

    async function localizarEndereco() {
        if (!address?.trim()) {
            setMessage("Preencha o endereço antes de localizar no mapa.");
            return;
        }

        setCanLocate(false);
        setMessage("Localizando endereço...");

        try {
            const result = await geocodeAddress(address);
            const position = { lat: result.latitude, lng: result.longitude };
            mapInstanceRef.current?.setCenter(position);
            mapInstanceRef.current?.setZoom(17);
            markerRef.current?.setPosition(position);

            onLocationChange({
                latitude: result.latitude,
                longitude: result.longitude,
            });
            setMessage("Endereço localizado. Você pode clicar no mapa ou arrastar o marcador.");
        } catch (error) {
            setMessage(error.message || "Não foi possível localizar o endereço.");
        } finally {
            setCanLocate(true);
        }
    }

    useEffect(() => {
        if (address?.trim()) setCanLocate(true);
    }, [address]);

    return (
        <div className="address-map-section">
            <div className="address-map-header">
                <div>
                    <strong>Confira a localização</strong>
                    <p>Clique no mapa ou arraste o marcador para ajustar o endereço.</p>
                </div>
                <button type="button" className="secondary-button" onClick={localizarEndereco} disabled={!canLocate || loading}>
                    Localizar endereço
                </button>
            </div>

            <div ref={mapRef} className="address-map" aria-label="Mapa para ajustar o endereço" />

            {loading && <small className="field-message">Carregando mapa...</small>}
            {message && <small className="field-message">{message}</small>}
        </div>
    );
}

export default AddressMap;
