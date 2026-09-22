import { importLibrary, setOptions } from "@googlemaps/js-api-loader";

const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

if (!apiKey) {
    console.warn("VITE_GOOGLE_MAPS_API_KEY não configurada.");
} else {
    setOptions({
        key: apiKey,
        v: "weekly",
        language: "pt-BR",
        region: "BR",
    });
}

export async function loadGoogleMaps() {
    if (!apiKey) {
        throw new Error(
            "VITE_GOOGLE_MAPS_API_KEY não configurada."
        );
    }

    await importLibrary("maps");

    return window.google.maps;
}

export async function getGoogleMapsLibrary(libraryName) {
    if (!apiKey) {
        throw new Error(
            "VITE_GOOGLE_MAPS_API_KEY não configurada."
        );
    }

    return importLibrary(libraryName);
}

export async function geocodeAddress(address) {
    const { Geocoder } = await getGoogleMapsLibrary("geocoding");

    const geocoder = new Geocoder();

    const response = await geocoder.geocode({
        address,
        region: "BR",
    });

    const result = response.results?.[0];

    if (!result) {
        throw new Error(
            "Não foi possível localizar o endereço no mapa."
        );
    }

    return {
        latitude: result.geometry.location.lat(),
        longitude: result.geometry.location.lng(),
        formattedAddress: result.formatted_address,
        components: result.address_components || [],
    };
}

export async function reverseGeocode(latitude, longitude) {
    const { Geocoder } = await getGoogleMapsLibrary("geocoding");

    const geocoder = new Geocoder();

    const response = await geocoder.geocode({
        location: {
            lat: latitude,
            lng: longitude,
        },
    });

    const result = response.results?.[0];

    if (!result) {
        throw new Error(
            "Não foi possível identificar o endereço desse ponto."
        );
    }

    return {
        latitude,
        longitude,
        formattedAddress: result.formatted_address,
        components: result.address_components || [],
    };
}

export function getAddressComponent(components, type) {
    const component = components.find((item) =>
        item.types?.includes(type)
    );

    return component?.long_name || "";
}

export function getShortAddressComponent(components, type) {
    const component = components.find((item) =>
        item.types?.includes(type)
    );

    return component?.short_name || "";
}