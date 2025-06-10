import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import GitSourceSelector from '../GitSourceSelector';
import { getRepositories, getDirectories, cloneGitLabRepo } from '../../services/api';

// Mock API functions
jest.mock('../../services/api');

describe('GitSourceSelector', () => {
  const mockOnCodeFetched = jest.fn();
  const mockSetLoading = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );
    expect(screen.getByText(/从代码仓库获取代码/i)).toBeInTheDocument();
  });

  it('switches between GitHub and GitLab', () => {
    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 检查默认是 GitHub
    expect(screen.getByLabelText(/github/i)).toBeChecked();

    // 切换到 GitLab
    fireEvent.click(screen.getByLabelText(/gitlab/i));
    expect(screen.getByLabelText(/gitlab/i)).toBeChecked();
    expect(screen.getByPlaceholderText(/gitlab仓库的完整url/i)).toBeInTheDocument();
  });

  it('shows error for empty token', async () => {
    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 点击加载按钮但没有输入令牌
    fireEvent.click(screen.getByText(/加载仓库/i));
    await waitFor(() => {
      expect(screen.getByText(/请输入访问令牌/i)).toBeInTheDocument();
    });
  });

  it('loads GitHub repositories successfully', async () => {
    const mockRepos = [
      { name: 'repo1', full_name: 'user/repo1', html_url: 'http://example.com/repo1' },
      { name: 'repo2', full_name: 'user/repo2', html_url: 'http://example.com/repo2' }
    ];

    getRepositories.mockResolvedValueOnce(mockRepos);

    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 输入令牌
    fireEvent.change(screen.getByPlaceholderText(/github访问令牌/i), {
      target: { value: 'test-token' }
    });

    // 点击加载按钮
    await act(async () => {
      fireEvent.click(screen.getByText(/加载仓库/i));
    });

    await waitFor(() => {
      expect(screen.getByText(/repo1/i)).toBeInTheDocument();
      expect(screen.getByText(/repo2/i)).toBeInTheDocument();
    });
  });

  it('handles GitLab repository cloning', async () => {
    const mockCloneResult = {
      success: true,
      clone_path: '/tmp/repo'
    };

    cloneGitLabRepo.mockResolvedValueOnce(mockCloneResult);

    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 切换到 GitLab
    fireEvent.click(screen.getByLabelText(/gitlab/i));

    // 输入令牌和仓库地址
    fireEvent.change(screen.getByPlaceholderText(/gitlab访问令牌/i), {
      target: { value: 'test-token' }
    });
    fireEvent.change(screen.getByPlaceholderText(/gitlab仓库的完整url/i), {
      target: { value: 'https://gitlab.com/user/repo.git' }
    });

    // 点击克隆按钮
    await act(async () => {
      fireEvent.click(screen.getByText(/克隆仓库/i));
    });

    await waitFor(() => {
      expect(cloneGitLabRepo).toHaveBeenCalledWith(
        'https://gitlab.com/user/repo.git',
        'test-token'
      );
    });
  });

  it('handles loading states correctly', async () => {
    getRepositories.mockImplementation(() => new Promise(resolve => setTimeout(() => {
      resolve([{ name: 'repo1', full_name: 'user/repo1' }]);
    }, 100)));

    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 输入令牌
    fireEvent.change(screen.getByPlaceholderText(/github访问令牌/i), {
      target: { value: 'test-token' }
    });

    // 点击加载按钮
    fireEvent.click(screen.getByText(/加载仓库/i));

    // 检查加载状态
    expect(screen.getByText(/正在加载仓库/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // 等待加载完成
    await waitFor(() => {
      expect(screen.queryByText(/正在加载仓库/i)).not.toBeInTheDocument();
    });
  });

  it('handles errors properly', async () => {
    getRepositories.mockRejectedValueOnce(new Error('API Error'));

    render(
      <GitSourceSelector
        onCodeFetched={mockOnCodeFetched}
        loading={false}
        setLoading={mockSetLoading}
      />
    );

    // 输入令牌
    fireEvent.change(screen.getByPlaceholderText(/github访问令牌/i), {
      target: { value: 'test-token' }
    });

    // 点击加载按钮
    await act(async () => {
      fireEvent.click(screen.getByText(/加载仓库/i));
    });

    // 检查错误消息
    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });
  });
});
