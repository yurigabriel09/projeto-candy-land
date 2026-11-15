import { useCallback, useEffect, useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { getPayment } from "../services/orderService";
import { gerarPixEstatico } from "../utils/pixBrCode";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const INTERVALO_MS = 5000;

const CHAVE_ESTATICA = import.meta.env.VITE_PIX_STATIC_KEY || "";
const NOME_ESTATICO = import.meta.env.VITE_PIX_NOME || "Candyland";
const CIDADE_ESTATICA = import.meta.env.VITE_PIX_CIDADE || "Sao Paulo";

function PixPayment({ pedidoId, pagamento, total, onConfirmado, onVoltar }) {
    const [dados, setDados] = useState(pagamento || {});
    const [modo, setModo] = useState("dinamico");
    const [copiado, setCopiado] = useState(false);
    const [verificando, setVerificando] = useState(false);
    const [aviso, setAviso] = useState("");
    const confirmou = useRef(false);

    const copiaCola = dados.pix_copy_paste || "";
    const qrBase64 = dados.pix_qr_code_base64 || "";
    const temDinamico = Boolean(copiaCola || qrBase64);
    const estatico = CHAVE_ESTATICA
        ? gerarPixEstatico({ chave: CHAVE_ESTATICA, nome: NOME_ESTATICO, cidade: CIDADE_ESTATICA, valor: total, txid: `PED${pedidoId}` })
        : "";
    const modoAtual = temDinamico ? modo : "estatico";
    const codigoAtual = modoAtual === "dinamico" ? copiaCola : estatico;

    const status = dados.status || "PENDING";
    const aprovado = status === "APPROVED";
    const recusado = ["REJECTED", "CANCELLED", "FAILED"].includes(status);

    const consultar = useCallback(async (manual = false) => {
        if (manual) { setVerificando(true); setAviso(""); }
        try {
            const atual = await getPayment(pedidoId);
            if (atual) setDados((antes) => ({ ...antes, ...atual }));
            if (manual && atual?.status === "PENDING") setAviso("Ainda não recebemos o pagamento. Assim que o banco confirmar, esta tela atualiza sozinha.");
        } catch (e) {
            if (manual) setAviso(e.message || "Não foi possível consultar o pagamento agora.");
        } finally {
            if (manual) setVerificando(false);
        }
    }, [pedidoId]);

    // Consulta automática enquanto o pagamento estiver pendente
    useEffect(() => {
        if (aprovado || recusado) return undefined;
        const timer = setInterval(() => consultar(false), INTERVALO_MS);
        return () => clearInterval(timer);
    }, [aprovado, recusado, consultar]);

    useEffect(() => {
        if (aprovado && !confirmou.current) {
            confirmou.current = true;
            onConfirmado?.();
        }
    }, [aprovado, onConfirmado]);

    async function copiar() {
        if (!codigoAtual) return;
        try {
            await navigator.clipboard.writeText(codigoAtual);
        } catch {
            const area = document.getElementById("pixpay-codigo");
            area?.select();
            document.execCommand?.("copy");
        }
        setCopiado(true);
        setTimeout(() => setCopiado(false), 2500);
    }

    if (aprovado) {
        return (
            <div className="conta-card pixpay-card pixpay-ok" role="status">
                <span className="pixpay-emoji">✅</span>
                <h3 className="pixpay-title">Pagamento confirmado!</h3>
                <p className="pixpay-desc">Recebemos o seu Pix. Redirecionando para o acompanhamento do pedido...</p>
            </div>
        );
    }

    if (recusado) {
        return (
            <div className="conta-card pixpay-card pixpay-erro" role="alert">
                <span className="pixpay-emoji">⚠️</span>
                <h3 className="pixpay-title">Pagamento não concluído</h3>
                <p className="pixpay-desc">{dados.message || "O Pix foi recusado ou cancelado. Você pode tentar novamente pelo carrinho."}</p>
                <button type="button" className="btn-contorno" onClick={onVoltar}>Voltar</button>
            </div>
        );
    }

    return (
        <div className="conta-card pixpay-card">
            <div className="pixpay-header">
                <span className="pixpay-spinner" aria-hidden="true" />
                <div>
                    <h3 className="pixpay-title">Aguardando confirmação do pagamento</h3>
                    <p className="pixpay-desc">Pague {moeda.format(total)} via Pix. Esta tela atualiza sozinha quando o pagamento for confirmado.</p>
                </div>
            </div>

            {temDinamico && estatico && (
                <div className="pixpay-tabs">
                    <button type="button" className={`pixpay-tab ${modoAtual === "dinamico" ? "active" : ""}`} onClick={() => setModo("dinamico")}>QR Code do pedido</button>
                    <button type="button" className={`pixpay-tab ${modoAtual === "estatico" ? "active" : ""}`} onClick={() => setModo("estatico")}>QR estático da loja</button>
                </div>
            )}

            <div className="pixpay-qr">
                {modoAtual === "dinamico" && qrBase64 ? (
                    <img src={qrBase64.startsWith("data:") ? qrBase64 : `data:image/png;base64,${qrBase64}`} alt="QR Code Pix do pedido" width={220} height={220} />
                ) : codigoAtual ? (
                    <QRCodeSVG value={codigoAtual} size={220} marginSize={2} />
                ) : (
                    <p className="pixpay-desc">QR Code indisponível no momento.</p>
                )}
            </div>

            {modoAtual === "estatico" && (
                <p className="pixpay-aviso">
                    Este é um Pix estático: o valor e a chave já vão preenchidos, mas o banco não avisa a Candyland sozinho.
                    Após pagar, a confirmação pode levar mais tempo.
                </p>
            )}

            {codigoAtual && (
                <div className="pixpay-copia">
                    <label htmlFor="pixpay-codigo">Pix Copia e Cola</label>
                    <textarea id="pixpay-codigo" readOnly rows={3} value={codigoAtual} onFocus={(e) => e.target.select()} />
                    <button type="button" className="primary-button" onClick={copiar}>
                        {copiado ? "✓ Código copiado!" : "Copiar código"}
                    </button>
                </div>
            )}

            {!temDinamico && !estatico && dados.approval_url && (
                <a className="primary-button" href={dados.approval_url} target="_blank" rel="noreferrer">Abrir página de pagamento</a>
            )}

            <ol className="pixpay-passos">
                <li>Abra o app do seu banco e escolha pagar com Pix.</li>
                <li>Escaneie o QR Code ou cole o código copiado.</li>
                <li>Confira o valor e confirme. Pronto!</li>
            </ol>

            {aviso && <p className="pixpay-aviso" role="status">{aviso}</p>}

            <div className="pixpay-acoes">
                <button type="button" className="btn-contorno" onClick={() => consultar(true)} disabled={verificando}>
                    {verificando ? "Verificando..." : "Já paguei, verificar agora"}
                </button>
                <button type="button" className="btn-contorno" onClick={onVoltar}>Cancelar e voltar</button>
            </div>
        </div>
    );
}

export default PixPayment;