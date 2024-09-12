# Engineering Guidelines

## Guidelines for LLM API Chat

- The script should be designed to be as simple and straightforward as possible, with a focus on usability and efficiency.
- The script should be optimized for speed and efficiency, minimizing any unnecessary delays or resource consumption.
- The script should be compatible with a wide range of operating systems, including Windows, macOS, and Linux.
- The script should be well-documented, with clear instructions and explanations of its functionality.
- The script should be designed to be easily customizable, allowing users to tailor its behavior to their specific needs.
- The script should be tested thoroughly, with a focus on ensuring its functionality and reliability.
- The script should be designed to be accessible to users with varying levels of technical expertise, providing a user-friendly interface.

## Tests

- tests should be written using the pytest framework
- tests should be organized into separate files within the `tests` directory
- tests should be named using the convention `test_<module_name>.py`

Tests that import classes from the `modules` directory should be placed in the `tests` directory, and should include the following code at the top of the test file:

```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

This ensures that the test can import the necessary classes from the `modules` directory.

## Coding Conventions

- Prefer verbose variable names to make the code more readable.
- Use descriptive function and variable names to improve code readability.
- Use comments to explain complex or non-obvious code.
- Use consistent indentation and formatting to improve code readability.
- Prefer verbose code with comments over dense, cryptic code.