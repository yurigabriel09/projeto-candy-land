const VIA_CEP_URL = "https://viacep.com.br/ws";

export async function getAddressByCep(cep) {
    const cleanCep = cep.replace(/\D/g, "");

    if (cleanCep.length !== 8) {
        return null;
    }

    const response = await fetch(`${VIA_CEP_URL}/${cleanCep}/json/`);

    if (!response.ok) {
        throw new Error("Erro ao consultar o CEP");
    }

    const data = await response.json();

    if (data.erro) {
        throw new Error("CEP não encontrado");
    }

    return {
        address: data.logradouro || "",
        neighborhood: data.bairro || "",
        city: data.localidade || "",
        state: data.uf || ""
    };
}