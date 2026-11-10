const VAPID_PUBLIC_KEY = "SUA_CHAVE_PUBLICA_VAPID_AQUI";

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

export async function registrarPushNotifications(userId, token) {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        console.warn("Este navegador não suporta notificações Push.");
        return;
    }

    try {
        const permissao = await Notification.requestPermission();
        if (permissao !== "granted") {
            console.log("Permissão de notificação negada pelo usuário.");
            return;
        }

        const registro = await navigator.serviceWorker.register("/sw.js");
        await navigator.serviceWorker.ready;

        let subscricao = await registro.pushManager.getSubscription();
        if (!subscricao) {
            const convertedKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
            subscricao = await registro.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedKey
            });
        }

        const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
        await fetch(`${apiBase}/users/${userId}/push-subscription`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(subscricao)
        });

        console.log("Notificações Push registradas com sucesso!");
    } catch (erro) {
        console.error("Erro ao registrar notificações Push:", erro);
    }
}