import React from 'react';
import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Login from './Login';
import Register from './Register';

const auth = {
  login: vi.fn(),
  register: vi.fn(),
  loading: false,
};

vi.mock('../../context/authState', () => ({ useAuth: () => auth }));

vi.mock('react-select', () => ({
  default: ({ inputId, isDisabled }) => (
    <select id={inputId} disabled={isDisabled} defaultValue="FR">
      <option value="FR">France</option>
    </select>
  ),
}));

vi.mock('react-phone-input-2', () => ({
  default: ({ inputProps, value, onChange }) => (
    <input {...inputProps} value={value} onChange={(event) => onChange(event.target.value)} />
  ),
}));

const renderPage = (page, path) => render(
  <MemoryRouter initialEntries={[path]}>{page}</MemoryRouter>,
);

const fillLogin = () => {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'awa@example.com' } });
  fireEvent.change(screen.getByLabelText('Mot de passe'), { target: { value: 'MotDePasse12' } });
};

const fillRegister = async () => {
  await waitFor(() => expect(screen.getByLabelText('Pays')).toHaveValue('FR'));
  fireEvent.change(screen.getByLabelText('Prénom'), { target: { value: 'Awa' } });
  fireEvent.change(screen.getByLabelText('Nom'), { target: { value: 'Traoré' } });
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'awa@example.com' } });
  fireEvent.change(screen.getByLabelText('Mot de passe'), { target: { value: 'MotDePasse12' } });
  fireEvent.change(screen.getByLabelText('Confirmer le mot de passe'), { target: { value: 'MotDePasse12' } });
};

describe('Pages Connexion et Inscription', () => {
  beforeEach(() => {
    auth.loading = false;
    auth.login.mockReset().mockResolvedValue({});
    auth.register.mockReset().mockResolvedValue({});
  });
  afterEach(cleanup);

  it('valide puis soumet la connexion avec les valeurs attendues', async () => {
    renderPage(<Login />, '/login');
    fillLogin();
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    await waitFor(() => expect(auth.login).toHaveBeenCalledWith({
      email: 'awa@example.com', password: 'MotDePasse12',
    }));
  });

  it('affiche les erreurs de validation près des champs de connexion', async () => {
    renderPage(<Login />, '/login');
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByText("L'email est requis")).toBeInTheDocument();
    expect(screen.getByText('Mot de passe requis')).toBeInTheDocument();
    expect(auth.login).not.toHaveBeenCalled();
  });

  it('conserve les valeurs et annonce une erreur serveur de connexion', async () => {
    auth.login.mockRejectedValue(new Error('Compte momentanément indisponible'));
    renderPage(<Login />, '/login');
    fillLogin();
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Compte momentanément indisponible');
    expect(screen.getByLabelText('Email')).toHaveValue('awa@example.com');
  });

  it('soumet une inscription valide sans ajouter de champ', async () => {
    renderPage(<Register />, '/register');
    await fillRegister();
    fireEvent.click(screen.getByRole('button', { name: 'Créer mon compte' }));

    await waitFor(() => expect(auth.register).toHaveBeenCalledWith(expect.objectContaining({
      first_name: 'Awa', last_name: 'Traoré', email: 'awa@example.com', country: expect.any(String),
    })));
  });

  it('affiche les validations et une erreur serveur sans effacer la saisie', async () => {
    renderPage(<Register />, '/register');
    fireEvent.click(screen.getByRole('button', { name: 'Créer mon compte' }));
    expect(await screen.findByText(/prénom doit contenir/i)).toBeInTheDocument();
    expect(auth.register).not.toHaveBeenCalled();

    await fillRegister();
    auth.register.mockRejectedValue(new Error('Adresse email déjà utilisée'));
    fireEvent.click(screen.getByRole('button', { name: 'Créer mon compte' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Connexion au serveur impossible');
    expect(screen.getByLabelText('Email')).toHaveValue('awa@example.com');
  });

  it('désactive formulaires et actions pendant une soumission', () => {
    auth.loading = true;
    renderPage(<Login />, '/login');

    expect(screen.getByRole('button', { name: 'Connexion en cours…' })).toBeDisabled();
    expect(screen.getByLabelText('Email')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Afficher le mot de passe' })).toBeDisabled();
  });
});
