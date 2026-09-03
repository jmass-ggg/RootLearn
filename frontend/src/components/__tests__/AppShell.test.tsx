import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import AppShell from '../AppShell';

const push = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
  usePathname: () => '/session/session-1',
  useSearchParams: () => new URLSearchParams('user_id=user-1'),
}));

describe('AppShell navigation', () => {
  beforeEach(() => {
    push.mockClear();
  });

  it('lets the learner open workspace sections from the sidebar', () => {
    const onSectionChange = vi.fn();
    render(
      <AppShell status="diagnosing" activeSection="diagnosis" onSectionChange={onSectionChange}>
        <p>Session content</p>
      </AppShell>
    );

    const overviewButtons = screen.getAllByRole('button', { name: 'Overview' });
    const mapButtons = screen.getAllByRole('button', { name: 'Knowledge Map' });
    const progressButtons = screen.getAllByRole('button', { name: 'Progress' });

    expect(overviewButtons[0]).toBeEnabled();
    expect(mapButtons[0]).toBeEnabled();
    expect(progressButtons[0]).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Root Gap' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'AI Tutor' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Session History' })).not.toBeInTheDocument();

    fireEvent.click(overviewButtons[0]);
    fireEvent.click(mapButtons[0]);
    fireEvent.click(progressButtons[0]);

    expect(onSectionChange).toHaveBeenNthCalledWith(1, 'overview');
    expect(onSectionChange).toHaveBeenNthCalledWith(2, 'knowledge-map');
    expect(onSectionChange).toHaveBeenNthCalledWith(3, 'progress');
  });

  it('routes nested session pages back to the selected workspace section', () => {
    render(
      <AppShell status="tutoring" activeSection="knowledge-map">
        <p>Root gap content</p>
      </AppShell>
    );

    fireEvent.click(screen.getAllByRole('button', { name: 'Overview' })[0]);
    fireEvent.click(screen.getAllByRole('button', { name: 'Progress' })[0]);

    expect(push).toHaveBeenNthCalledWith(1, '/');
    expect(push).toHaveBeenNthCalledWith(2, '/session/session-1?user_id=user-1&section=progress');
  });
});
