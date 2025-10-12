# Generate Phase Execution Plan

## Arguments

$EPIC = $1 (epic name)
Phase number X = $2 (phase number)

## CRITICAL RULES
- **USE SUB-AGENTS**: When executing the phase plan, use subagents as much as possible for discrete tasks.  Sub-agents are ideal for atomic operations like creating/modifying a code file, creating/modifying a test file, executing a test suite, debugging a test suite, etc.
- **RUN SUB-AGENTS SERIALLY**
- **DO NOT RUN TASKS IN PARALLEL**

## Overview

Your job is to execute the phase plan for phase X as efficiently as possible.  You want to conserve tokens, so keep your chatter to a minimum. Only state the most important status updates and keep all user updates brief.  Try to use a subagent for every step in the plan if possible.  If a sub-agent fails to perform a task, only then attempt it yourself.

## Instructions

1. read admin/$EPIC/action/phase_X_execution_plan.md and execute it.  use subagents whenever possible, but don't run tasks in parallel.
