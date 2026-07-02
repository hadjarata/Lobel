import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateRegister } from '../../api/auth';
import Select from 'react-select';
import PhoneInput from 'react-phone-input-2/lib/lib';
import { parsePhoneNumberFromString } from 'libphonenumber-js';
import countryData from 'country-telephone-data';
import logo from '../../logo/LOBEL PROFIL 4.jpg.jpeg';
import 'react-phone-input-2/lib/style.css';
import './Auth.css';

const Register = () => {
  const navigate = useNavigate();
  const { register, loading } = useAuth();

  const [registerData, setRegisterData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });

  const [selectedCountry, setSelectedCountry] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [registerErrors, setRegisterErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  const countryOptions = useMemo(() => {
    const options = countryData.allCountries.map((item) => ({
      label: `${item.name} (+${item.dialCode})`,
      value: item.iso2.toUpperCase(),
      dialCode: item.dialCode,
    }));
    return options.sort((a, b) => a.label.localeCompare(b.label));
  }, []);

  useEffect(() => {
    const locale = navigator.language || navigator.userLanguage || 'FR';
    const detected = locale.split(/[-_]/)[1]?.toUpperCase() || 'FR';
    const defaultCountry = countryOptions.find((option) => option.value === detected)
      || countryOptions.find((option) => option.value === 'FR');
    setSelectedCountry(defaultCountry || countryOptions[0]);
  }, [countryOptions]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setRegisterData((prev) => ({ ...prev, [name]: value }));
    if (registerErrors[name]) {
      setRegisterErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (submitError) {
      setSubmitError('');
    }
  };

  const formatPhoneNumber = (rawValue) => {
    if (!rawValue) return '';
    const sanitized = rawValue.trim().startsWith('+') ? rawValue.trim() : `+${rawValue.trim()}`;
    const phone = parsePhoneNumberFromString(sanitized);
    return phone && phone.isValid() ? phone.format('E.164') : null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      ...registerData,
      country: selectedCountry?.value || '',
      phone_number: phoneNumber ? formatPhoneNumber(phoneNumber) : '',
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
      const response = await register(payload);
      if (response?.detail) {
        navigate('/login', { state: { message: response.detail } });
      }
    } catch (error) {
      setSubmitError(error.message || 'Erreur lors de l\'inscription');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card auth-card--wide">
        <div className="auth-logo">
          <img src={logo} alt="Lobel Store logo" />
        </div>

        <div className="auth-header">
          <h1>Inscription</h1>
          <p>Créez votre compte et profitez des offres.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {submitError && <div className="auth-error">{submitError}</div>}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">Prénom</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={registerData.first_name}
                onChange={handleChange}
                className={registerErrors.first_name ? 'error' : ''}
                placeholder="Jean"
                disabled={loading}
              />
              {registerErrors.first_name && (
                <span className="error-message">{registerErrors.first_name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Nom</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={registerData.last_name}
                onChange={handleChange}
                className={registerErrors.last_name ? 'error' : ''}
                placeholder="Dupont"
                disabled={loading}
              />
              {registerErrors.last_name && (
                <span className="error-message">{registerErrors.last_name}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={registerData.email}
              onChange={handleChange}
              className={registerErrors.email ? 'error' : ''}
              placeholder="votre@email.com"
              disabled={loading}
            />
            {registerErrors.email && (
              <span className="error-message">{registerErrors.email}</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="country">Pays</label>
              <Select
                inputId="country"
                instanceId="country"
                value={selectedCountry}
                options={countryOptions}
                onChange={(option) => {
                  setSelectedCountry(option);
                  if (registerErrors.country) {
                    setRegisterErrors((prev) => ({ ...prev, country: '' }));
                  }
                }}
                placeholder="Sélectionnez votre pays"
                isSearchable
                classNamePrefix="react-select"
                isDisabled={loading}
              />
              {registerErrors.country && (
                <span className="error-message">{registerErrors.country}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Numéro de téléphone</label>
              <PhoneInput
                country={selectedCountry?.value?.toLowerCase()}
                value={phoneNumber}
                onChange={(value) => {
                  setPhoneNumber(value);
                  if (registerErrors.phone_number) {
                    setRegisterErrors((prev) => ({ ...prev, phone_number: '' }));
                  }
                }}
                inputProps={{
                  name: 'phone_number',
                  id: 'phone_number',
                  disabled: loading,
                }}
                enableSearch
                disableCountryCode={false}
                disableDropdown
                placeholder="+33 6 12 34 56 78"
                containerClass="phone-input-container"
                inputClass={registerErrors.phone_number ? 'error' : ''}
              />
              {registerErrors.phone_number && (
                <span className="error-message">{registerErrors.phone_number}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              name="password"
              value={registerData.password}
              onChange={handleChange}
              className={registerErrors.password ? 'error' : ''}
              placeholder="•••••••"
              disabled={loading}
            />
            {registerErrors.password && (
              <span className="error-message">{registerErrors.password}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirm_password">Confirmer le mot de passe</label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              value={registerData.confirm_password}
              onChange={handleChange}
              className={registerErrors.confirm_password ? 'error' : ''}
              placeholder="•••••••"
              disabled={loading}
            />
            {registerErrors.confirm_password && (
              <span className="error-message">{registerErrors.confirm_password}</span>
            )}
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Inscription...' : 'Créer mon compte'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Vous avez déjà un compte ?{' '}
            <Link to="/login" className="auth-link">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
