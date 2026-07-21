import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import {
  downloadOrderReceipt, getOrderById,
} from '../../api/orders';
import OrderDetail from './OrderDetail';

vi.mock('../../api/orders', () => ({
  cancelOrder: vi.fn(),
  downloadOrderReceipt: vi.fn(),
  getOrderById: vi.fn(),
}));

const paidOrder = {
  id: 42,
  date_ordered: '2026-01-01T10:00:00Z',
  status: 'paid',
  timeline: [],
  items: [],
  delivery_recipient_name: 'Cliente',
  delivery_address: 'Adresse',
  delivery_method_label: 'Standard',
  subtotal_amount: '1000.00',
  shipping_amount: '0.00',
  discount_amount: '0.00',
  total_amount: '1000.00',
  currency: 'XOF',
  payment: { status: 'completed' },
  available_actions: {
    can_download_receipt: true,
    can_pay: false,
    can_cancel: false,
  },
};

const renderDetail = () => render(
  <MemoryRouter initialEntries={['/orders/42']}>
    <Routes>
      <Route path="/orders/:id" element={<OrderDetail />} />
    </Routes>
  </MemoryRouter>,
);

beforeEach(() => {
  getOrderById.mockResolvedValue(paidOrder);
  URL.createObjectURL = vi.fn(() => 'blob:receipt');
  URL.revokeObjectURL = vi.fn();
  HTMLAnchorElement.prototype.click = vi.fn();
});

afterEach(cleanup);

describe('justificatif PDF de commande', () => {
  it('affiche une action clavier uniquement lorsque le backend l’autorise', async () => {
    renderDetail();
    const button = await screen.findByRole('button', {
      name: 'Télécharger le justificatif PDF',
    });
    expect(button).toBeEnabled();

    cleanup();
    getOrderById.mockResolvedValueOnce({
      ...paidOrder,
      available_actions: {
        ...paidOrder.available_actions,
        can_download_receipt: false,
      },
    });
    renderDetail();
    await screen.findByRole('heading', { name: 'Commande #42' });
    expect(screen.queryByText('Télécharger le justificatif PDF')).toBeNull();
  });

  it('bloque le double clic, télécharge le Blob et révoque son URL', async () => {
    let resolveDownload;
    downloadOrderReceipt.mockReturnValueOnce(
      new Promise((resolve) => { resolveDownload = resolve; }),
    );
    renderDetail();
    const button = await screen.findByRole('button', {
      name: 'Télécharger le justificatif PDF',
    });
    fireEvent.click(button);
    fireEvent.click(button);
    expect(downloadOrderReceipt).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Téléchargement…' })).toBeDisabled();

    const blob = new Blob(['%PDF'], { type: 'application/pdf' });
    resolveDownload({ blob, filename: 'justificatif.pdf' });
    await waitFor(() => expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:receipt'));
    expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
  });

  it('affiche une erreur neutre si le téléchargement échoue', async () => {
    downloadOrderReceipt.mockRejectedValueOnce({ response: { status: 409 } });
    renderDetail();
    fireEvent.click(await screen.findByRole('button', {
      name: 'Télécharger le justificatif PDF',
    }));
    expect(await screen.findByText(
      'Le justificatif est temporairement indisponible.',
    )).toBeVisible();
  });
});
