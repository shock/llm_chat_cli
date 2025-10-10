# Phase execution plan

Phase number X = $ARGUMENTS

## Overview

Don't start implementing yet.  For now, only write a detailed execution plan for implementing Phase X and save it as admin/refactor-providers/action/phase_X_execution_plan.md.  The execution plan should contain a comprehensive summary of the work to be done and all of the relevant details from the masterplan document that have already been decided and any code samples or examples that have already been written.  A developer should be able to read the phase execution plan along with the master plan and have all of the necessary information to implement the phase.  It's crucial that the phase execution plan be complete and accurate and contain all of the necessary requirements for successful implementation.  It's essential that the execution plan contain specific pytest test requirements for all code implemented in the phase.

## Steps to follow

1. DO NOT SEARCH THE CODEBASE YET
2. READ THE MASTER PLAN at admin/refactor-providers/master_plan.md
4. Run the full test suite and make sure all tests pass.  If they do not, stop and notify the user.  DO NOT CONTINUE with these steps before consulting with the user.
5. Write the phase execution plan at admin/refactor-providers/action/phase_X_execution_plan.md where X is the phase number and include the following steps:
    1. The first step of the phase execution plan should be to read the entire master plan document.
    2. The second step of the phase execution plan should be to run the full test suite and make sure all tests pass.  If they do not, stop and notify the user.
    3. The next of phase execution plan should be to review the codebase and understand all relevant code files and modules as they currently exist.
    4. The next section of the phase execution plan should detail how to fully implement the phase, including code modification requirements and unit test requirements.  This section should be contain every single detail from the masterplan document related to the phase execution, including general guidelines from the masterplan that are not specific to a particular phase.  This section should be broken down into ordered sub-steps, each with detailed, but concise instructions for modifying the codebase.  Avoid redundancy.  NOTE: certain existing tests may be expected to fail if they are not updated, in which case they should be updated to test the new functionality.  Other existing tests may be expected to fail if they fail due to the incompleteness of the master plan.  These tests should be disabled until the master plan is complete.
    5. The final section of the phase execution plan should include the following conclusion steps:
        1. Run the full test suite.
        2. Create or update the admin/status/phase_X_execution_plan.md file to reflect the current phase execution status, capturing a full status report on the existing state of the codebase with respect to the phase execution plan and test suite results.

## Result

- The final result of this task should be an execution plan that is complete and accurate and contains all of the necessary requirements for successful implementation.
