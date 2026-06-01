#!/usr/bin/env ruby
# frozen_string_literal: true

# Codebase invariant: no orch/commands/*.rb may surface a branch-op git
# command (checkout / switch / branch -D / branch <name>) as a `command`
# string in next_steps for the agent to execute. Branch ops are owned
# exclusively by Ruby; the deny rule on Bash(git checkout *) at the
# harness layer must never have to fire because the orchestration
# pipeline never even tries.
#
# This test guards against regressions: if a future change reintroduces
# `'command' => "git checkout ..."` etc., the test fails before the
# behaviour can leak to production.
#
# Run with: ruby orch/test/test_no_agent_runnable_branch_ops.rb

require 'minitest/autorun'

COMMANDS_DIR = File.expand_path('../commands', __dir__)
BRANCH_OP_PATTERN = /git\s+(checkout|switch|branch\s+-D|branch\s+[^\s\-])/

class TestNoAgentRunnableBranchOps < Minitest::Test
  def test_no_command_field_contains_branch_op
    offenders = []
    Dir.glob(File.join(COMMANDS_DIR, '*.rb')).each do |path|
      File.foreach(path).with_index(1) do |line, lineno|
        next unless line.include?("'command' =>") || line.include?('"command" =>')
        next unless line.match?(BRANCH_OP_PATTERN)
        offenders << "#{path}:#{lineno}: #{line.strip}"
      end
    end

    assert_empty offenders,
                 "branch-op command strings must not be surfaced to the agent. Found:\n#{offenders.join("\n")}"
  end

  def test_every_direct_branch_op_has_log_git_op_within_two_lines
    offenders = []
    Dir.glob(File.join(COMMANDS_DIR, '*.rb')).each do |path|
      lines = File.readlines(path)
      lines.each_with_index do |line, idx|
        # Match backtick branch ops: `git checkout ...`, `git switch ...`,
        # `git branch -D ...`, but exclude read-only `git branch --show-current`
        # and `git rev-parse --verify` style probes.
        next unless line =~ /`git\s+(checkout\s+\S|switch\s+\S|branch\s+-D)/

        # Look back up to 4 lines for AgentAttribution.log_git_op.
        window = lines[[idx - 4, 0].max..idx].join
        next if window.include?('AgentAttribution.log_git_op')

        offenders << "#{path}:#{idx + 1}: #{line.strip}"
      end
    end

    assert_empty offenders,
                 "direct branch ops must be tagged with AgentAttribution.log_git_op. Found untagged:\n#{offenders.join("\n")}"
  end

  def test_every_direct_git_commit_uses_tempfile_pattern
    # The `-m "..."` form does not preserve trailer newlines reliably and
    # makes attribution easy to forget. Direct commits must use `-F <file>`.
    offenders = []
    Dir.glob(File.join(COMMANDS_DIR, '*.rb')).each do |path|
      File.foreach(path).with_index(1) do |line, lineno|
        next unless line =~ /`git commit\s+-m\b/
        offenders << "#{path}:#{lineno}: #{line.strip}"
      end
    end

    assert_empty offenders,
                 "direct git commits must use `-F <tempfile>` (with AgentAttribution.commit_trailer), not `-m`. Found:\n#{offenders.join("\n")}"
  end
end
