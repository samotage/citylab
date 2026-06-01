#!/usr/bin/env ruby
# frozen_string_literal: true

# AgentAttribution - identifies which agent persona triggered an orch run
#
# Every orchestration workflow command (prepare, proposal, prebuild, build,
# test, validate, finalize) must run with OTL_AGENT_SLUG and OTL_AGENT_ID
# set in the environment. The lead session sets them; spawned workers
# inherit them automatically.
#
# Used to:
#   1. Hard-fail at boot if a workflow is started without attribution
#   2. Stamp every commit Ruby creates with Agent: / Agent-Id: trailers
#   3. Tag git operation log lines so the reflog can be cross-referenced
#
# Read-only orchestrator commands (state show, queue list, status, etc.)
# do NOT require attribution — operators may inspect state from any shell.

module AgentAttribution
  AGENT_SLUG_ENV = 'OTL_AGENT_SLUG'
  AGENT_ID_ENV   = 'OTL_AGENT_ID'

  # Workflow commands that mutate the repo and must carry attribution.
  # Read-only inspection commands are deliberately excluded.
  ATTRIBUTED_COMMANDS = %w[prepare proposal prebuild build test validate finalize].freeze

  module_function

  def agent_slug
    value = ENV[AGENT_SLUG_ENV]
    value.nil? || value.empty? ? nil : value
  end

  def agent_id
    value = ENV[AGENT_ID_ENV]
    value.nil? || value.empty? ? nil : value
  end

  def attributed?
    !agent_slug.nil? && !agent_id.nil?
  end

  # Aborts the process with a clear message if attribution is missing.
  # Call from workflow command boot paths and before any commit.
  def require_attribution!(context: 'orchestrator')
    missing = []
    missing << AGENT_SLUG_ENV if agent_slug.nil?
    missing << AGENT_ID_ENV   if agent_id.nil?
    return if missing.empty?

    abort <<~MSG
      [#{context}] Missing required environment variables: #{missing.join(', ')}

      Every orch workflow run must carry agent attribution so commits can be traced
      back to the persona that triggered them. Set both before invoking:

        export OTL_AGENT_SLUG=<persona-slug>     # e.g. backend-con-5
        export OTL_AGENT_ID=<persona-numeric-id> # e.g. 5

      The lead session (/otl:orch:20-start-queue-process) sets these once;
      spawned workers inherit them from the parent process automatically.
    MSG
  end

  # Standard commit trailer block. Prefixed with TWO newlines: one to close
  # the body's final line, one to leave the blank-line separator that git's
  # trailer parser requires. Without that blank line, `git log
  # --pretty='%(trailers)'` and `git interpret-trailers --parse` treat the
  # Agent: lines as body content and return nothing.
  #
  # Callers can safely concatenate this onto a body that ends without a
  # newline (e.g. `body.strip + commit_trailer`) — the leading `\n\n`
  # guarantees the separator exists.
  def commit_trailer
    require_attribution!(context: 'commit_trailer')
    "\n\nAgent: #{agent_slug}\n" \
      "Agent-Id: #{agent_id}\n" \
      "Co-Authored-By: Claude <noreply@anthropic.com>\n"
  end

  # Log line emitted before any direct git operation Ruby executes.
  # Goes to STDERR for terminal visibility; pair with OrchLogger calls
  # at the call site for the structured log file.
  def log_git_op(command)
    slug = agent_slug || '<no-slug>'
    id   = agent_id   || '<no-id>'
    Kernel.warn "[orch] #{command} (executed by orchestrator, agent: #{slug}:#{id})"
  end
end
