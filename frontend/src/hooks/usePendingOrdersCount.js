import { useCallback, useEffect, useState } from "react";
import { getOrders } from "../services/orderService";

/** Conta somente pedidos que ainda aguardam confirmação do pagamento. */
export default function usePendingOrdersCount(ativo = true) {
    const [quantidade, setQuantidade] = useState(0);

    const atualizar = useCallback(async () => {
        if (!ativo) {
            setQuantidade(0);
            return;
        }
        try {
            const pedidos = await getOrders();
            setQuantidade((pedidos || []).filter((pedido) => pedido.status === "PENDENTE_PAGAMENTO").length);
        } catch {
            // A falha temporária de rede não deve quebrar a navegação;
            // uma próxima entrada/foco da página tentará atualizar a contagem.
        }
    }, [ativo]);

    useEffect(() => {
        atualizar();
        if (!ativo) return undefined;
        const aoAtualizarPedidos = () => atualizar();
        window.addEventListener("focus", aoAtualizarPedidos);
        window.addEventListener("pageshow", aoAtualizarPedidos);
        window.addEventListener("candyland:pending-orders-updated", aoAtualizarPedidos);
        return () => {
            window.removeEventListener("focus", aoAtualizarPedidos);
            window.removeEventListener("pageshow", aoAtualizarPedidos);
            window.removeEventListener("candyland:pending-orders-updated", aoAtualizarPedidos);
        };
    }, [ativo, atualizar]);

    return quantidade;
}
