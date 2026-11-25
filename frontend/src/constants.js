export const GENDERS = ['Male', 'Female', 'Other'];

export const WARDS = ['General', 'ICU', 'Pediatrics', 'Maternity', 'Emergency', 'Surgery'];

export const DEPARTMENTS = [
  'General Medicine',
  'Cardiology',
  'Neurology',
  'Orthopedics',
  'Pediatrics',
  'Dermatology',
];

export const DOCTORS = [
  'Dr. A Sharma',
  'Dr. R Iyer',
  'Dr. M Rao',
  'Dr. S Menon',
  'Dr. K Verma',
  'Dr. P Nair',
];

export const STATUSES = ['Admitted', 'Discharged'];

export const OPTIONS = {
  gender: GENDERS,
  ward: WARDS,
  department: DEPARTMENTS,
  doctor: DOCTORS,
  status: STATUSES,
};

export const EMPTY_FORM = {
  name: '',
  age: '',
  gender: '',
  ward: '',
  department: '',
  doctor: '',
  admission_date: '',
  status: 'Admitted',
};
