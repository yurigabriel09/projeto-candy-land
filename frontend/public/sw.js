self.addEventListener("push", (event) => {
    let data = { title: "Candyland", body: "Atualização no seu pedido!" };
    
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: "/logo192.png", // Altere para o ícone da sua aplicação
        badge: "/logo192.png",
        data: {
            url: data.url || "/minha-conta/historico-compras"
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});