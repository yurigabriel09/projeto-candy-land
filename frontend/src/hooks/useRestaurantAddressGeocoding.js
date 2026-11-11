import { useCallback, useEffect, useRef, useState } from "react";
import { geocodeRestaurantAddress } from "../services/restaurantService";

function normalizar(valor) {
    return String(valor ?? "").trim().toLocaleLowerCase("pt-BR");
}

function montarChave(endereco) {
    return [
        endereco?.cep,
        endereco?.rua,
        endereco?.numero,
        endereco?.bairro,
        endereco?.cidade,
        endereco?.estado,
    ].map(normalizar).join("|");
}

function enderecoCompleto(endereco) {
    return Boolean(
        String(endereco?.rua || "").trim()
        && String(endereco?.numero || "").trim()
        && String(endereco?.cidade || "").trim()
        && String(endereco?.estado || "").trim()
    );
}

/**
 * Geocodifica somente depois que os campos essenciais do endereço foram
 * preenchidos e ficaram estáveis por um curto intervalo. Não envia uma
 * consulta a cada tecla e descarta respostas antigas quando o endereço muda.
 */
export default function useRestaurantAddressGeocoding({
    endereco,
    mode = "configuration",
    restaurantId,
    attemptId,
    onCoordinates,
}) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [retryVersion, setRetryVersion] = useState(0);
    const attemptedKey = useRef("");
    const previousKey = useRef("");
    const requestId = useRef(0);
    const onCoordinatesRef = useRef(onCoordinates);

    useEffect(() => {
        onCoordinatesRef.current = onCoordinates;
    }, [onCoordinates]);

    const key = montarChave(endereco);
    const hasCoordinates = endereco?.latitude != null
        && endereco?.longitude != null
        && endereco?.latitude !== ""
        && endereco?.longitude !== "";

    useEffect(() => {
        if (previousKey.current !== key) {
            previousKey.current = key;
            attemptedKey.current = "";
            // Uma falha do endereço anterior não deve exibir os campos manuais
            // enquanto a nova localização ainda está sendo consultada.
            setError("");
        }

        if (!enderecoCompleto(endereco) || hasCoordinates) {
            setLoading(false);
            return undefined;
        }
        if (attemptedKey.current === key) return undefined;

        const currentRequest = ++requestId.current;
        const controller = new AbortController();
        setLoading(true);
        setError("");
        const timer = window.setTimeout(async () => {
            attemptedKey.current = key;
            try {
                const resultado = await geocodeRestaurantAddress(endereco, {
                    mode,
                    restaurantId,
                    attemptId,
                    signal: controller.signal,
                });
                if (controller.signal.aborted || currentRequest !== requestId.current) return;
                if (resultado?.latitude == null || resultado?.longitude == null) {
                    throw new Error("O serviço de mapas não retornou coordenadas válidas.");
                }
                setError("");
                onCoordinatesRef.current?.({
                    latitude: Number(resultado.latitude),
                    longitude: Number(resultado.longitude),
                });
            } catch (geocodeError) {
                if (!controller.signal.aborted && currentRequest === requestId.current) {
                    setError(geocodeError.message || "Não foi possível localizar o endereço automaticamente.");
                }
            } finally {
                if (!controller.signal.aborted && currentRequest === requestId.current) {
                    setLoading(false);
                }
            }
        }, 900);

        return () => {
            window.clearTimeout(timer);
            controller.abort();
            if (currentRequest === requestId.current) requestId.current += 1;
        };
    }, [key, hasCoordinates, mode, restaurantId, attemptId, retryVersion]);

    const retry = useCallback(() => {
        attemptedKey.current = "";
        setError("");
        setRetryVersion((current) => current + 1);
    }, []);

    return {
        geocoding: loading,
        geocodingError: error,
        showManualCoordinates: Boolean(error),
        retryGeocoding: retry,
    };
}
