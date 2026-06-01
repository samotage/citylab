#!/usr/bin/env ruby
# frozen_string_literal: true

# Run with: ruby orch/test/test_agent_attribution.rb

require 'minitest/autorun'
require_relative '../agent_attribution'

class TestAgentAttribution < Minitest::Test
  def setup
    @saved_slug = ENV['OTL_AGENT_SLUG']
    @saved_id   = ENV['OTL_AGENT_ID']
  end

  def teardown
    ENV['OTL_AGENT_SLUG'] = @saved_slug
    ENV['OTL_AGENT_ID']   = @saved_id
  end

  def test_attributed_true_when_both_env_vars_set
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'
    assert AgentAttribution.attributed?
    assert_equal 'backend-con-5', AgentAttribution.agent_slug
    assert_equal '5', AgentAttribution.agent_id
  end

  def test_attributed_false_when_slug_missing
    ENV.delete('OTL_AGENT_SLUG')
    ENV['OTL_AGENT_ID'] = '5'
    refute AgentAttribution.attributed?
  end

  def test_attributed_false_when_id_missing
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV.delete('OTL_AGENT_ID')
    refute AgentAttribution.attributed?
  end

  def test_attributed_false_when_env_var_is_empty_string
    ENV['OTL_AGENT_SLUG'] = ''
    ENV['OTL_AGENT_ID']   = '5'
    refute AgentAttribution.attributed?
  end

  def test_commit_trailer_format
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'
    trailer = AgentAttribution.commit_trailer

    assert_includes trailer, "\nAgent: backend-con-5\n"
    assert_includes trailer, "Agent-Id: 5\n"
    assert_includes trailer, 'Co-Authored-By: Claude <noreply@anthropic.com>'
    assert trailer.start_with?("\n\n"),
           'trailer must start with TWO newlines: one to close body, one to make the blank-line separator git trailer parser requires'
  end

  def test_commit_trailer_is_recognised_by_git_interpret_trailers
    # Simulate the real call site: a body followed by the trailer.
    # `body.strip` mirrors how prebuild.rb / finalize.rb construct the message.
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'

    body = "feat(thing): subject line\n\nA body paragraph that explains the change.".strip
    full_message = body + AgentAttribution.commit_trailer

    parsed = IO.popen(['git', 'interpret-trailers', '--parse'], 'r+') do |io|
      io.write(full_message)
      io.close_write
      io.read
    end

    # `git interpret-trailers --parse` outputs ONLY the recognised trailers,
    # one per line. If the blank-line separator is missing, output is empty.
    assert_includes parsed, 'Agent: backend-con-5',
                    "git did not recognise Agent trailer; parsed output was: #{parsed.inspect}"
    assert_includes parsed, 'Agent-Id: 5',
                    "git did not recognise Agent-Id trailer; parsed output was: #{parsed.inspect}"
    assert_includes parsed, 'Co-Authored-By: Claude <noreply@anthropic.com>'
  end

  def test_commit_trailer_survives_pretty_trailers_extraction
    # The end-to-end audit query. If this passes, the trailer is also
    # discoverable via `git log --pretty='%(trailers:key=Agent)'`.
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'

    require 'tmpdir'
    require 'fileutils'

    Dir.mktmpdir('trailer-test-') do |dir|
      Dir.chdir(dir) do
        system('git init -q')
        system('git config user.email "test@test"')
        system('git config user.name "Test"')
        system('git config commit.gpgsign false')
        File.write('seed.txt', 'seed')
        system('git add seed.txt')

        body = 'feat(thing): subject\n\nbody paragraph.'.gsub('\\n', "\n").strip
        full_message = body + AgentAttribution.commit_trailer

        require 'tempfile'
        Tempfile.create('msg') do |f|
          f.write(full_message)
          f.close
          system("git commit -q -F #{f.path}")
        end

        agent_value = `git log -1 --pretty='%(trailers:key=Agent)'`.strip
        agent_id_value = `git log -1 --pretty='%(trailers:key=Agent-Id)'`.strip

        refute_empty agent_value,
                     '%(trailers:key=Agent) returned empty — trailer separator format is wrong'
        assert_includes agent_value, 'backend-con-5'
        refute_empty agent_id_value,
                     '%(trailers:key=Agent-Id) returned empty — trailer separator format is wrong'
        assert_includes agent_id_value, '5'
      end
    end
  end

  def test_commit_trailer_aborts_when_attribution_missing
    ENV.delete('OTL_AGENT_SLUG')
    ENV.delete('OTL_AGENT_ID')

    error = assert_raises(SystemExit) { capture_io { AgentAttribution.commit_trailer } }
    refute error.success?, 'process should exit non-zero when attribution missing'
  end

  def test_require_attribution_aborts_with_helpful_message
    ENV.delete('OTL_AGENT_SLUG')
    ENV.delete('OTL_AGENT_ID')

    _out, err = capture_io do
      assert_raises(SystemExit) { AgentAttribution.require_attribution!(context: 'orch:prepare') }
    end

    assert_includes err, 'orch:prepare'
    assert_includes err, 'OTL_AGENT_SLUG'
    assert_includes err, 'OTL_AGENT_ID'
    assert_includes err, 'lead session'
  end

  def test_require_attribution_passes_when_set
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'
    AgentAttribution.require_attribution!  # should not raise
  end

  def test_log_git_op_writes_to_stderr_with_attribution
    ENV['OTL_AGENT_SLUG'] = 'backend-con-5'
    ENV['OTL_AGENT_ID']   = '5'

    _out, err = capture_io { AgentAttribution.log_git_op('git checkout development') }
    assert_includes err, 'git checkout development'
    assert_includes err, 'agent: backend-con-5:5'
  end

  def test_log_git_op_handles_missing_attribution_gracefully
    # log_git_op should NOT abort — it's instrumentation, not enforcement.
    # Enforcement happens at require_attribution! / commit_trailer call sites.
    ENV.delete('OTL_AGENT_SLUG')
    ENV.delete('OTL_AGENT_ID')

    _out, err = capture_io { AgentAttribution.log_git_op('git status') }
    assert_includes err, '<no-slug>'
    assert_includes err, '<no-id>'
  end

  def test_attributed_commands_constant_includes_all_workflow_commands
    expected = %w[prepare proposal prebuild build test validate finalize]
    assert_equal expected.sort, AgentAttribution::ATTRIBUTED_COMMANDS.sort
  end
end
