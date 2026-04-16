import React from 'react';
import { render, screen } from '@testing-library/react';

test('renders basic test container', () => {
  render(<div>frontend ready</div>);
  const element = screen.getByText(/frontend ready/i);
  expect(element).toBeInTheDocument();
});
