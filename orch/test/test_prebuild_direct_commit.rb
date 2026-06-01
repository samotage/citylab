#!/usr/bin/env ruby
# frozen_string_literal: true

# Integration tests for PrebuildCommand direct-commit behaviour.
# Run with: ruby orch/test/test_prebuild_direct_commit.rb

require 'minitest/autorun'
require 'tmpdir'
require 'fileutils'
require 'tempfile'
require 'yaml'

ENV['OTL_AGENT_SLUG'] ||= 'backend-con-5'
ENV['OTL_AGENT_ID']   ||= '5'

PREBUILD_RB = File.expand_path('../commands/prebuild.rb', __dir__)

class TestPrebuildDirectCommit < Minitest::Test
  def setup
    @tmpdir = Dir.mktmpdir('prebuild-test-')
    @change_name = 'sample-feature'
    @openspec_dir = File.join(@tmpdir, 'openspec', 'changes', @change_name)
    FileUtils.mkdir_p(@openspec_dir)
    File.write(File.join(@openspec_dir, 'proposal.md'), "# Sample feature\n")
    init_git_repo
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
      system('git add seed.txt && git commit -q -m "seed"')
    end
  end

  def run_prebuild(*extra_args)
    args = ['ruby', PREBUILD_RB, '--change-name', @change_name] + extra_args
    stdout = nil
    @last_stderr = ''
    Tempfile.create('prebuild-stderr') do |stderr_file|
      stderr_file.close
      Dir.chdir(@tmpdir) do
        stdout = `#{args.join(' ')} 2>#{stderr_file.path}`
      end
      @last_stderr = File.read(stderr_file.path)
    end
    YAML.safe_load(stdout, permitted_classes: [Time, Symbol], aliases: true)
  end

  def commit_message_at_head
    Dir.chdir(@tmpdir) { `git log -1 --format=%B`.strip }
  end

  def test_snapshot_committed_directly_with_attribution
    result = run_prebuild
    assert_equal 'success', result['status'], "expected success, errors: #{result['errors'].inspect}"
    assert result['data']['commit']['committed'], 'commit.committed must be true'
    refute_nil result['data']['commit']['sha']
    refute_empty result['data']['commit']['sha']

    msg = commit_message_at_head
    assert_includes msg, "chore(spec): #{@change_name} pre-build snapshot"
    assert_includes msg, 'Agent: backend-con-5'
    assert_includes msg, 'Agent-Id: 5'
    assert_includes msg, 'Co-Authored-By: Claude'
  end

  def test_no_executable_command_fields_for_stage_or_commit
    # Contract: agent should never see git add / git commit as commands to run.
    result = run_prebuild
    assert_equal 'success', result['status']

    next_steps = result['next_steps'] || []
    actions = next_steps.map { |s| s['action'] }
    assert_includes actions, 'snapshot_committed'
    refute_includes actions, 'stage_files', 'agent must not be asked to run stage_files'
    refute_includes actions, 'commit', 'agent must not be asked to run commit'

    next_steps.each do |step|
      next unless step['command']
      refute_match(/\bgit\s+add\b/, step['command'], "stage cmd leaked into next_steps: #{step.inspect}")
      refute_match(/\bgit\s+commit\b/, step['command'], "commit cmd leaked into next_steps: #{step.inspect}")
    end
  end

  def test_log_git_op_emits_attribution_for_stage_and_commit
    run_prebuild
    assert_includes @last_stderr, '[orch] git add', 'log_git_op should tag the stage'
    assert_includes @last_stderr, '[orch] git commit', 'log_git_op should tag the commit'
    assert_includes @last_stderr, 'agent: backend-con-5:5'
  end

  def test_missing_openspec_dir_returns_error_without_committing
    FileUtils.rm_rf(@openspec_dir)
    result = run_prebuild
    assert_equal 'error', result['status']
    assert(result['errors'].any? { |e| e['type'] == 'openspec_not_found' })
    head = Dir.chdir(@tmpdir) { `git log --oneline`.strip }
    assert_equal 1, head.lines.count, 'no commit should have been created'
  end

  def test_push_command_still_present_in_next_steps
    # Push stays as an agent-runnable step (per the contract — only checkout/
    # switch/branch-create are restricted; push is fine).
    result = run_prebuild
    push_step = result['next_steps'].find { |s| s['action'] == 'push' }
    refute_nil push_step
    assert_match(/\bgit\s+push\b/, push_step['command'])
  end

  def test_compact_step_remains_for_agent
    result = run_prebuild
    compact_step = result['next_steps'].find { |s| s['action'] == 'compact' }
    refute_nil compact_step
    assert_equal '/compact', compact_step['command']
  end
end
