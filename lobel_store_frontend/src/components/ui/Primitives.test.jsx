import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  Badge,
  Button,
  Card,
  Container,
  Input,
  Section,
  Select,
  Textarea,
} from './index';

afterEach(cleanup);

describe('Design System primitives', () => {
  it('renders an accessible form field with hint and error', () => {
    render(
      <Input
        label="Adresse e-mail"
        hint="Utilisée pour votre reçu"
        error="Adresse invalide"
      />,
    );

    const input = screen.getByLabelText('Adresse e-mail');
    expect(input).toHaveClass('ds-input');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAccessibleDescription(
      'Utilisée pour votre reçu Adresse invalide',
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Adresse invalide');
  });

  it('supports native textarea and select semantics', () => {
    render(
      <>
        <Textarea label="Message" defaultValue="Bonjour" />
        <Select label="Taille" defaultValue="m">
          <option value="s">S</option>
          <option value="m">M</option>
        </Select>
      </>,
    );

    expect(screen.getByLabelText('Message')).toHaveValue('Bonjour');
    expect(screen.getByLabelText('Taille')).toHaveValue('m');
  });

  it('disables a loading button and exposes its busy state', () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Commander</Button>);

    const button = screen.getByRole('button', { name: 'Chargement' });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders layout and status primitives without changing semantics', () => {
    render(
      <Section id="nouveautes" title="Nouveautés" subtitle="Cette semaine">
        <Container size="narrow">
          <Card as="article" elevated>
            <Badge variant="strong">Nouveau</Badge>
          </Card>
        </Container>
      </Section>,
    );

    expect(screen.getByRole('region', { name: 'Nouveautés' })).toBeInTheDocument();
    expect(screen.getByRole('article')).toHaveClass('ds-card--elevated');
    expect(screen.getByText('Nouveau')).toHaveClass('ds-badge--strong');
  });
});
