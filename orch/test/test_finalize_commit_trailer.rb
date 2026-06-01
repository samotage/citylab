#!/usr/bin/env ruby
# frozen_string_literal: true

# Unit tests for FinalizeCommand's commit message construction with
# persona attribution. The full execute_commit_with_polling has a 15s
# fs-sync sleep and a polling loop that make end-to-end testing slow
# and brittle; the message-building logic is extracted into the helpers
# build_implementation_commit_message and implementation_commit_subject
# so they can be tested directly here. End-to-end behaviour is verified
# by the joint smoke test of a real orch pipeline run.
#
# Run with: ruby orch/test/test_finalize_commit_trailer.rb

require 'minitest/autorun'

ENV['OTL_AGENT_SLUG'] ||= 'backend-con-5'
ENV['OTL_AGENT_ID']   ||= '5'

require_relative '../commands/finalize'

class TestFinalizeCommitTrailer < Minitest::Test
  def setup
    @change_name = 'sample-feature'
    @cmd = FinalizeCommand.new(change_name: @change_name)
  end

  def test_subject_format
    assert_equal "feat(#{@change_name}): implementation complete",
                 @cmd.send(:implementation_commit_subject)
  end

  def test_message_includes_subject_line_first
    msg = @cmd.send(:build_implementation_commit_message)
    assert msg.start_with?("feat(#{@change_name}): implementation complete\n"),
           "subject line must be first line of commit message"
  end

  def test_message_includes_attribution_trailer
    msg = @cmd.send(:build_implementation_commit_message)
    assert_includes msg, "\nAgent: backend-con-5\n"
    assert_includes msg, "Agent-Id: 5\n"
    assert_includes msg, 'Co-Authored-By: Claude <noreply@anthropic.com>'
  end

  def test_message_describes_orchestration_origin
    msg = @cmd.send(:build_implementation_commit_message)
    assert_includes msg, 'Auto-committed by PRD orchestration system'
    assert_includes msg, "change #{@change_name}"
  end

  def test_message_aborts_when_attribution_missing
    saved_slug = ENV.delete('OTL_AGENT_SLUG')
    saved_id   = ENV.delete('OTL_AGENT_ID')

    error = assert_raises(SystemExit) do
      capture_io { @cmd.send(:build_implementation_commit_message) }
    end
    refute error.success?, 'commit-message construction must fail loudly without attribution'
  ensure
    ENV['OTL_AGENT_SLUG'] = saved_slug
    ENV['OTL_AGENT_ID']   = saved_id
  end

  def test_subject_picked_up_in_prepare_commit_metadata
    result = { 'data' => { 'commit_subject' => 'feat(other-name): implementation complete', 'commit_sha' => 'deadbeef' } }
    @cmd.send(:prepare_commit, result)
    assert_equal 'feat(other-name): implementation complete', result['data']['commit']['subject']
    assert_equal 'deadbeef', result['data']['commit']['sha']
    assert_nil result['data']['commit']['commands'], 'agent must not get commands for the implementation commit'
  end

  def test_prepare_commit_falls_back_to_default_subject_when_unset
    result = { 'data' => {} }
    @cmd.send(:prepare_commit, result)
    assert_equal "feat(#{@change_name}): implementation complete", result['data']['commit']['subject']
  end

  def test_finalize_source_logs_each_direct_git_op
    # Structural check: every direct git op in finalize.rb has an
    # accompanying AgentAttribution.log_git_op call so the audit trail
    # is preserved even when the polling pipeline is exercised in prod.
    src = File.read(File.expand_path('../commands/finalize.rb', __dir__))

    assert_match(/AgentAttribution\.log_git_op\(['"]git add -A['"]\)/, src,
                 'git add -A must be tagged via log_git_op')
    assert_match(/AgentAttribution\.log_git_op\(commit_cmd\)/, src,
                 'implementation commit must be tagged via log_git_op')
    assert_match(/AgentAttribution\.log_git_op\(['"]git checkout development['"]\)/, src,
                 'post-merge checkout must be tagged via log_git_op')
    assert_match(/AgentAttribution\.log_git_op\(['"]git pull --rebase origin development['"]\)/, src,
                 'post-merge pull must be tagged via log_git_op')
  end
end
