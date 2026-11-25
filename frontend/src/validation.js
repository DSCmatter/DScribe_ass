import { OPTIONS } from './constants';

const NAME_PATTERN = /^[A-Za-z]+(?: [A-Za-z]+)*$/;

export function parseDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '');
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(year, month - 1, day);
  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    return null;
  }
  return parsed;
}

export function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export function validatePatient(form) {
  const errors = {};
  const name = (form.name || '').trim();

  if (!name) {
    errors.name = 'Name is required.';
  } else if (!NAME_PATTERN.test(name)) {
    errors.name = 'Name must contain letters only.';
  }

  const rawAge = String(form.age ?? '').trim();
  if (!rawAge) {
    errors.age = 'Age is required.';
  } else if (!/^\d+$/.test(rawAge)) {
    errors.age = 'Age must be a number between 0 and 120.';
  } else {
    const age = Number(rawAge);
    if (!Number.isInteger(age) || age < 0 || age > 120) {
      errors.age = 'Age must be a number between 0 and 120.';
    }
  }

  Object.entries(OPTIONS).forEach(([field, values]) => {
    const value = form[field];
    const label = field.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());
    if (!value) {
      errors[field] = `${label} is required.`;
    } else if (!values.includes(value)) {
      errors[field] = `Select a valid ${label.toLowerCase()}.`;
    }
  });

  const admissionDate = parseDate(form.admission_date);
  if (!form.admission_date) {
    errors.admission_date = 'Admission date is required.';
  } else if (!admissionDate) {
    errors.admission_date = 'Enter a valid admission date.';
  } else {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (admissionDate > today) {
      errors.admission_date = 'Admission date cannot be in the future.';
    }
  }

  return errors;
}
