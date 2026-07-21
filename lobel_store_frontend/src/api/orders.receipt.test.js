import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = { get: vi.fn() };
vi.mock('./axios', () => ({ default: api }));
vi.mock('./contracts/orders', () => ({
  adaptOrderDetail: vi.fn((value) => value),
  adaptOrderListItem: vi.fn((value) => value),
}));

const { downloadOrderReceipt } = await import('./orders');

describe('téléchargement du justificatif PDF', () => {
  beforeEach(() => vi.clearAllMocks());

  it('télécharge un Blob PDF depuis l’endpoint authentifié existant', async () => {
    const blob = new Blob(['%PDF'], { type: 'application/pdf' });
    api.get.mockResolvedValue({
      data: blob,
      headers: {
        'content-type': 'application/pdf',
        'content-disposition': 'attachment; filename="lobelstore-justificatif-LOBEL-RCPT-2026-000001.pdf"',
      },
    });

    await expect(downloadOrderReceipt(42)).resolves.toEqual({
      blob,
      filename: 'lobelstore-justificatif-LOBEL-RCPT-2026-000001.pdf',
    });
    expect(api.get).toHaveBeenCalledWith(
      '/api/orders/orders/42/receipt/',
      { responseType: 'blob' },
    );
  });

  it('refuse un type MIME qui n’est pas PDF', async () => {
    api.get.mockResolvedValue({
      data: new Blob(['html'], { type: 'text/html' }),
      headers: { 'content-type': 'text/html' },
    });
    await expect(downloadOrderReceipt(42)).rejects.toThrow(
      'invalid_receipt_content_type',
    );
  });

  it('ignore un nom de fichier dangereux', async () => {
    const blob = new Blob(['%PDF'], { type: 'application/pdf' });
    api.get.mockResolvedValue({
      data: blob,
      headers: {
        'content-type': 'application/pdf',
        'content-disposition': 'attachment; filename="../../secret.pdf"',
      },
    });
    await expect(downloadOrderReceipt(42)).resolves.toMatchObject({
      filename: 'lobelstore-justificatif-commande-42.pdf',
    });
  });
});
