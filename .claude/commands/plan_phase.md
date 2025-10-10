# Generate Phase Execution Plan

Phase number X = $ARGUMENTS

## Overview

Don't start implementing yet. For now, only write a detailed execution plan for implementing Phase X and save it as admin/refactor-providers/action/phase_X_execution_plan.md. The execution plan should contain a comprehensive summary of the work to be done and all of the relevant details from the masterplan document that have already been decided and any code samples or examples that have already been written. A developer should be able to read the phase execution plan along with the master plan and have all of the necessary information to implement the phase. It's crucial that the phase execution plan be complete and accurate and contain all of the necessary requirements for successful implementation. It's essential that the execution plan contain specific pytest test requirements for all code implemented in the phase.

## Instructions

1. DO NOT SEARCH THE CODEBASE YET
2. READ THE MASTER PLAN at admin/refactor-providers/master_plan.md
3. Write the phase execution plan at admin/refactor-providers/action/phase_X_execution_plan.md where X is the phase number and include the following sections:
    - Include an introduction section in the phase execution plan that provides a high-level overview of the phase and its purpose.  Indicate in the introduction section that if any steps cannot be completed, the execution should be aborted, the status document updated, and the user notified.

    **IMPORTANT**: The following steps are not steps for you to follow. They are steps for the executor to follow and should be captured in the phase execution plan.  Assume the executor has not performed any of your own instructions above.  DO NOT PERFORM ANY OF THE FOLLOWING STEPS NOW.  DOCUMENT THE FOLLOWING STEPS IN THE PHASE EXECUTION PLAN.

    Pre-Implementation Steps:
    - The first step of the phase execution plan should be to read the entire master plan document.
    - The next step of the phase execution plan should be to scan the /admin/refactor-providers/status directory to determine the current status of plan execution.  If a status document for phase X already exists, the executor should read it and use its contents to determine the current state of the phase execution plan to determine how to proceed with the remaining steps.
    - The next step of the phase execution plan should be to run the full test suite and make sure all tests pass. If they do not, stop and notify the user. Don't list specific number of tests to pass, just that they must all pass.
    - The next of phase execution plan should be to review the codebase and understand all relevant code files and modules as they currently exist.

    Implementation Steps:
    - The next section of the phase execution plan should detail how to fully implement the phase, including code modification requirements and unit test requirements. This section should be contain every single detail from the masterplan document related to the phase execution, including general guidelines from the masterplan that are not specific to a particular phase. This section should be broken down into ordered sub-steps, each with detailed, but concise instructions for modifying the codebase. Avoid redundancy.
      - When appropriate, instruct the executor to execute a step using a sub-agent via the `Task` tool.  If a task is to be delegated to a sub-agent, the instructions should provide the sub-agent with ALL of the necessary information to complete the step.  This is crucial for ensuring that the step is completed successfully because the sub-agent will not have visibility to the rest of the execution plan.  Only instruct the executor to execute a step using sub-agents for quantitatively discrete tasks that can be completed by a single agent and whose outcome can be easily and clearly interpreted by the executor.  sub-agents should prompted to output concise and comprehensive status reports to the executor as to the success or failure of their task.
      - NOTE: certain existing tests may be expected to fail if they are not updated, in which case they should be updated to test the new functionality. Other existing tests may be expected to fail if they fail due to the incompleteness of the master plan. These tests should be disabled until the master plan is complete.

    Post-Implementation Steps:
    - The final section of the phase execution plan should include the following conclusion steps:
        1. Instruct the executor to run the full test suite.
        2. Instruct the executor to create or update the admin/status/phase_X_execution_status.md file to reflect the current phase execution status, capturing a full status report on the existing state of the codebase with respect to the phase execution plan and test suite results.  The status document should be extremely concise and should not repeat information from the phase execution plan, but rather reference each step of the phase execution plan and its status ("COMPLETED", "IN PROGRESS", "NOT STARTED", or "NEEDS CLARIFICATION").  Provide an example of a status document in this section. The status document should end with one single overarching next step from the perspective of the executor.

## Result

- The final result of this (your) task should be an execution plan that is complete and accurate and contains all of the necessary requirements for successful implementation of Phase X.
