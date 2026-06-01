#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'fileutils'

# ProgressManager - Non-intrusive progress tracking for orchestration workers
#
# Workers report progress at milestones to orch/working/progress.yaml.
# The lead clears progress after each phase completes.
# The live status skill reads progress for display.
#
# Modelled on StateManager (orch/state_manager.rb).
#
class ProgressManager
  PROGRESS_FILE = File.expand_path('../working/progress.yaml', __FILE__)

  def initialize
    @progress = load_progress
  end

  # Update progress with current activity
  def update(phase:, step:, detail: nil, metrics: nil)
    now = Time.now.iso8601

    # Initialize history on first update or phase change
    if @progress['phase'] != phase
      @progress['history'] = []
      @progress['phase_started_at'] = now
    end

    # Append to history
    @progress['history'] ||= []
    @progress['history'] << { 'step' => step, 'at' => now }

    # Keep history bounded (last 20 entries)
    @progress['history'] = @progress['history'].last(20)

    @progress['phase'] = phase
    @progress['step'] = step
    @progress['detail'] = detail if detail
    @progress['updated_at'] = now
    @progress['phase_started_at'] ||= now

    if metrics
      @progress['metrics'] ||= {}
      @progress['metrics'].merge!(metrics)
    end

    save_progress
    @progress
  end

  # Clear progress (called by lead on phase completion)
  def clear
    return { 'cleared' => false, 'message' => 'No progress file' } unless File.exist?(PROGRESS_FILE)

    FileUtils.rm(PROGRESS_FILE)
    @progress = {}
    { 'cleared' => true }
  end

  # Return current progress hash
  def current
    return { 'active' => false, 'message' => 'No active worker progress' } unless File.exist?(PROGRESS_FILE)

    @progress.merge('active' => true)
  end

  private

  def load_progress
    return {} unless File.exist?(PROGRESS_FILE)

    YAML.safe_load(File.read(PROGRESS_FILE)) || {}
  rescue StandardError => e
    warn "Warning: Could not load progress file: #{e.message}"
    {}
  end

  def save_progress
    FileUtils.mkdir_p(File.dirname(PROGRESS_FILE))
    File.write(PROGRESS_FILE, @progress.to_yaml)
  end
end

# CLI interface when run directly
if __FILE__ == $PROGRAM_NAME
  require 'json'

  action = ARGV.shift
  options = {}

  # Parse CLI args
  while ARGV.any?
    arg = ARGV.shift
    if arg.start_with?('--')
      key = arg[2..].tr('-', '_')
      options[key] = ARGV.shift
    end
  end

  manager = ProgressManager.new

  result = case action
  when 'update'
    unless options['phase'] && options['step']
      puts "Error: --phase and --step are required"
      exit 1
    end

    metrics = options['metrics'] ? JSON.parse(options['metrics']) : nil

    manager.update(
      phase: options['phase'],
      step: options['step'],
      detail: options['detail'],
      metrics: metrics
    )

  when 'clear'
    manager.clear

  when 'show'
    manager.current

  else
    puts "Unknown action: #{action}"
    puts "Actions: update, clear, show"
    puts ""
    puts "Usage:"
    puts "  ruby orch/progress_manager.rb update --phase test --step running_tests --detail 'pytest -v' --metrics '{\"tests_passed\":12}'"
    puts "  ruby orch/progress_manager.rb clear"
    puts "  ruby orch/progress_manager.rb show"
    exit 1
  end

  puts result.to_yaml
end
