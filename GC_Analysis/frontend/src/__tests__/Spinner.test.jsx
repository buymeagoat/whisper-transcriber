import { render } from '@testing-library/react';
import Spinner from '../Spinner.jsx';
import '@testing-library/jest-dom';

test('renders Spinner component', () => {
  const { container } = render(<Spinner />);
  expect(container.firstChild).toBeInTheDocument();
});
