import React, { useEffect, useState } from 'react';
import { updateCustomerProfile } from '../../api/profile';
import { toast } from '../../components/ui/toast';
import { formatDate, getCustomerDisplayName } from '../../utils/profileUtils';

const ProfileInfoPanel = ({ customer, onUpdated, startEditing = false, onEditingChange }) => {
  const [isEditing, setIsEditing] = useState(startEditing);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    country: '',
    phone_number: '',
    address: '',
  });

  useEffect(() => {
    setIsEditing(startEditing);
  }, [startEditing]);

  useEffect(() => {
    if (!customer) {
      return;
    }

    setForm({
      first_name: customer.user?.first_name || '',
      last_name: customer.user?.last_name || '',
      country: customer.country || '',
      phone_number: customer.phone_number || '',
      address: customer.address || '',
    });
  }, [customer]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!customer?.id) {
      return;
    }

    setIsSaving(true);

    try {
      const updated = await updateCustomerProfile(customer.id, form);
      toast.success('Profil mis à jour');
      setIsEditing(false);
      onEditingChange?.(false);
      onUpdated?.(updated);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        Object.values(err?.response?.data || {})?.flat?.()?.[0] ||
        'Impossible de mettre à jour le profil.';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!customer) {
    return null;
  }

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Mon profil</h2>
          <p className="profile-panel-subtitle">
            Gérez vos informations personnelles et de livraison.
          </p>
        </div>
        {!isEditing && (
          <button
            type="button"
            className="profile-btn profile-btn-outline"
            onClick={() => {
              setIsEditing(true);
              onEditingChange?.(true);
            }}
          >
            Modifier
          </button>
        )}
      </div>

      {!isEditing ? (
        <dl className="profile-info-grid">
          <div className="profile-info-item">
            <dt>Nom complet</dt>
            <dd>{getCustomerDisplayName(customer)}</dd>
          </div>
          <div className="profile-info-item">
            <dt>Email</dt>
            <dd>{customer.user?.email || '—'}</dd>
          </div>
          <div className="profile-info-item">
            <dt>Pays</dt>
            <dd>{customer.country || '—'}</dd>
          </div>
          <div className="profile-info-item">
            <dt>Téléphone</dt>
            <dd>{customer.phone_number || '—'}</dd>
          </div>
          <div className="profile-info-item profile-info-item-wide">
            <dt>Adresse</dt>
            <dd>{customer.address || '—'}</dd>
          </div>
          <div className="profile-info-item">
            <dt>Membre depuis</dt>
            <dd>{formatDate(customer.date_created)}</dd>
          </div>
        </dl>
      ) : (
        <form className="profile-form" onSubmit={handleSubmit}>
          <div className="profile-form-grid">
            <label className="profile-field">
              <span>Prénom</span>
              <input
                type="text"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
              />
            </label>
            <label className="profile-field">
              <span>Nom</span>
              <input
                type="text"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
              />
            </label>
            <label className="profile-field">
              <span>Pays (code ISO)</span>
              <input
                type="text"
                name="country"
                value={form.country}
                onChange={handleChange}
                placeholder="SN"
              />
            </label>
            <label className="profile-field">
              <span>Téléphone</span>
              <input
                type="tel"
                name="phone_number"
                value={form.phone_number}
                onChange={handleChange}
                placeholder="+221..."
              />
            </label>
            <label className="profile-field profile-field-wide">
              <span>Adresse</span>
              <textarea
                name="address"
                value={form.address}
                onChange={handleChange}
                rows={3}
              />
            </label>
          </div>
          <div className="profile-form-actions">
            <button
              type="button"
              className="profile-btn profile-btn-ghost"
              onClick={() => {
                setIsEditing(false);
                onEditingChange?.(false);
              }}
              disabled={isSaving}
            >
              Annuler
            </button>
            <button type="submit" className="profile-btn profile-btn-primary" disabled={isSaving}>
              {isSaving ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
};

export default ProfileInfoPanel;
