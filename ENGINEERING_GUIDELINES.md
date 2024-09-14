# Engineering Guidelines

## Guidelines for LLM API Chat

- Prefer verbose variable names to make the code more readable.
- Always add news tests for new functionality.
- Prefer verbose code with comments over dense, cryptic code.
- Use descriptive function and variable names to improve code readability.

## Tests

- tests should be written using the pytest framework
- tests should be organized into separate files within the `tests` directory, one file per module
- tests should be named using the convention `test_<module_name>.py`

Tests that import classes from the `modules` directory should be placed in the `tests` directory, and should include the following code at the top of the test file:

```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

This ensures that the test can import the necessary classes from the `modules` directory.
