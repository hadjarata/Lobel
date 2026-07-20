import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AuthContext } from '../../context/authState';
import { AUTH_STATUS } from '../../auth/authConstants';
import PrivateRoute from './PrivateRoute';

const renderRoute = (status) => render(
  <AuthContext.Provider value={{ status }}>
    <MemoryRouter initialEntries={['/profile']}>
      <Routes>
        <Route path="/login" element={<div>Connexion</div>} />
        <Route path="/profile" element={<PrivateRoute><div>Profil privé</div></PrivateRoute>} />
      </Routes>
    </MemoryRouter>
  </AuthContext.Provider>,
);

describe('PrivateRoute', () => {
  it('affiche un loader pendant initialisation', () => {
    renderRoute(AUTH_STATUS.INITIALIZING);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByText('Profil privé')).not.toBeInTheDocument();
  });
  it('affiche la route authentifiée', () => {
    renderRoute(AUTH_STATUS.AUTHENTICATED);
    expect(screen.getByText('Profil privé')).toBeInTheDocument();
  });
  it('redirige une session anonyme', () => {
    renderRoute(AUTH_STATUS.ANONYMOUS);
    expect(screen.getByText('Connexion')).toBeInTheDocument();
  });
});
