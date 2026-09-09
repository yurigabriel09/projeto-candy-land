export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isValidPhone(phone) {
  const numbers = phone.replace(/\D/g, "");

  return numbers.length === 11;
}

export function isValidCpf(cpf) {
  const numbers = cpf.replace(/\D/g, "");

  if (numbers.length !== 11) {
    return false;
  }

  if (/^(\d)\1+$/.test(numbers)) {
    return false;
  }

  let sum = 0;

  for (let i = 0; i < 9; i++) {
    sum += Number(numbers[i]) * (10 - i);
  }

  let digit = (sum * 10) % 11;

  if (digit === 10) {
    digit = 0;
  }

  if (digit !== Number(numbers[9])) {
    return false;
  }

  sum = 0;

  for (let i = 0; i < 10; i++) {
    sum += Number(numbers[i]) * (11 - i);
  }

  digit = (sum * 10) % 11;

  if (digit === 10) {
    digit = 0;
  }

  return digit === Number(numbers[10]);
}

export function isValidCnpj(cnpj) {
  const numbers = cnpj.replace(/\D/g, "");

  if (numbers.length !== 14) {
    return false;
  }

  if (/^(\d)\1+$/.test(numbers)) {
    return false;
  }

  const firstWeights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const secondWeights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

  let sum = 0;

  for (let i = 0; i < 12; i++) {
    sum += Number(numbers[i]) * firstWeights[i];
  }

  let digit = sum % 11;
  digit = digit < 2 ? 0 : 11 - digit;

  if (digit !== Number(numbers[12])) {
    return false;
  }

  sum = 0;

  for (let i = 0; i < 13; i++) {
    sum += Number(numbers[i]) * secondWeights[i];
  }

  digit = sum % 11;
  digit = digit < 2 ? 0 : 11 - digit;

  return digit === Number(numbers[13]);
}

export function isValidCep(cep) {
  const numbers = cep.replace(/\D/g, "");

  return numbers.length === 8;
}