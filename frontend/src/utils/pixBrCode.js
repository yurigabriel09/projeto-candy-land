// Gera o "Pix Copia e Cola" (BR Code EMV) ESTÁTICO.
// Esse código é montado no próprio navegador a partir da chave Pix da loja.
// Atenção: Pix estático NÃO confirma o pagamento sozinho (não há txid rastreável
// pelo banco), por isso a tela avisa o cliente e depende da confirmação do backend.

function campo(id, valor) {
    const tamanho = String(valor.length).padStart(2, "0");
    return `${id}${tamanho}${valor}`;
}

export function crc16(texto) {
    let crc = 0xffff;
    for (let i = 0; i < texto.length; i++) {
        crc ^= texto.charCodeAt(i) << 8;
        for (let j = 0; j < 8; j++) {
            crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff;
        }
    }
    return crc.toString(16).toUpperCase().padStart(4, "0");
}

// O padrão aceita só letras/números ASCII sem acento nos textos do merchant.
function limpar(texto, max) {
    return String(texto || "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/[^A-Za-z0-9 ]/g, "")
        .trim()
        .slice(0, max)
        .toUpperCase();
}

export function gerarPixEstatico({ chave, nome, cidade, valor, txid = "***" }) {
    if (!chave) return "";
    const conta = campo("00", "br.gov.bcb.pix") + campo("01", String(chave).trim());
    const partes = [
        campo("00", "01"),
        campo("26", conta),
        campo("52", "0000"),
        campo("53", "986"),
    ];
    const v = Number(valor);
    if (v > 0) partes.push(campo("54", v.toFixed(2)));
    partes.push(
        campo("58", "BR"),
        campo("59", limpar(nome, 25) || "CANDYLAND"),
        campo("60", limpar(cidade, 15) || "SAO PAULO"),
        campo("62", campo("05", limpar(txid, 25).replace(/ /g, "") || "***")),
    );
    const semCrc = partes.join("") + "6304";
    return semCrc + crc16(semCrc);
}