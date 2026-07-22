import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import Select from 'react-select';
import PhoneInputModule from 'react-phone-input-2';
import { parsePhoneNumberFromString } from 'libphonenumber-js';
import countryData from 'country-telephone-data';
import { useAuth } from '../../context/authState';
import { validateRegister } from '../../api/auth';
import AuthPageShell from '../../components/auth/AuthPageShell';
import { ApiValidationError, applyApiFieldErrors, parseApiError } from '../../utils/apiErrors';
import { buildCountryOptions, detectDefaultCountry } from '../../utils/countryTelephone';
import { resolveDefaultExport } from '../../utils/resolveDefaultExport';
import 'react-phone-input-2/lib/style.css';
import './Auth.css';

const PhoneInput = resolveDefaultExport(PhoneInputModule);

const Register = () => {
  const { register, loading } = useAuth();
  const [registerData, setRegisterData] = useState({
    first_name: '', last_name: '', email: '', password: '', confirm_password: '',
  });
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [registerErrors, setRegisterErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [visiblePasswords, setVisiblePasswords] = useState({ password: false, confirm_password: false });
  const countryOptions = useMemo(() => buildCountryOptions(countryData), []);

  useEffect(() => {
    setSelectedCountry(detectDefaultCountry(countryOptions));
  }, [countryOptions]);

  const clearError = (name) => {
    if (registerErrors[name]) setRegisterErrors((previous) => ({ ...previous, [name]: '' }));
    if (submitError) setSubmitError('');
  };

  const handleChange = ({ target: { name, value } }) => {
    setRegisterData((previous) => ({ ...previous, [name]: value }));
    clearError(name);
  };

  const formatPhoneNumber = (rawValue, countryCode = '') => {
    if (!rawValue) return '';
    const trimmed = rawValue.trim();
    const sanitized = trimmed.startsWith('+') ? trimmed : `+${trimmed}`;
    const phone = parsePhoneNumberFromString(sanitized, countryCode || undefined);
    return phone?.isValid() ? phone.format('E.164') : null;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (loading) return;

    const payload = {
      ...registerData,
      country: selectedCountry?.value || '',
      phone_number: phoneNumber ? formatPhoneNumber(phoneNumber, selectedCountry?.value || '') : '',
    };
    if (phoneNumber && !payload.phone_number) {
      setRegisterErrors({ phone_number: 'Numéro de téléphone invalide' });
      return;
    }
    const validation = validateRegister(payload);
    if (!validation.isValid) {
      setRegisterErrors(validation.errors);
      return;
    }
    try {
      await register(payload);
      setRegisterData((previous) => ({ ...previous, password: '', confirm_password: '' }));
    } catch (error) {
      if (error instanceof ApiValidationError) {
        applyApiFieldErrors(error.fieldErrors, setRegisterErrors);
        setSubmitError(error.message);
        return;
      }
      const parsed = parseApiError(error, "Erreur lors de l'inscription");
      applyApiFieldErrors(parsed.fieldErrors, setRegisterErrors);
      setSubmitError(parsed.message);
    }
  };

  const togglePassword = (name) => {
    setVisiblePasswords((previous) => ({ ...previous, [name]: !previous[name] }));
  };

  const passwordField = (name, label, errorId, toggleLabels) => (
    <div className="form-group">
      <label htmlFor={name}>{label}</label>
      <div className="auth-password-field">
        <input
          type={visiblePasswords[name] ? 'text' : 'password'}
          id={name}
          name={name}
          value={registerData[name]}
          onChange={handleChange}
          className={registerErrors[name] ? 'error' : ''}
          placeholder="••••••••"
          disabled={loading}
          autoComplete="new-password"
          aria-invalid={Boolean(registerErrors[name])}
          aria-describedby={registerErrors[name] ? errorId : undefined}
        />
        <button
          type="button"
          className="auth-password-toggle"
          onClick={() => togglePassword(name)}
          aria-label={visiblePasswords[name] ? toggleLabels.hide : toggleLabels.show}
          aria-pressed={visiblePasswords[name]}
          disabled={loading}
        >
          {visiblePasswords[name] ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
        </button>
      </div>
      {registerErrors[name] && <span className="error-message" id={errorId}>{registerErrors[name]}</span>}
    </div>
  );

  const phoneCountryCode = selectedCountry?.value?.toLowerCase() || 'fr';

  return (
    <AuthPageShell
      eyebrow="Bienvenue chez LobelStore"
      title="Créer un compte"
      description="Créez votre espace personnel pour une expérience plus fluide et attentive."
      note="Votre sélection, vos commandes et vos envies réunies dans un espace qui vous ressemble."
    >
      <form onSubmit={handleSubmit} className="auth-entry-form auth-entry-form--register" noValidate>
        {submitError && <div className="auth-error" role="alert">{submitError}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="first_name">Prénom</label>
            <input id="first_name" name="first_name" value={registerData.first_name} onChange={handleChange} className={registerErrors.first_name ? 'error' : ''} placeholder="Awa" disabled={loading} autoComplete="given-name" aria-invalid={Boolean(registerErrors.first_name)} aria-describedby={registerErrors.first_name ? 'register-first-name-error' : undefined} />
            {registerErrors.first_name && <span className="error-message" id="register-first-name-error">{registerErrors.first_name}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="last_name">Nom</label>
            <input id="last_name" name="last_name" value={registerData.last_name} onChange={handleChange} className={registerErrors.last_name ? 'error' : ''} placeholder="Traoré" disabled={loading} autoComplete="family-name" aria-invalid={Boolean(registerErrors.last_name)} aria-describedby={registerErrors.last_name ? 'register-last-name-error' : undefined} />
            {registerErrors.last_name && <span className="error-message" id="register-last-name-error">{registerErrors.last_name}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input type="email" id="email" name="email" value={registerData.email} onChange={handleChange} className={registerErrors.email ? 'error' : ''} placeholder="votre@email.com" disabled={loading} autoComplete="email" aria-invalid={Boolean(registerErrors.email)} aria-describedby={registerErrors.email ? 'register-email-error' : undefined} />
          {registerErrors.email && <span className="error-message" id="register-email-error">{registerErrors.email}</span>}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="country">Pays</label>
            <Select inputId="country" instanceId="country" value={selectedCountry} options={countryOptions} onChange={(option) => { setSelectedCountry(option || null); clearError('country'); }} placeholder="Sélectionnez votre pays" isSearchable classNamePrefix="react-select" isDisabled={loading} />
            {registerErrors.country && <span className="error-message">{registerErrors.country}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="phone_number">Numéro de téléphone</label>
            <PhoneInput country={phoneCountryCode} value={phoneNumber} onChange={(value) => { setPhoneNumber(value); clearError('phone_number'); }} inputProps={{ name: 'phone_number', id: 'phone_number', disabled: loading, 'aria-invalid': Boolean(registerErrors.phone_number) }} enableSearch disableCountryCode={false} disableDropdown placeholder="+223 70 12 34 56" containerClass="phone-input-container" inputClass={registerErrors.phone_number ? 'error' : ''} />
            {registerErrors.phone_number && <span className="error-message">{registerErrors.phone_number}</span>}
          </div>
        </div>

        <div className="form-row auth-password-row">
          {passwordField('password', 'Mot de passe', 'register-password-error', { show: 'Afficher le mot de passe', hide: 'Masquer le mot de passe' })}
          {passwordField('confirm_password', 'Confirmer le mot de passe', 'register-confirm-password-error', { show: 'Afficher la confirmation', hide: 'Masquer la confirmation' })}
        </div>

        <button type="submit" className="auth-submit-btn" disabled={loading} aria-busy={loading}>
          {loading ? 'Création en cours…' : 'Créer mon compte'}
        </button>
      </form>

      <footer className="auth-footer">
        <p>Vous avez déjà un compte ? <Link to="/login" className="auth-link">Se connecter</Link></p>
      </footer>
    </AuthPageShell>
  );
};

export default Register;
