import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Pagination from './Pagination';

afterEach(cleanup);

describe('catalog pagination', () => {
  it('is hidden for one page', () => {
    const { container } = render(<Pagination totalPages={1} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('marks the current page accessibly', () => {
    render(<Pagination currentPage={3} totalPages={5} />);
    expect(screen.getByRole('button', { name: '3' })).toHaveAttribute('aria-current', 'page');
  });

  it('disables previous on the first page', () => {
    render(<Pagination currentPage={1} totalPages={3} />);
    expect(screen.getByRole('button', { name: /précédente/i })).toBeDisabled();
  });

  it('disables next on the last page', () => {
    render(<Pagination currentPage={3} totalPages={3} />);
    expect(screen.getByRole('button', { name: /suivante/i })).toBeDisabled();
  });

  it('navigates to the next page', () => {
    const onChange = vi.fn();
    render(<Pagination currentPage={2} totalPages={4} onPageChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /suivante/i }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it('navigates directly to a numbered page', () => {
    const onChange = vi.fn();
    render(<Pagination currentPage={1} totalPages={8} onPageChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: '8' }));
    expect(onChange).toHaveBeenCalledWith(8);
  });
});
