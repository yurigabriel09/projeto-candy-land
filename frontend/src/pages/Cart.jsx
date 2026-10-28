import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import LocationMap from "../components/LocationMap";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { cancelOrder, createOrder, createPayment, getCustomerAddresses, getPayment, getOrder } from "../services/orderService";
import { geocodeCustomerAddress, saveAddressCoordinates } from "../services/userService";
import AddressCoordinates from "../components/AddressCoordinates";
import { getRestaurantPickupAddresses } from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function formatarEndereco(endereco) {
    const linha = [endereco.rua, endereco.numero].filter(Boolean).join(", ");
    const local = [endereco.bairro, endereco.cidade, endereco.estado].filter(Boolean).join(" — ");
    return [linha, local, endereco.cep].filter(Boolean).join(" | ");
}

const CHECKOUT_SESSION_KEY = "candyland_checkout_pending";
const CHECKOUT_REDIRECTED_KEY = "candyland_checkout_redirected_order_id";

function carregarCheckoutPendente(userId) {
    try {
        const raw = sessionStorage.getItem(CHECKOUT_SESSION_KEY);
        if (!raw) return null;
        const salvo = JSON.parse(raw);
        if (!salvo?.pedido?.id || String(salvo.userId) !== String(userId)) return null;
        // If the browser returned from Checkout Pro directly to /cart (rather
        // than the result URL), show the server-backed pending-order card.
        const redirecionado = sessionStorage.getItem(CHECKOUT_REDIRECTED_KEY);
        if (redirecionado && String(redirecionado) === String(salvo.pedido.id)) {
            sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
            sessionStorage.removeItem(CHECKOUT_REDIRECTED_KEY);
            return null;
        }
        return salvo;
    } catch {
        sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
        return null;
    }
}

function Cart() {
    const { dadosAutenticacao } = useAuth();
    const [checkoutInicial] = useState(() => carregarCheckoutPendente(dadosAutenticacao?.id));
    const {
        carrinho,
        atualizarQuantidade,
        removerItem,
        atualizarTipoPedido,
        limparCarrinho,
        total,
    } = useCart();

    const [enderecos, setEnderecos] = useState([]);
    const [enderecoId, setEnderecoId] = useState("");
    const [enderecosRetirada, setEnderecosRetirada] = useState([]);
    const [enderecoRetiradaId, setEnderecoRetiradaId] = useState("");
    const [carregandoEnderecos, setCarregandoEnderecos] = useState(false);
    const [carregandoEnderecosRetirada, setCarregandoEnderecosRetirada] = useState(false);
    const [erroEnderecosRetirada, setErroEnderecosRetirada] = useState("");
    const [erroEnderecos, setErroEnderecos] = useState("");
    const [geocodificando, setGeocodificando] = useState(false);
    const [erroGeocodificacao, setErroGeocodificacao] = useState("");
    const [manualLatitude, setManualLatitude] = useState("");
    const [manualLongitude, setManualLongitude] = useState("");
    const [salvandoCoordenadas, setSalvandoCoordenadas] = useState(false);
    const [mensagemCoordenadas, setMensagemCoordenadas] = useState("");
    const geocodificacoesTentadas = useRef(new Set());
    const criacaoPedidoEmAndamento = useRef(false);
    const [metodoPagamento, setMetodoPagamento] = useState(() => checkoutInicial?.metodoPagamento || "PIX");
    const [enviando, setEnviando] = useState(false);
    const [iniciandoPagamento, setIniciandoPagamento] = useState(false);
    const [erroCheckout, setErroCheckout] = useState("");
    const [pedidoCriado, setPedidoCriado] = useState(() => checkoutInicial?.pedido || null);
    const [pagamentoPix, setPagamentoPix] = useState(null);
    const [pixCopiado, setPixCopiado] = useState(false);
    const [pedidoEmOperacao, setPedidoEmOperacao] = useState(null);

    // AuthContext can finish restoring a session after the first render. Re-read
    // the pending checkout once the customer ID is available so a refresh does
    // not lose the confirmation screen in that case.
    useEffect(() => {
        if (!dadosAutenticacao?.id || pedidoCriado) return;
        const pendente = carregarCheckoutPendente(dadosAutenticacao.id);
        if (pendente?.pedido) {
            setPedidoCriado(pendente.pedido);
            setMetodoPagamento(pendente.metodoPagamento || "PIX");
        }
    }, [dadosAutenticacao?.id, pedidoCriado]);

    useEffect(() => {
        const aoRetornarDoCheckout = () => {
            const redirecionado = sessionStorage.getItem(CHECKOUT_REDIRECTED_KEY);
            if (!redirecionado) return;
            if (pedidoCriado && String(pedidoCriado.id) === String(redirecionado)) {
                setPedidoCriado(null);
                sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
            }
            sessionStorage.removeItem(CHECKOUT_REDIRECTED_KEY);
            window.dispatchEvent(new Event("candyland:pending-orders-updated"));
        };
        window.addEventListener("pageshow", aoRetornarDoCheckout);
        window.addEventListener("focus", aoRetornarDoCheckout);
        return () => {
            window.removeEventListener("pageshow", aoRetornarDoCheckout);
            window.removeEventListener("focus", aoRetornarDoCheckout);
        };
    }, [pedidoCriado]);

    useEffect(() => {
        let ativo = true;
        if (!dadosAutenticacao?.id) {
            setErroEnderecos("Não foi possível identificar a conta autenticada. Entre novamente.");
            return () => { ativo = false; };
        }

        setCarregandoEnderecos(true);
        setErroEnderecos("");
        getCustomerAddresses(dadosAutenticacao.id)
            .then((lista) => {
                if (!ativo) return;
                setEnderecos(lista);
                const preferido = lista.find((endereco) => endereco.principal) || lista[0];
                setEnderecoId(preferido ? String(preferido.id) : "");
            })
            .catch((error) => {
                if (ativo) setErroEnderecos(error.message || "Não foi possível carregar seus endereços.");
            })
            .finally(() => {
                if (ativo) setCarregandoEnderecos(false);
            });

        return () => { ativo = false; };
    }, [dadosAutenticacao?.id]);

    const enderecoSelecionado = enderecos.find((endereco) => Number(endereco.id) === Number(enderecoId));
    const enderecoRetiradaSelecionado = enderecosRetirada.find((endereco) => Number(endereco.id) === Number(enderecoRetiradaId));

    useEffect(() => {
        setManualLatitude(enderecoSelecionado?.latitude == null ? "" : String(enderecoSelecionado.latitude));
        setManualLongitude(enderecoSelecionado?.longitude == null ? "" : String(enderecoSelecionado.longitude));
        setMensagemCoordenadas("");
    }, [enderecoSelecionado?.id, enderecoSelecionado?.latitude, enderecoSelecionado?.longitude]);

    useEffect(() => {
        let ativo = true;
        if (carrinho.orderType !== "PICKUP" || !carrinho.restauranteId) return undefined;
        setCarregandoEnderecosRetirada(true);
        setErroEnderecosRetirada("");
        getRestaurantPickupAddresses(carrinho.restauranteId)
            .then((lista) => {
                if (!ativo) return;
                setEnderecosRetirada(lista);
                setEnderecoRetiradaId((atual) => {
                    const continuaValido = lista.some((endereco) => String(endereco.id) === String(atual));
                    if (continuaValido) return atual;
                    const preferido = lista.find((endereco) => endereco.principal) || lista[0];
                    return preferido ? String(preferido.id) : "";
                });
            })
            .catch((error) => {
                if (ativo) setErroEnderecosRetirada(error.message || "Não foi possível carregar os endereços de retirada.");
            })
            .finally(() => { if (ativo) setCarregandoEnderecosRetirada(false); });
        return () => { ativo = false; };
    }, [carrinho.orderType, carrinho.restauranteId]);

    function persistirCheckoutSessao(pedido, metodo = metodoPagamento) {
        try {
            sessionStorage.setItem(CHECKOUT_SESSION_KEY, JSON.stringify({
                userId: dadosAutenticacao?.id,
                pedido,
                metodoPagamento: metodo,
            }));
        } catch {
            // A compra já foi gravada no backend; a sessão apenas preserva a tela.
        }
    }

    function limparCheckoutSessao() {
        sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
    }

    useEffect(() => {
        if (carrinho.orderType !== "DELIVERY" || !dadosAutenticacao?.id || !enderecoId || !enderecoSelecionado) return undefined;
        if (enderecoSelecionado.latitude != null && enderecoSelecionado.longitude != null) return undefined;

        const chaveTentativa = `${dadosAutenticacao.id}:${enderecoId}`;
        if (geocodificacoesTentadas.current.has(chaveTentativa)) return undefined;
        geocodificacoesTentadas.current.add(chaveTentativa);
        let ativo = true;
        setGeocodificando(true);
        setErroGeocodificacao("");

        geocodeCustomerAddress(dadosAutenticacao.id, Number(enderecoId))
            .then((atualizado) => {
                if (!ativo) return;
                setEnderecos((atuais) => atuais.map((endereco) => endereco.id === atualizado.id ? atualizado : endereco));
            })
            .catch((error) => {
                if (ativo) setErroGeocodificacao(error.message || "Não foi possível localizar o endereço automaticamente.");
            })
            .finally(() => { if (ativo) setGeocodificando(false); });
        return () => { ativo = false; };
    }, [carrinho.orderType, dadosAutenticacao?.id, enderecoId, enderecoSelecionado?.id, enderecoSelecionado?.latitude, enderecoSelecionado?.longitude]);

    async function tentarLocalizarEnderecoNovamente() {
        if (!dadosAutenticacao?.id || !enderecoId) return;
        geocodificacoesTentadas.current.delete(`${dadosAutenticacao.id}:${enderecoId}`);
        setErroGeocodificacao("");
        setGeocodificando(true);
        try {
            const atualizado = await geocodeCustomerAddress(dadosAutenticacao.id, Number(enderecoId));
            setEnderecos((atuais) => atuais.map((endereco) => endereco.id === atualizado.id ? atualizado : endereco));
        } catch (error) {
            setErroGeocodificacao(error.message || "Não foi possível localizar o endereço automaticamente.");
        } finally {
            setGeocodificando(false);
        }
    }

    async function salvarCoordenadasManuais() {
        if (!dadosAutenticacao?.id || !enderecoId) {
            setErroGeocodificacao("Selecione um endereço antes de salvar as coordenadas.");
            return;
        }
        const latitude = Number(manualLatitude);
        const longitude = Number(manualLongitude);
        if (manualLatitude.trim() === "" || manualLongitude.trim() === ""
            || !Number.isFinite(latitude) || !Number.isFinite(longitude)
            || latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
            setErroGeocodificacao("Informe uma latitude entre -90 e 90 e uma longitude entre -180 e 180.");
            return;
        }
        setSalvandoCoordenadas(true);
        setErroGeocodificacao("");
        setMensagemCoordenadas("");
        try {
            const atualizado = await saveAddressCoordinates(
                dadosAutenticacao.id, Number(enderecoId), latitude, longitude,
            );
            setEnderecos((atuais) => atuais.map((endereco) =>
                Number(endereco.id) === Number(atualizado.id) ? atualizado : endereco
            ));
            setManualLatitude(String(atualizado.latitude));
            setManualLongitude(String(atualizado.longitude));
            geocodificacoesTentadas.current.add(`${dadosAutenticacao.id}:${enderecoId}`);
            setMensagemCoordenadas("Coordenadas salvas. O mapa e o cálculo de entrega já podem usar este endereço.");
        } catch (error) {
            setErroGeocodificacao(error.message || "Não foi possível salvar as coordenadas.");
        } finally {
            setSalvandoCoordenadas(false);
        }
    }

    async function handleIniciarPagamento(pedidoId) {
        setErroCheckout("");
        setIniciandoPagamento(true);
        try {
            const pagamento = await createPayment(pedidoId);
            if (metodoPagamento === "PIX" && pagamento?.pix_copy_paste && pagamento?.pix_qr_code_base64) {
                setPagamentoPix(pagamento);
                setPixCopiado(false);
                return;
            }
            if (!pagamento?.approval_url) {
                throw new Error(pagamento?.message || (metodoPagamento === "PAYPAL" ? "O PayPal não retornou a URL de aprovação." : "O Mercado Pago não retornou a URL do checkout."));
            }
            const url = new URL(pagamento.approval_url);
            if (url.protocol !== "https:") {
                throw new Error("A URL de checkout retornada não é HTTPS. O pagamento não foi aberto.");
            }
            sessionStorage.setItem(CHECKOUT_REDIRECTED_KEY, String(pedidoId));
            window.location.assign(url.href);
        } catch (error) {
            const mensagem = error.message || "Não foi possível iniciar o pagamento selecionado.";
            const mensagemNormalizada = mensagem.toLowerCase();
            if (mensagem.includes("MERCADO_PAGO_ACCESS_TOKEN")) {
                setErroCheckout("Pedido criado, mas o pagamento ainda não foi iniciado: falta configurar o Access Token do Mercado Pago em backend/.env. O pedido continuará pendente; nenhuma cobrança foi realizada.");
            } else if (mensagemNormalizada.includes("fictício") || mensagemNormalizada.includes("mock")) {
                setErroCheckout("O backend ainda está usando o provedor mock de testes. Para usar o Mercado Pago, configure PAYMENT_PROVIDER=mercadopago e MERCADO_PAGO_ACCESS_TOKEN no backend/.env e reinicie o backend. Nenhuma cobrança foi realizada.");
            } else {
                setErroCheckout(`${mensagem} O pedido continua pendente; nenhuma cobrança foi confirmada.`);
            }
        } finally {
            setIniciandoPagamento(false);
        }
    }

    useEffect(() => {
        if (!pedidoCriado?.id || metodoPagamento !== "PIX" || pedidoCriado.status !== "PENDENTE_PAGAMENTO") return undefined;
        let ativo = true;
        const consultarPix = async () => {
            try {
                const pagamento = await getPayment(pedidoCriado.id);
                const pedidoAtual = await getOrder(pedidoCriado.id);
                if (!ativo) return;
                if (pagamento?.provider === "mercadopago" && pagamento?.pix_copy_paste && pagamento?.pix_qr_code_base64) setPagamentoPix(pagamento);
                if (pedidoAtual) setPedidoCriado(pedidoAtual);
                if (pedidoAtual && pedidoAtual.status !== "PENDENTE_PAGAMENTO") { setPagamentoPix(null); window.dispatchEvent(new Event("candyland:pending-orders-updated")); }
            } catch { /* tentativa pode ainda não existir durante os primeiros segundos */ }
        };
        consultarPix();
        const timer = window.setInterval(consultarPix, 5000);
        return () => { ativo = false; window.clearInterval(timer); };
    }, [pedidoCriado?.id, pedidoCriado?.status, metodoPagamento]);

    async function handleCancelarPedidoPendente(pedido) {
        if (!window.confirm(`Deseja desistir do pedido ${pedido.order_code}? O pedido será cancelado e não será enviado ao restaurante.`)) return;
        setErroCheckout("");
        setPedidoEmOperacao(pedido.id);
        try {
            await cancelOrder(pedido.id);
            if (String(pedidoCriado?.id) === String(pedido.id)) {
                setPedidoCriado(null);
                setPagamentoPix(null);
                setPixCopiado(false);
                limparCheckoutSessao();
            }
            window.dispatchEvent(new Event("candyland:pending-orders-updated"));
        } catch (error) {
            setErroCheckout(error.message || "Não foi possível cancelar o pedido.");
        } finally {
            setPedidoEmOperacao(null);
        }
    }

    async function handleFinalizarPedido(event) {
        event.preventDefault();
        setErroCheckout("");

        if (!carrinho.restauranteId || carrinho.itens.length === 0) {
            setErroCheckout("Adicione pelo menos um produto antes de finalizar o pedido.");
            return;
        }
        if (!["PIX", "PAYPAL", "MERCADO_PAGO"].includes(metodoPagamento)) {
            setErroCheckout("Selecione Pix, PayPal ou Mercado Pago.");
            return;
        }
        if (carrinho.orderType === "DELIVERY" && !enderecoId) {
            setErroCheckout("Selecione um endereço ativo para receber o pedido.");
            return;
        }
        if (carrinho.orderType === "DELIVERY" && (!enderecoSelecionado || enderecoSelecionado.latitude == null || enderecoSelecionado.longitude == null)) {
            setErroCheckout("Não foi possível localizar automaticamente este endereço. Tente novamente ou selecione retirada no restaurante.");
            return;
        }
        if (carrinho.orderType === "PICKUP" && !enderecoRetiradaId) {
            setErroCheckout("Selecione a unidade do restaurante onde deseja retirar o pedido.");
            return;
        }

        const payload = {
            restaurant_id: Number(carrinho.restauranteId),
            order_type: carrinho.orderType,
            payment_method: metodoPagamento,
            items: carrinho.itens.map((item) => ({
                produto_id: Number(item.id_produto),
                quantidade: Number(item.quantidade),
            })),
        };
        if (carrinho.orderType === "DELIVERY") payload.delivery_address_id = Number(enderecoId);
        if (carrinho.orderType === "PICKUP") payload.pickup_address_id = Number(enderecoRetiradaId);

        if (criacaoPedidoEmAndamento.current) return;
        criacaoPedidoEmAndamento.current = true;
        setEnviando(true);
        try {
            const pedido = await createOrder(payload);
            setPagamentoPix(null);
            setPixCopiado(false);
            setPedidoCriado(pedido);
            persistirCheckoutSessao(pedido, metodoPagamento);
            limparCarrinho();
            window.dispatchEvent(new Event("candyland:pending-orders-updated"));
            // Primeiro mostramos uma confirmação do pedido. O pagamento só começa
            // quando a pessoa clicar explicitamente em “Continuar para pagamento”.
        } catch (error) {
            criacaoPedidoEmAndamento.current = false;
            setErroCheckout(error.message || "Não foi possível criar o pedido.");
        } finally {
            setEnviando(false);
        }
    }

    return (
        <>
            <Header />
            <main className="container secao">
                <h1 className="titulo-secao">Seu carrinho</h1>

                {pedidoCriado ? (
                    <section className="cart-pedido-sucesso" role="status">
                        <h2>Pedido criado!</h2>
                        <p>Seu pedido <strong>{pedidoCriado.order_code}</strong> foi registrado e aguarda confirmação do pagamento.</p>
                        <dl>
                            <div><dt>Status</dt><dd>{pedidoCriado.status}</dd></div>
                            <div><dt>Modalidade</dt><dd>{pedidoCriado.order_type === "PICKUP" ? "Retirada no restaurante" : "Entrega no endereço"}</dd></div>
                            <div><dt>Forma de pagamento</dt><dd>{metodoPagamento === "PIX" ? "Pix" : metodoPagamento === "PAYPAL" ? "PayPal" : "Mercado Pago"}</dd></div>
                            <div><dt>{pedidoCriado.order_type === "PICKUP" ? "Unidade para retirada" : "Endereço de entrega"}</dt><dd>{pedidoCriado.order_type === "PICKUP" ? (pedidoCriado.pickup_location?.endereco || "Endereço da unidade não disponível") : (pedidoCriado.delivery_location?.endereco || "Endereço de entrega não disponível")}</dd></div>
                            <div><dt>Subtotal</dt><dd>{moeda.format(pedidoCriado.subtotal || 0)}</dd></div>
                            <div><dt>Taxa de entrega</dt><dd>{moeda.format(pedidoCriado.delivery_fee || 0)}</dd></div>
                            <div><dt>Total calculado pelo servidor</dt><dd><strong>{moeda.format(pedidoCriado.total || 0)}</strong></dd></div>
                        </dl>
                        <LocationMap
                            latitude={pedidoCriado.order_type === "PICKUP" ? pedidoCriado.pickup_location?.latitude : pedidoCriado.delivery_location?.latitude}
                            longitude={pedidoCriado.order_type === "PICKUP" ? pedidoCriado.pickup_location?.longitude : pedidoCriado.delivery_location?.longitude}
                            label={pedidoCriado.order_type === "PICKUP" ? (pedidoCriado.pickup_location?.endereco || "Unidade de retirada") : (pedidoCriado.delivery_location?.endereco || "Endereço de entrega")}
                            height={230}
                        />
                        <p className="cart-aviso-checkout">Confira os dados acima. Ao continuar, você será levado ao ambiente seguro de pagamento. O pedido só será confirmado após a validação do pagamento pelo servidor.</p>
                        {erroCheckout && <p className="cart-checkout-erro" role="alert">{erroCheckout}</p>}
                        <button className="btn-principal" type="button" disabled={iniciandoPagamento || Boolean(pagamentoPix)} onClick={() => handleIniciarPagamento(pedidoCriado.id)}>
                            {iniciandoPagamento ? "Iniciando pagamento..." : metodoPagamento === "PIX" ? (pagamentoPix ? "QR Code Pix gerado" : "Gerar Pix") : metodoPagamento === "PAYPAL" ? "Continuar para PayPal" : "Continuar para Mercado Pago"}
                        </button>
                        {pagamentoPix && metodoPagamento === "PIX" && (
                            <section className="cart-pagamento-pix" aria-label="Pagamento Pix">
                                <h3>Escaneie o QR Code Pix</h3>
                                <p>Abra o aplicativo do seu banco, escaneie o código abaixo ou copie o código Pix. O pedido só será confirmado depois da validação do Mercado Pago.</p>
                                <img src={`data:image/jpeg;base64,${pagamentoPix.pix_qr_code_base64}`} alt="QR Code para pagamento Pix" className="cart-pix-qr" />
                                <label htmlFor="pix-copia-cola">Pix Copia e Cola</label>
                                <textarea id="pix-copia-cola" readOnly rows={4} value={pagamentoPix.pix_copy_paste} />
                                <button type="button" className="btn-contorno" onClick={async () => { try { await navigator.clipboard.writeText(pagamentoPix.pix_copy_paste); setPixCopiado(true); } catch { setErroCheckout("Não foi possível copiar automaticamente. Selecione e copie o código Pix manualmente."); } }}>Copiar código Pix</button>
                                {pixCopiado && <p role="status">Código Pix copiado.</p>}
                                <p role="status">Status: {pagamentoPix.status === "APPROVED" ? "Pagamento confirmado" : "Aguardando confirmação"}. A tela consulta o status automaticamente.</p>
                            </section>
                        )}
                        <div className="checkout-result-actions">
                            <Link to={`/pedidos/${pedidoCriado.id}/acompanhar`} className="btn-contorno">Acompanhar pedido</Link>
                            <button type="button" className="btn-contorno cart-pedido-cancelar" disabled={pedidoEmOperacao !== null} onClick={() => handleCancelarPedidoPendente(pedidoCriado)}>
                                {pedidoEmOperacao === pedidoCriado.id ? "Cancelando..." : "🗑 Desistir do pedido"}
                            </button>
                            <Link to="/home" className="btn-contorno" onClick={limparCheckoutSessao}>Voltar às lojas</Link>
                        </div>
                    </section>
                ) : carrinho.itens.length === 0 ? (
                    <>
                        <p className="mensagem-vazia">Seu carrinho está vazio.</p>
                        <Link to="/home" className="btn-contorno">← Continuar comprando</Link>
                    </>
                ) : (
                    <>
                        <p>Pedido em: <strong>{carrinho.restauranteNome}</strong></p>
                        <div className="cart-lista">
                            {carrinho.itens.map((item) => (
                                <div className="cart-item" key={item.id_produto}>
                                    <span className="cart-item-nome">{item.nome}</span>
                                    <div className="cart-item-qtd">
                                        <button type="button" aria-label={`Diminuir ${item.nome}`} onClick={() => atualizarQuantidade(item.id_produto, item.quantidade - 1)}>-</button>
                                        <span>{item.quantidade}</span>
                                        <button type="button" aria-label={`Aumentar ${item.nome}`} onClick={() => atualizarQuantidade(item.id_produto, item.quantidade + 1)}>+</button>
                                    </div>
                                    <span className="cart-item-preco">{moeda.format(item.preco * item.quantidade)}</span>
                                    <button type="button" className="cart-item-remover" aria-label={`Remover ${item.nome}`} onClick={() => removerItem(item.id_produto)}>✕</button>
                                </div>
                            ))}
                        </div>

                        <fieldset className="cart-tipo-pedido">
                            <legend>Como deseja receber?</legend>
                            <label>
                                <input type="radio" name="orderType" value="DELIVERY" checked={carrinho.orderType === "DELIVERY"} onChange={() => atualizarTipoPedido("DELIVERY")} />
                                <span><strong>Receber no endereço</strong><small>O servidor valida coordenadas, raio e taxa de entrega.</small></span>
                            </label>
                            <label>
                                <input type="radio" name="orderType" value="PICKUP" checked={carrinho.orderType === "PICKUP"} onChange={() => atualizarTipoPedido("PICKUP")} />
                                <span><strong>Retirar no restaurante</strong><small>Escolha a unidade onde deseja retirar, sem taxa de entrega.</small></span>
                            </label>
                        </fieldset>

                        {carrinho.orderType === "DELIVERY" && (
                            <div className="cart-checkout-campo checkout-address-field">
                                <label htmlFor="checkout-endereco">Endereço de entrega</label>
                                {carregandoEnderecos ? (
                                    <p role="status">Carregando endereços...</p>
                                ) : enderecos.length > 0 ? (
                                    <select className="checkout-endereco-select" id="checkout-endereco" value={enderecoId} onChange={(event) => setEnderecoId(event.target.value)} required>
                                        <option value="">Selecione um endereço</option>
                                        {enderecos.map((endereco) => (
                                            <option key={endereco.id} value={endereco.id}>
                                                {endereco.principal ? "Principal — " : ""}{formatarEndereco(endereco)}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <p className="cart-aviso-checkout">Nenhum endereço ativo foi encontrado. Cadastre um endereço na conta antes da entrega ou selecione retirada.</p>
                                )}
                                {erroEnderecos && <p className="cart-checkout-erro" role="alert">{erroEnderecos}</p>}
                                {geocodificando && <p className="cart-aviso-checkout" role="status">Validando endereço de entrega...</p>}
                                {enderecoSelecionado && (
                                    enderecoSelecionado.latitude != null && enderecoSelecionado.longitude != null ? (
                                        <p className="cart-endereco-validado" role="status">✓ Endereço pronto para entrega</p>
                                    ) : (
                                        <div className="cart-aviso-localizacao">
                                            <p className="cart-aviso-checkout">Este endereço ainda não tem coordenadas. Se o geocoding automático não estiver configurado, você pode informar latitude e longitude manualmente, sem contratar uma API para a demonstração.</p>
                                            {erroGeocodificacao && (
                                                <div className="cart-checkout-erro" role="alert">
                                                    <p>{erroGeocodificacao}</p>
                                                    <button type="button" className="btn-contorno" disabled={geocodificando} onClick={tentarLocalizarEnderecoNovamente}>
                                                        {geocodificando ? "Localizando..." : "Tentar geocoding novamente"}
                                                    </button>
                                                </div>
                                            )}
                                            <AddressCoordinates
                                                title="Coordenadas para entrega"
                                                latitude={manualLatitude === "" ? null : Number(manualLatitude)}
                                                longitude={manualLongitude === "" ? null : Number(manualLongitude)}
                                                onChange={({ latitude, longitude }) => {
                                                    setManualLatitude(latitude == null ? "" : String(latitude));
                                                    setManualLongitude(longitude == null ? "" : String(longitude));
                                                    setMensagemCoordenadas("");
                                                }}
                                            />
                                            <button type="button" className="btn-principal" disabled={salvandoCoordenadas || !enderecoId} onClick={salvarCoordenadasManuais}>
                                                {salvandoCoordenadas ? "Salvando coordenadas..." : "Salvar coordenadas do endereço"}
                                            </button>
                                            {mensagemCoordenadas && <p className="cart-endereco-validado" role="status">{mensagemCoordenadas}</p>}
                                        </div>
                                    )
                                )}
                                {enderecoSelecionado && (
                                    <LocationMap
                                        latitude={enderecoSelecionado.latitude}
                                        longitude={enderecoSelecionado.longitude}
                                        label={formatarEndereco(enderecoSelecionado)}
                                        height={230}
                                    />
                                )}
                            </div>
                        )}

                        {carrinho.orderType === "PICKUP" && (
                            <div className="cart-checkout-campo checkout-address-field">
                                <label htmlFor="checkout-endereco-retirada">Unidade para retirada</label>
                                {carregandoEnderecosRetirada ? (
                                    <p role="status">Carregando unidades do restaurante...</p>
                                ) : enderecosRetirada.length > 0 ? (
                                    <select
                                        className="checkout-endereco-select"
                                        id="checkout-endereco-retirada"
                                        value={enderecoRetiradaId}
                                        onChange={(event) => setEnderecoRetiradaId(event.target.value)}
                                        required
                                    >
                                        <option value="">Selecione uma unidade</option>
                                        {enderecosRetirada.map((endereco) => (
                                            <option key={endereco.id} value={endereco.id}>
                                                {endereco.principal ? "Unidade principal — " : ""}{formatarEndereco(endereco)}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <p className="cart-aviso-checkout">Nenhuma unidade com endereço ativo foi cadastrada para retirada.</p>
                                )}
                                {erroEnderecosRetirada && <p className="cart-checkout-erro" role="alert">{erroEnderecosRetirada}</p>}
                                {enderecoRetiradaSelecionado && (
                                    <div className="checkout-address-preview">
                                        <strong>{enderecoRetiradaSelecionado.principal ? "Unidade principal" : "Endereço para retirada"}</strong>
                                        <span>{formatarEndereco(enderecoRetiradaSelecionado)}</span>
                                    </div>
                                )}
                                {enderecoRetiradaSelecionado && (
                                    <LocationMap
                                        latitude={enderecoRetiradaSelecionado.latitude}
                                        longitude={enderecoRetiradaSelecionado.longitude}
                                        label={formatarEndereco(enderecoRetiradaSelecionado)}
                                        height={230}
                                    />
                                )}
                            </div>
                        )}

                        <fieldset className="checkout-metodos-pagamento">
                            <legend>Forma de pagamento</legend>
                            <div className="checkout-metodos-opcoes">
                                <label className={`checkout-metodo-pagamento ${metodoPagamento === "PIX" ? "selecionado" : ""}`}>
                                    <input type="radio" name="metodoPagamento" value="PIX" checked={metodoPagamento === "PIX"} onChange={() => setMetodoPagamento("PIX")} />
                                    <span className="checkout-metodo-icone" aria-hidden="true">▦</span>
                                    <span className="checkout-metodo-texto"><strong>Pix</strong><small>QR Code e Copia e Cola</small></span>
                                </label>
                                <label className={`checkout-metodo-pagamento ${metodoPagamento === "PAYPAL" ? "selecionado" : ""}`}>
                                    <input type="radio" name="metodoPagamento" value="PAYPAL" checked={metodoPagamento === "PAYPAL"} onChange={() => setMetodoPagamento("PAYPAL")} />
                                    <span className="checkout-metodo-icone" aria-hidden="true">P</span>
                                    <span className="checkout-metodo-texto"><strong>PayPal</strong><small>Checkout seguro PayPal</small></span>
                                </label>
                                <label className={`checkout-metodo-pagamento ${metodoPagamento === "MERCADO_PAGO" ? "selecionado" : ""}`}>
                                    <input type="radio" name="metodoPagamento" value="MERCADO_PAGO" checked={metodoPagamento === "MERCADO_PAGO"} onChange={() => setMetodoPagamento("MERCADO_PAGO")} />
                                    <span className="checkout-metodo-icone" aria-hidden="true">M</span>
                                    <span className="checkout-metodo-texto"><strong>Mercado Pago</strong><small>Cartão via Checkout Pro</small></span>
                                </label>
                            </div>
                            <p className="checkout-metodo-ajuda">Pix gera QR Code no CandyLand; PayPal e Mercado Pago abrem o checkout seguro do provedor.</p>
                        </fieldset>

                        <div className="cart-total"><span>Subtotal estimado</span><strong>{moeda.format(total)}</strong></div>
                        <p className="cart-aviso-checkout">Preço, estoque e taxa serão recalculados no backend. A confirmação depende de uma resposta válida do Mercado Pago.</p>
                        {erroCheckout && <p className="cart-checkout-erro" role="alert">{erroCheckout}</p>}
                        <button className="btn-principal" type="button" disabled={enviando || iniciandoPagamento || carregandoEnderecos} onClick={handleFinalizarPedido}>
                            {enviando ? "Criando pedido..." : "Confirmar pedido"}
                        </button>
                    </>
                )}
            </main>
        </>
    );
}

export default Cart;
