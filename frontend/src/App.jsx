import React, { useEffect, useState } from 'react';
import {
  DEPARTMENTS,
  DOCTORS,
  EMPTY_FORM,
  GENDERS,
  STATUSES,
  WARDS,
} from './constants';
import { todayISO, validatePatient } from './validation';

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  let data = {};
  try {
    data = await response.json();
  } catch (error) {
    data = {};
  }
  if (!response.ok) {
    const failure = new Error(data.message || 'Something went wrong. Please try again.');
    failure.data = data;
    throw failure;
  }
  return data;
}

function Field({ label, error, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}

const FILTER_FIELDS = [
  { key: 'ward', placeholder: 'All wards', options: WARDS },
  { key: 'department', placeholder: 'All departments', options: DEPARTMENTS },
  { key: 'doctor', placeholder: 'All doctors', options: DOCTORS },
];

export default function App() {
  const [patients, setPatients] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    ward: '',
    department: '',
    doctor: '',
  });
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  function showNotice(type, text) {
    setNotice({ type, text });
  }

  async function refresh(currentFilters = filters) {
    setLoading(true);
    const params = new URLSearchParams();
    Object.entries(currentFilters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    try {
      const data = await api(`/api/patients?${params.toString()}`);
      setPatients(data.patients);
    } catch (error) {
      showNotice('error', error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM, admission_date: todayISO() });
    setFormErrors({});
    setFormOpen(true);
  }

  function openEdit(patient) {
    setEditingId(patient.id);
    setForm({
      name: patient.name,
      age: String(patient.age),
      gender: patient.gender,
      ward: patient.ward,
      department: patient.department,
      doctor: patient.doctor,
      admission_date: patient.admission_date,
      status: patient.status,
    });
    setFormErrors({});
    setFormOpen(true);
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setFormErrors((current) => {
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const errors = validatePatient(form);
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    setSaving(true);
    try {
      const isEdit = editingId !== null;
      const data = await api(isEdit ? `/api/patients/${editingId}` : '/api/patients', {
        method: isEdit ? 'PUT' : 'POST',
        body: JSON.stringify({ ...form, age: Number(form.age) }),
      });
      setFormOpen(false);
      showNotice('success', data.message);
      await refresh();
    } catch (error) {
      if (error.data && error.data.errors) setFormErrors(error.data.errors);
      showNotice('error', error.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDischarge(patient) {
    try {
      const data = await api(`/api/patients/${patient.id}/discharge`, {
        method: 'PATCH',
        body: '{}',
      });
      showNotice('success', data.message);
      await refresh();
    } catch (error) {
      showNotice('error', error.message);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      const data = await api(`/api/patients/${deleteTarget.id}`, { method: 'DELETE' });
      setDeleteTarget(null);
      showNotice('success', data.message);
      await refresh();
    } catch (error) {
      showNotice('error', error.message);
    }
  }

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="app">
      <header className="topbar">
        <div className="wrap topbar-inner">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">+</span>
            <span>
              <strong>Patient Admissions</strong>
              <small>Unriddle Technologies · DScribe</small>
            </span>
          </div>
          <span className="count-pill">{patients.length} patients</span>
        </div>
      </header>

      <main className="wrap main">
        {notice && (
          <div className={`notice ${notice.type}`} role="status">
            <span>{notice.text}</span>
            <button
              type="button"
              className="notice-close"
              onClick={() => setNotice(null)}
              aria-label="Dismiss message"
            >
              ×
            </button>
          </div>
        )}

        <section className="card toolbar" aria-label="Patient filters">
          <div className="search-wrap">
            <span className="search-icon" aria-hidden="true">⌕</span>
            <input
              type="search"
              value={filters.search}
              onChange={(event) => updateFilter('search', event.target.value)}
              placeholder="Search patients by name"
              aria-label="Search patients by name"
            />
          </div>
          <div className="filter-grid">
            {FILTER_FIELDS.map(({ key, placeholder, options }) => (
              <select
                key={key}
                value={filters[key]}
                onChange={(event) => updateFilter(key, event.target.value)}
                aria-label={placeholder}
              >
                <option value="">{placeholder}</option>
                {options.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            ))}
          </div>
          <div className="toolbar-actions">
            <button
              type="button"
              className="btn ghost"
              onClick={() => setFilters({ search: '', ward: '', department: '', doctor: '' })}
              disabled={!hasFilters}
            >
              Clear filters
            </button>
            <button type="button" className="btn primary" onClick={openCreate}>
              Add patient
            </button>
          </div>
        </section>

        <section className="card list" aria-label="Patient list">
          <div className="list-title">
            <h1>Patient records</h1>
            <span>{loading ? 'Loading…' : `${patients.length} shown`}</span>
          </div>

          <div className="list-head" aria-hidden="true">
            <span>Patient</span>
            <span>Ward</span>
            <span>Department</span>
            <span>Doctor</span>
            <span>Admitted</span>
            <span>Status</span>
            <span>Actions</span>
          </div>

          {loading ? (
            <div className="empty">Loading patient records…</div>
          ) : patients.length === 0 ? (
            <div className="empty">
              <strong>No patients found.</strong>
              <span>Try changing your filters or add a new patient.</span>
            </div>
          ) : (
            patients.map((patient) => (
              <div className="patient-row" key={patient.id}>
                <div className="cell patient-cell">
                  <span className="avatar" aria-hidden="true">{patient.name.charAt(0)}</span>
                  <span className="patient-identity">
                    <strong>{patient.name}</strong>
                    <small>{patient.age} yrs · {patient.gender}</small>
                  </span>
                </div>
                <div className="cell" data-label="Ward">{patient.ward}</div>
                <div className="cell" data-label="Department">{patient.department}</div>
                <div className="cell" data-label="Doctor">{patient.doctor}</div>
                <div className="cell" data-label="Admitted">{patient.admission_date}</div>
                <div className="cell" data-label="Status">
                  <span className={`badge ${patient.status === 'Discharged' ? 'discharged' : 'admitted'}`}>
                    {patient.status}
                  </span>
                </div>
                <div className="cell actions">
                  <button type="button" className="btn tiny" onClick={() => openEdit(patient)}>
                    Edit
                  </button>
                  {patient.status === 'Admitted' && (
                    <button
                      type="button"
                      className="btn tiny teal"
                      onClick={() => handleDischarge(patient)}
                    >
                      Discharge
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn tiny danger"
                    onClick={() => setDeleteTarget(patient)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </section>
      </main>

      {formOpen && (
        <div
          className="modal-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setFormOpen(false);
          }}
        >
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="form-title">
            <div className="modal-head">
              <div>
                <h2 id="form-title">{editingId !== null ? 'Edit patient' : 'Add patient'}</h2>
                <p>Fields marked with an error must be corrected before saving.</p>
              </div>
              <button
                type="button"
                className="icon-btn"
                onClick={() => setFormOpen(false)}
                aria-label="Close form"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} noValidate>
              <div className="form-grid">
                <Field label="Full name" error={formErrors.name}>
                  <input
                    name="name"
                    type="text"
                    value={form.name}
                    onChange={(event) => updateForm('name', event.target.value)}
                    placeholder="e.g. Jane Smith"
                    className={formErrors.name ? 'invalid' : ''}
                  />
                </Field>
                <Field label="Age" error={formErrors.age}>
                  <input
                    name="age"
                    type="number"
                    min="0"
                    max="120"
                    value={form.age}
                    onChange={(event) => updateForm('age', event.target.value)}
                    className={formErrors.age ? 'invalid' : ''}
                  />
                </Field>
                <Field label="Gender" error={formErrors.gender}>
                  <select
                    name="gender"
                    value={form.gender}
                    onChange={(event) => updateForm('gender', event.target.value)}
                    className={formErrors.gender ? 'invalid' : ''}
                  >
                    <option value="">Select gender</option>
                    {GENDERS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Ward" error={formErrors.ward}>
                  <select
                    name="ward"
                    value={form.ward}
                    onChange={(event) => updateForm('ward', event.target.value)}
                    className={formErrors.ward ? 'invalid' : ''}
                  >
                    <option value="">Select ward</option>
                    {WARDS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Department" error={formErrors.department}>
                  <select
                    name="department"
                    value={form.department}
                    onChange={(event) => updateForm('department', event.target.value)}
                    className={formErrors.department ? 'invalid' : ''}
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Doctor" error={formErrors.doctor}>
                  <select
                    name="doctor"
                    value={form.doctor}
                    onChange={(event) => updateForm('doctor', event.target.value)}
                    className={formErrors.doctor ? 'invalid' : ''}
                  >
                    <option value="">Select doctor</option>
                    {DOCTORS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Admission date" error={formErrors.admission_date}>
                  <input
                    name="admission_date"
                    type="date"
                    max={todayISO()}
                    value={form.admission_date}
                    onChange={(event) => updateForm('admission_date', event.target.value)}
                    className={formErrors.admission_date ? 'invalid' : ''}
                  />
                </Field>
                <Field label="Status" error={formErrors.status}>
                  <select
                    name="status"
                    value={form.status}
                    onChange={(event) => updateForm('status', event.target.value)}
                    className={formErrors.status ? 'invalid' : ''}
                  >
                    {STATUSES.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => setFormOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn primary" disabled={saving}>
                  {saving ? 'Saving…' : editingId !== null ? 'Save changes' : 'Add patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="modal-backdrop" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setDeleteTarget(null);
        }}>
          <div className="modal small" role="alertdialog" aria-modal="true" aria-labelledby="delete-title">
            <div className="modal-head">
              <div>
                <h2 id="delete-title">Delete this patient?</h2>
                <p>
                  {deleteTarget.name} will be removed from the records. This cannot be undone.
                </p>
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn ghost" onClick={() => setDeleteTarget(null)}>
                Cancel
              </button>
              <button type="button" className="btn danger-solid" onClick={handleDelete}>
                Delete patient
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
