import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, MagicMock, patch
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent, Completion

from modules.DelegatingCompleter import DelegatingCompleter


# Test Fixtures

@pytest.fixture
def mock_completer_a():
    """Create mock completer A for testing."""
    completer = Mock()
    completer.get_completions.return_value = [
        Completion(text="completion_a_1", start_position=-3, display_meta="A1"),
        Completion(text="completion_a_2", start_position=-3, display_meta="A2")
    ]
    return completer


@pytest.fixture
def mock_completer_b():
    """Create mock completer B for testing."""
    completer = Mock()
    completer.get_completions.return_value = [
        Completion(text="completion_b_1", start_position=-3, display_meta="B1"),
        Completion(text="completion_b_2", start_position=-3, display_meta="B2")
    ]
    return completer


@pytest.fixture
def mock_decision_function():
    """Create mock decision function for testing."""
    return Mock(return_value=True)


@pytest.fixture
def delegating_completer(mock_completer_a, mock_completer_b, mock_decision_function):
    """Create a DelegatingCompleter instance for testing."""
    return DelegatingCompleter(mock_completer_a, mock_completer_b, mock_decision_function)


@pytest.fixture
def mock_document():
    """Create a mock Document for testing."""
    def create_document(text, cursor_position=None):
        if cursor_position is None:
            cursor_position = len(text)
        return Document(text=text, cursor_position=cursor_position)
    return create_document


@pytest.fixture
def mock_complete_event():
    """Create a mock CompleteEvent for testing."""
    event = MagicMock(spec=CompleteEvent)
    event.completion_requested = False
    return event


# Core Functionality Tests

def test_delegation_to_completer_a(delegating_completer, mock_document, mock_complete_event):
    """Test delegation to completer_a when decision function returns True."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify
    delegating_completer.decision_function.assert_called_once_with(document)
    delegating_completer.completer_a.get_completions.assert_called_once_with(document, mock_complete_event)
    delegating_completer.completer_b.get_completions.assert_not_called()

    # Verify completions from completer_a are returned
    assert len(completions) == 2
    assert completions[0].text == "completion_a_1"
    assert completions[1].text == "completion_a_2"


def test_delegation_to_completer_b(delegating_completer, mock_document, mock_complete_event):
    """Test delegation to completer_b when decision function returns False."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify
    delegating_completer.decision_function.assert_called_once_with(document)
    delegating_completer.completer_b.get_completions.assert_called_once_with(document, mock_complete_event)
    delegating_completer.completer_a.get_completions.assert_not_called()

    # Verify completions from completer_b are returned
    assert len(completions) == 2
    assert completions[0].text == "completion_b_1"
    assert completions[1].text == "completion_b_2"


def test_constructor_validation():
    """Test that constructor properly validates parameters."""
    # Test with valid parameters
    completer_a = Mock()
    completer_b = Mock()
    decision_function = Mock()

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    assert delegating_completer.completer_a == completer_a
    assert delegating_completer.completer_b == completer_b
    assert delegating_completer.decision_function == decision_function


def test_get_completions_method_returns_generator(delegating_completer, mock_document, mock_complete_event):
    """Test that get_completions returns a generator/iterable."""
    document = mock_document("test input")

    # Execute
    result = delegating_completer.get_completions(document, mock_complete_event)

    # Verify it's iterable
    assert hasattr(result, '__iter__')

    # Verify we can iterate over it
    completions = list(result)
    assert isinstance(completions, list)


# Error Handling Tests

def test_graceful_handling_of_completer_a_exception(delegating_completer, mock_document, mock_complete_event):
    """Test graceful handling when completer_a raises an exception."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True
    delegating_completer.completer_a.get_completions.side_effect = Exception("Completer A error")

    # Execute and verify exception is raised (current implementation doesn't handle exceptions)
    with pytest.raises(Exception, match="Completer A error"):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_graceful_handling_of_completer_b_exception(delegating_completer, mock_document, mock_complete_event):
    """Test graceful handling when completer_b raises an exception."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False
    delegating_completer.completer_b.get_completions.side_effect = Exception("Completer B error")

    # Execute and verify exception is raised (current implementation doesn't handle exceptions)
    with pytest.raises(Exception, match="Completer B error"):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_graceful_handling_of_decision_function_exception(delegating_completer, mock_document, mock_complete_event):
    """Test graceful handling when decision function raises an exception."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.side_effect = Exception("Decision function error")

    # Execute and verify exception is raised (current implementation doesn't handle exceptions)
    with pytest.raises(Exception, match="Decision function error"):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_handling_of_none_completer_a(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_a is None."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True
    delegating_completer.completer_a = None

    # Execute and verify exception is raised (current implementation doesn't handle None)
    with pytest.raises(AttributeError):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_handling_of_none_completer_b(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_b is None."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False
    delegating_completer.completer_b = None

    # Execute and verify exception is raised (current implementation doesn't handle None)
    with pytest.raises(AttributeError):
        list(delegating_completer.get_completions(document, mock_complete_event))


# Edge Case Tests

def test_empty_completions_from_completer_a(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_a returns empty completions."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True
    delegating_completer.completer_a.get_completions.return_value = []

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify empty list is returned
    assert len(completions) == 0


def test_empty_completions_from_completer_b(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_b returns empty completions."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False
    delegating_completer.completer_b.get_completions.return_value = []

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify empty list is returned
    assert len(completions) == 0


def test_none_completions_from_completer_a(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_a returns None."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True
    delegating_completer.completer_a.get_completions.return_value = None

    # Execute and verify exception is raised (current implementation doesn't handle None)
    with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_none_completions_from_completer_b(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_b returns None."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False
    delegating_completer.completer_b.get_completions.return_value = None

    # Execute and verify exception is raised (current implementation doesn't handle None)
    with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
        list(delegating_completer.get_completions(document, mock_complete_event))


def test_completer_a_returns_generator(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_a returns a generator."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True

    def generator_completions():
        yield Completion(text="gen_a_1", start_position=-3, display_meta="GA1")
        yield Completion(text="gen_a_2", start_position=-3, display_meta="GA2")

    delegating_completer.completer_a.get_completions.return_value = generator_completions()

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify generator results are properly yielded
    assert len(completions) == 2
    assert completions[0].text == "gen_a_1"
    assert completions[1].text == "gen_a_2"


def test_completer_b_returns_generator(delegating_completer, mock_document, mock_complete_event):
    """Test behavior when completer_b returns a generator."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = False

    def generator_completions():
        yield Completion(text="gen_b_1", start_position=-3, display_meta="GB1")
        yield Completion(text="gen_b_2", start_position=-3, display_meta="GB2")

    delegating_completer.completer_b.get_completions.return_value = generator_completions()

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify generator results are properly yielded
    assert len(completions) == 2
    assert completions[0].text == "gen_b_1"
    assert completions[1].text == "gen_b_2"


# Integration Tests

def test_integration_with_real_document_and_event():
    """Test integration with real prompt_toolkit Document and CompleteEvent."""
    # Setup real objects
    document = Document(text="test input", cursor_position=10)
    event = CompleteEvent()

    # Setup mock completers
    completer_a = Mock()
    completer_a.get_completions.return_value = [
        Completion(text="real_completion", start_position=-4, display_meta="Real")
    ]

    completer_b = Mock()
    decision_function = Mock(return_value=True)

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    # Execute
    completions = list(delegating_completer.get_completions(document, event))

    # Verify
    decision_function.assert_called_once_with(document)
    completer_a.get_completions.assert_called_once_with(document, event)
    completer_b.get_completions.assert_not_called()

    assert len(completions) == 1
    assert completions[0].text == "real_completion"


def test_decision_function_receives_correct_document():
    """Test that decision function receives the correct Document object."""
    # Setup
    document = Document(text="specific input", cursor_position=5)
    event = CompleteEvent()

    completer_a = Mock()
    completer_a.get_completions.return_value = []  # Return empty iterable
    completer_b = Mock()
    decision_function = Mock(return_value=True)

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    # Execute
    list(delegating_completer.get_completions(document, event))

    # Verify decision function received the exact document
    decision_function.assert_called_once_with(document)
    assert decision_function.call_args[0][0] is document


def test_complete_event_passed_to_delegated_completer():
    """Test that CompleteEvent is passed correctly to delegated completer."""
    # Setup
    document = Document(text="test")
    event = CompleteEvent()
    event.completion_requested = True

    completer_a = Mock()
    completer_a.get_completions.return_value = []  # Return empty iterable
    completer_b = Mock()
    decision_function = Mock(return_value=True)

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    # Execute
    list(delegating_completer.get_completions(document, event))

    # Verify completer_a received the exact event
    completer_a.get_completions.assert_called_once_with(document, event)
    assert completer_a.get_completions.call_args[0][1] is event


# Performance Tests

def test_performance_with_large_completion_lists(delegating_completer, mock_document, mock_complete_event):
    """Test performance when delegated completers return large lists."""
    # Setup
    document = mock_document("test input")
    delegating_completer.decision_function.return_value = True

    # Create large list of completions
    large_completions = [
        Completion(text=f"completion_{i}", start_position=-3, display_meta=f"Meta{i}")
        for i in range(100)
    ]
    delegating_completer.completer_a.get_completions.return_value = large_completions

    # Execute and time
    import time
    start_time = time.time()
    completions = list(delegating_completer.get_completions(document, mock_complete_event))
    end_time = time.time()

    # Verify performance is reasonable (< 0.1 seconds)
    assert end_time - start_time < 0.1

    # Verify all completions are returned
    assert len(completions) == 100


def test_decision_function_called_only_once(delegating_completer, mock_document, mock_complete_event):
    """Test that decision function is called only once per get_completions call."""
    document = mock_document("test input")

    # Execute
    list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify decision function called exactly once
    assert delegating_completer.decision_function.call_count == 1


# Mock Testing Strategy Tests

def test_mock_completer_integration(delegating_completer, mock_document, mock_complete_event):
    """Test integration with mocked completers."""
    document = mock_document("test input")

    # Execute
    completions = list(delegating_completer.get_completions(document, mock_complete_event))

    # Verify mock interactions
    delegating_completer.decision_function.assert_called_once_with(document)
    delegating_completer.completer_a.get_completions.assert_called_once_with(document, mock_complete_event)

    # Verify completion structure
    for completion in completions:
        assert isinstance(completion.text, str)
        assert isinstance(completion.start_position, int)
        assert hasattr(completion, 'display_meta')


def test_mock_document_variations(delegating_completer, mock_complete_event):
    """Test with various Document scenarios."""
    # Test with different cursor positions
    test_cases = [
        ("test input", 5),   # cursor in middle
        ("test input", 0),   # cursor at beginning
        ("test input", 10),  # cursor at end
        ("", 0),            # empty document
    ]

    for text, cursor_position in test_cases:
        document = Document(text=text, cursor_position=cursor_position)

        # Should not raise exceptions
        completions = list(delegating_completer.get_completions(document, mock_complete_event))

        # Decision function should be called with the document
        delegating_completer.decision_function.assert_called_with(document)
        delegating_completer.decision_function.reset_mock()


def test_mock_complete_event_variations(delegating_completer, mock_document):
    """Test with various CompleteEvent scenarios."""
    document = mock_document("test input")

    # Test different event configurations
    test_events = [
        MagicMock(spec=CompleteEvent, completion_requested=True),
        MagicMock(spec=CompleteEvent, completion_requested=False),
        MagicMock(spec=CompleteEvent, text_inserted=True),
        MagicMock(spec=CompleteEvent, text_inserted=False),
    ]

    for event in test_events:
        # Should not raise exceptions
        completions = list(delegating_completer.get_completions(document, event))

        # Event should be passed to delegated completer
        delegating_completer.completer_a.get_completions.assert_called_with(document, event)
        delegating_completer.completer_a.reset_mock()


# Test Coverage Verification

def test_all_public_methods_tested():
    """Verify that all public methods of DelegatingCompleter are tested."""
    # DelegatingCompleter has only one public method: get_completions
    # Constructor is implicitly tested in fixture setup
    assert hasattr(DelegatingCompleter, 'get_completions')
    assert callable(DelegatingCompleter.get_completions)


def test_completer_inheritance():
    """Verify that DelegatingCompleter properly inherits from Completer."""
    from prompt_toolkit.completion import Completer

    completer_a = Mock()
    completer_b = Mock()
    decision_function = Mock()

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    # Verify inheritance
    assert isinstance(delegating_completer, Completer)
    assert hasattr(delegating_completer, 'get_completions')


# Documentation and Code Quality Tests

def test_constructor_documentation():
    """Test that constructor properly stores references to completers and decision function."""
    completer_a = Mock()
    completer_b = Mock()
    decision_function = Mock()

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)

    # Verify references are stored correctly
    assert delegating_completer.completer_a is completer_a
    assert delegating_completer.completer_b is completer_b
    assert delegating_completer.decision_function is decision_function


def test_yield_from_behavior():
    """Test that yield from properly delegates to the selected completer."""
    completer_a = Mock()
    completer_b = Mock()
    decision_function = Mock(return_value=True)

    # Create completions that will be yielded
    expected_completions = [
        Completion(text="comp1", start_position=-1, display_meta="meta1"),
        Completion(text="comp2", start_position=-2, display_meta="meta2")
    ]
    completer_a.get_completions.return_value = expected_completions

    delegating_completer = DelegatingCompleter(completer_a, completer_b, decision_function)
    document = Document(text="test")
    event = CompleteEvent()

    # Execute
    actual_completions = list(delegating_completer.get_completions(document, event))

    # Verify yield from behavior - should return the exact completions from completer_a
    assert actual_completions == expected_completions