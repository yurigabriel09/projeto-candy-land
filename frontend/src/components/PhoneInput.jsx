import { countries } from "../utils/countries";
import { maskPhone } from "../utils/masks";

function PhoneInput({ value = "", countryCode = "BR", onChange, onCountryChange, disabled = false }) {
    const country = countries.find((item) => item.code === countryCode) || countries[0];

    function handlePhoneChange(event) {
        const novoValor = country.code === "BR"
            ? maskPhone(event.target.value)
            : event.target.value.replace(/\D/g, "");

        onChange(novoValor);
    }

    return (
        <div className="phone-input">
            <select
                value={country.code}
                onChange={(event) => onCountryChange(event.target.value)}
                disabled={disabled}
                aria-label="País"
            >
                {countries.map((item) => (
                    <option key={item.code} value={item.code}>
                        {item.flag} {item.dialCode}
                    </option>
                ))}
            </select>

            <input
                type="tel"
                value={value}
                onChange={handlePhoneChange}
                placeholder={country.code === "BR" ? "(11) 91234-5678" : "Número de telefone"}
                disabled={disabled}
                inputMode="tel"
            />
        </div>
    );
}

export default PhoneInput;