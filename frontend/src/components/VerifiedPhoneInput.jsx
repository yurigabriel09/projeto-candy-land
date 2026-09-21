import { parsePhoneNumberFromString } from "libphonenumber-js";
import { countries } from "../utils/countries";

function VerifiedPhoneInput({ value = "" }) {
    const phone = parsePhoneNumberFromString(value);

    if (!phone) {
        return (
            <input
                type="tel"
                value={value}
                disabled
                readOnly
            />
        );
    }

    const countryCode = phone.country || "BR";
    const country = countries.find((item) => item.code === countryCode);

    const flag = country?.flag || "🌎";
    const dialCode = phone.countryCallingCode
        ? `+${phone.countryCallingCode}`
        : "";

    const nationalNumber = phone.formatNational();

    return (
        <input
            id="phone"
            name="phone"
            type="tel"
            value={`${flag} ${dialCode} ${nationalNumber}`}
            disabled
            readOnly
        />
    );
}

export default VerifiedPhoneInput;