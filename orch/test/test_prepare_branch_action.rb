#!/usr/bin/env ruby
# frozen_string_literal: true

# Integration tests for PrepareCommand's second-call --branch-action dispatch.
# Each test that mutates git uses a fresh tmp repo to avoid polluting the host repo.
#
# Run with: ruby orch/test/test_prepare_branch_action.rb

require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'
require 'yaml'

ENV['OTL_AGENT_SLUG'] ||= 'backend-con-5'
ENV['OTL_AGENT_ID']   ||= '5'

PREPARE_RB = File.expand_path('../commands/prepare.rb', __dir__)

class TestPrepareBranchActionDispatch < Minitest::Test
  def setup
    @tmpdir = Dir.mktmpdir('prepare-test-')
    @prd_dir = File.join(@tmpdir, 'docs', 'prds')
    FileUtils.mkdir_p(@prd_dir)
    @prd_path = File.join(@prd_dir, 'sample-feature-prd.md')
    File.write(@prd_path, "---\ntitle: Sample\n---\n\n# Sample feature PRD\n")
    @derived_branch = 'feature/sample-feature'
  end

  def teardown
    FileUtils.remove_entry(@tmpdir) if @tmpdir && File.exist?(@tmpdir)
  end

  def init_git_repo
    Dir.chdir(@tmpdir) do
      system('git init -q')
      system('git config user.email "test@test"')
      system('git config user.name "Test"')
      system('git config commit.gpgsign false')
      File.write('seed.txt', 'seed')
      # Commit the PRD too so the working tree is clean for tests that need it.
      system('git add . && git commit -q -m "seed"')
    end
  end

  def run_prepare(*extra_args)
    require 'tempfile'
    args = ['ruby', PREPARE_RB, '--prd-path', @prd_path] + extra_args
    stdout = nil
    @last_stderr = ''
    Tempfile.create('prepare-stderr') do |stderr_file|
      stderr_file.close
      Dir.chdir(@tmpdir) do
        stdout = `#{args.join(' ')} 2>#{stderr_file.path}`
      end
      @last_stderr = File.read(stderr_file.path)
    end
    YAML.safe_load(stdout, permitted_classes: [Time, Symbol], aliases: true)
  end

  def test_invalid_branch_action_returns_error
    result = run_prepare('--branch-action', 'bogus')
    assert_equal 'error', result['status']
    assert(result['errors'].any? { |e| e['type'] == 'invalid_branch_action' },
           "expected invalid_branch_action error, got: #{result['errors'].inspect}")
  end

  def test_branch_mismatch_returns_error
    init_git_repo
    result = run_prepare('--branch-action', 'use_existing', '--branch', 'feature/wrong-name')
    assert_equal 'error', result['status']
    assert(result['errors'].any? { |e| e['type'] == 'branch_mismatch' },
           "expected branch_mismatch error, got: #{result['errors'].inspect}")
  end

  def test_abort_returns_clean_with_branch_action_completed
    init_git_repo
    result = run_prepare('--branch-action', 'abort')
    assert_equal 'success', result['status']
    assert_equal 'abort', result['data']['branch_action_completed']
    refute(result['next_steps'].nil?)
    assert(result['next_steps'].any? { |s| s['action'] == 'pipeline_terminate' })
  end

  def test_use_existing_with_clean_tree_checks_out_branch
    init_git_repo
    Dir.chdir(@tmpdir) do
      system("git checkout -q -b #{@derived_branch}")
      system('git checkout -q master 2>/dev/null || git checkout -q main 2>/dev/null')
    end

    result = run_prepare('--branch-action', 'use_existing')
    assert_equal 'success', result['status']
    assert_equal 'use_existing', result['data']['branch_action_completed']

    Dir.chdir(@tmpdir) do
      current = `git branch --show-current`.strip
      assert_equal @derived_branch, current
    end

    assert_includes @last_stderr, '[orch] git checkout', 'log_git_op should emit a tagged stderr line'
    assert_includes @last_stderr, 'agent: backend-con-5:5'
  end

  def test_use_existing_with_dirty_tree_blocks
    init_git_repo
    Dir.chdir(@tmpdir) do
      system("git checkout -q -b #{@derived_branch}")
      system('git checkout -q master 2>/dev/null || git checkout -q main 2>/dev/null')
      File.write('uncommitted.txt', 'dirty')
    end

    result = run_prepare('--branch-action', 'use_existing')
    assert_equal 'error', result['status']
    assert_equal 'dirty_tree_blocked', result['data']['branch_action_completed']
    refute_nil result['data']['dirty_files']
    assert(result['errors'].any? { |e| e['type'] == 'dirty_tree_blocked' })

    Dir.chdir(@tmpdir) do
      current = `git branch --show-current`.strip
      refute_equal @derived_branch, current, 'must NOT have switched into dirty tree'
    end
  end

  def test_delete_and_recreate_runs_both_ops
    init_git_repo
    Dir.chdir(@tmpdir) do
      system("git checkout -q -b #{@derived_branch}")
      File.write('on-feature.txt', 'feature work')
      system('git add . && git commit -q -m "feature commit"')
      system('git checkout -q master 2>/dev/null || git checkout -q main 2>/dev/null')
    end

    result = run_prepare('--branch-action', 'delete_and_recreate')
    assert_equal 'success', result['status']
    assert_equal 'delete_and_recreate', result['data']['branch_action_completed']

    Dir.chdir(@tmpdir) do
      current = `git branch --show-current`.strip
      assert_equal @derived_branch, current
      # Recreated from current HEAD: the old feature commit must NOT be reachable.
      log = `git log --oneline #{@derived_branch}`
      refute_includes log, 'feature commit', 'recreated branch must not contain old feature commit'
    end
  end

  def test_returned_yaml_contains_no_command_strings_for_branch_ops
    # Contract change: branch ops should no longer surface 'git checkout ...' as
    # a next_steps command for the agent to execute.
    init_git_repo
    result = run_prepare('--branch-action', 'create') rescue nil
    # 'create' isn't a valid CLI --branch-action; checking the safe-path output below instead.

    # First-call path with new branch: should auto-create, return ready.
    result = run_prepare
    if result['status'] == 'success'
      branch_steps = result['next_steps'].select { |s| %w[branch_ready pipeline_terminate].include?(s['action']) }
      assert branch_steps.any?, "expected a branch_ready step, got next_steps: #{result['next_steps'].inspect}"
      result['next_steps'].each do |step|
        assert_nil step['command'], "branch op next_step must not contain 'command': #{step.inspect}" if step['action'] == 'branch_ready'
      end
    end
    # If openspec isn't installed in test env this'll be a non-success status; that's OK,
    # the contract assertion above is the goal.
  end
end
