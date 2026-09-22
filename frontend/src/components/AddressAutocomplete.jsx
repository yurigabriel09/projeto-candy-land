import { useEffect, useRef, useState } from "react";
import { getGoogleMapsLibrary } from "../services/googleMapsService";

function AddressAutocomplete({ value, onChange, onSelect, placeholder = "Digite seu endereço" }) {
    const containerRef = useRef(null);
    const elementRef = useRef(null);
    const onSelectRef = useRef(onSelect);
    const onChangeRef = useRef(onChange);
    const [error, setError] = useState("");

    useEffect(() => {
        onSelectRef.current = onSelect;
        onChangeRef.current = onChange;
    }, [onSelect, onChange]);

    useEffect(() => {
        let mounted = true;
        let placeAutocomplete = null;

        async function setupAutocomplete() {
            try {
                const { PlaceAutocompleteElement } = await getGoogleMapsLibrary("places");
                if (!mounted || !containerRef.current) return;

                placeAutocomplete = new PlaceAutocompleteElement();

                placeAutocomplete.placeholder = placeholder;
                placeAutocomplete.includedRegionCodes = ["br"];

                placeAutocomplete.style.width = "100%";
                placeAutocomplete.style.colorScheme = "light";
                placeAutocomplete.style.backgroundColor = "#ffffff";
                placeAutocomplete.style.borderRadius = "12px";

                placeAutocomplete.addEventListener("input", (event) => {
                    onChangeRef.current?.({ target: { value: event.target.value } });
                });

                placeAutocomplete.addEventListener("gmp-select", async ({ placePrediction }) => {
                    try {
                        setError("");

                        const place = placePrediction.toPlace();
                        await place.fetchFields({
                            fields: ["displayName", "formattedAddress", "location", "id", "addressComponents"],
                        });

                        if (!place.location) {
                            setError("Selecione um endereço válido da lista.");
                            return;
                        }

                        onSelectRef.current?.({
                            address: place.formattedAddress || place.displayName || "",
                            latitude: place.location.lat(),
                            longitude: place.location.lng(),
                            placeId: place.id || null,
                            components: place.addressComponents || [],
                        });
                    } catch (selectionError) {
                        setError(selectionError.message || "Não foi possível selecionar esse endereço.");
                    }
                });

                containerRef.current.replaceChildren(placeAutocomplete);
                elementRef.current = placeAutocomplete;
                placeAutocomplete.value = value || "";
            } catch (loadError) {
                if (mounted) {
                    setError(loadError.message || "Não foi possível carregar a busca de endereços.");
                }
            }
        }

        setupAutocomplete();

        return () => {
            mounted = false;
            placeAutocomplete?.remove?.();
            elementRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (!elementRef.current) return;
        if (document.activeElement === elementRef.current) return;
        elementRef.current.value = value || "";
    }, [value]);

    return (
        <div className="address-autocomplete" ref={containerRef}>
            {error && <small className="field-error">{error}</small>}
        </div>
    );
}

export default AddressAutocomplete;