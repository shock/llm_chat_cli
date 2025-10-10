# Generate Phase Execution Plan

Phase number X = $ARGUMENTS

## CRITICAL RULES
- **USE SUB-AGENTS**: When executing the phase plan, use subagents as much as possible for discrete tasks.  Sub-agents are ideal for atomic operations like creating/modifying a code file, creating/modifying a test file, executing a test suite, debugging a test suite, etc.

## Overview

Your job is to execute the phase plan for phase X as efficiently as possible.  You want to conserve tokens, so keep your chatter to a minimum. Only state the most important status updates and keep all user updates brief.  Try to use a subagent for every step in the plan if possible.  If a sub-agent fails to perform a task, only then attempt it yourself.

## Instructions

1. read @admin/refactor-providers/action/phase_X_execution_plan.md and execute it.  use subagents whenever possible.
