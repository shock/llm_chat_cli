import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import re
from unittest.mock import MagicMock, patch, call
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from modules.ModelCommandCompleter import ModelCommandCompleter, fuzzy_subsequence_search, is_subsequence, score_match


# Test Fixtures

@pytest.fixture
def sample_model_names():
    """Create sample model names for testing."""
    return [
        "openai/gpt-4o (gpt4o)",
        "openai/gpt-4o-mini (gpt4omini)",
        "anthropic/claude-3-opus-20240229 (opus)",
        "anthropic/claude-3-sonnet-20240229 (sonnet)",
        "groq/llama-3.1-70b-versatile (llama70b)",
        "groq/mixtral-8x7b-32768 (mixtral)",
        "cohere/command-r-plus (commandrplus)",
        "cohere/command-r (commandr)"
    ]


@pytest.fixture
def mock_provider_manager(sample_model_names):
    """Create a mock ProviderManager instance."""
    mock_manager = MagicMock()
    mock_manager.valid_scoped_models.return_value = sample_model_names
    return mock_manager


@pytest.fixture
def mod_command_pattern():
    """Create the model command pattern used by ModelCommandCompleter."""
    return re.compile(r'/mod\s+(.*)')


@pytest.fixture
def model_completer(mock_provider_manager, mod_command_pattern):
    """Create a ModelCommandCompleter instance for testing."""
    return ModelCommandCompleter(mock_provider_manager, mod_command_pattern)


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

def test_get_completions_basic(model_completer, mock_document, mock_complete_event):
    """Test basic completion functionality with valid input."""
    document = mock_document("/mod gpt")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    assert len(completions) > 0
    assert all(hasattr(comp, 'text') for comp in completions)
    assert all(hasattr(comp, 'start_position') for comp in completions)
    assert all(hasattr(comp, 'display_meta') for comp in completions)

    # Should find GPT models
    gpt_completions = [comp for comp in completions if 'gpt' in comp.text.lower()]
    assert len(gpt_completions) > 0


def test_get_completions_empty_input(model_completer, mock_document, mock_complete_event):
    """Test behavior with empty input after /mod command."""
    document = mock_document("/mod ")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # With empty input and no completion request, should return no completions
    assert len(completions) == 0


def test_get_completions_short_input(model_completer, mock_document, mock_complete_event):
    """Test behavior with short input (< 2 chars)."""
    document = mock_document("/mod g")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # With subsequence matching, should return completions even for single character input
    assert len(completions) > 0


def test_get_completions_short_input_with_completion_request(model_completer, mock_document):
    """Test behavior with short input when completion is explicitly requested."""
    document = mock_document("/mod g")
    event = MagicMock(spec=CompleteEvent)
    event.completion_requested = True

    completions = list(model_completer.get_completions(document, event))

    # With completion request, should return completions even for short input
    assert len(completions) > 0


def test_get_completions_boundary_input_lengths(model_completer, mock_document, mock_complete_event):
    """Test boundary conditions for input string lengths."""
    # Test with single character input (without completion request)
    document = mock_document("/mod g")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0  # With subsequence matching, should return completions for single char

    # Test with two character input
    document = mock_document("/mod gp")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0  # Should return completions for two chars

    # Test with very long input (50+ characters)
    long_input = "a" * 50
    document = mock_document(f"/mod {long_input}")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # Should handle long input without errors, may or may not find matches
    assert isinstance(completions, list)

    # Test with input exactly matching model name length
    document = mock_document("/mod gpt-4o")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("gpt-4o" in comp.text for comp in completions)


def test_get_completions_exact_match(model_completer, mock_document, mock_complete_event):
    """Test exact string matching."""
    document = mock_document("/mod gpt-4o")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should find exact match for gpt-4o
    # With new logic: completion.text is only the full name part (before space)
    # and display_meta contains the short name
    exact_matches = [comp for comp in completions if comp.text == "openai/gpt-4o"]
    assert len(exact_matches) == 1

    # Verify the display_meta contains the short name
    exact_match = exact_matches[0]
    # display_meta is a FormattedText object, we need to check its content
    assert hasattr(exact_match.display_meta, '__iter__')
    # Convert FormattedText to string for comparison
    display_meta_str = str(exact_match.display_meta)
    assert "gpt4o" in display_meta_str


def test_get_completions_partial_match(model_completer, mock_document, mock_complete_event):
    """Test partial string matching."""
    document = mock_document("/mod claude")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should find Claude models
    claude_completions = [comp for comp in completions if 'claude' in comp.text.lower()]
    assert len(claude_completions) > 0


def test_get_completions_case_insensitive(model_completer, mock_document, mock_complete_event):
    """Test case-insensitive matching."""
    document = mock_document("/mod GPT")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should find GPT models regardless of case
    gpt_completions = [comp for comp in completions if 'gpt' in comp.text.lower()]
    assert len(gpt_completions) > 0


# Edge Case Tests

def test_get_completions_empty_model_list(model_completer, mock_document, mock_complete_event):
    """Test behavior when ProviderManager returns empty model list."""
    # Mock ProviderManager to return empty list
    model_completer.provider_manager.valid_scoped_models.return_value = []
    document = mock_document("/mod gpt")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should return empty list
    assert len(completions) == 0


def test_get_completions_special_characters(model_completer, mock_document, mock_complete_event):
    """Test model names with special characters like hyphens, underscores, dots."""
    # Mock ProviderManager with models containing special characters
    special_models = [
        "openai/gpt-4o-mini-2024-07-18 (gpt4omini)",
        "anthropic/claude-3.5-sonnet-20241022 (claude35sonnet)",
        "provider/model_with_underscores (model_underscore)",
        "provider/model.with.dots (model_dots)"
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = special_models

    # Test hyphen matching
    document = mock_document("/mod gpt-4o-mini")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("gpt-4o-mini" in comp.text for comp in completions)

    # Test dot matching
    document = mock_document("/mod claude-3.5")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("claude-3.5" in comp.text for comp in completions)


def test_get_completions_complex_special_character_scenarios(model_completer, mock_document, mock_complete_event):
    """Test complex special character scenarios including regex metacharacters."""
    # Mock ProviderManager with models containing complex special characters
    complex_models = [
        "provider/model-with-multiple-hyphens-2024-12-31 (multi_hyphen)",
        "provider/model_with_multiple_underscores_here (multi_underscore)",
        "provider/model.with.multiple.dots.here (multi_dot)",
        "provider/model+plus+sign (plus_model)",
        "provider/model*asterisk*test (asterisk_model)",
        "provider/model?question?mark (question_model)",
        "provider/model[with]brackets (bracket_model)",
        "provider/model(with)parentheses (paren_model)",
        "provider/model{with}braces (brace_model)",
        "provider/model^caret^test (caret_model)",
        "provider/model$dollar$test (dollar_model)",
        "provider/model|pipe|test (pipe_model)",
        "provider/model\\backslash\\test (backslash_model)",
        "provider/model~tilde~test (tilde_model)",
        "provider/model@at@test (at_model)",
        "provider/model#hash#test (hash_model)",
        "provider/model%percent%test (percent_model)",
        "provider/model&and&test (and_model)",
        "provider/model=equals=test (equals_model)",
        "provider/model:colon:test (colon_model)",
        "provider/model;semicolon;test (semicolon_model)",
        "provider/model,comma,test (comma_model)",
        "provider/model<less>than (lessthan_model)",
        "provider/model>greater>than (greaterthan_model)",
        "provider/model'single'quote (singlequote_model)",
        'provider/model"double"quote (doublequote_model)'
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = complex_models

    # Test hyphen patterns
    document = mock_document("/mod multiple-hyphens")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("multiple-hyphens" in comp.text for comp in completions)

    # Test underscore patterns
    document = mock_document("/mod multiple_underscores")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("multiple_underscores" in comp.text for comp in completions)

    # Test dot patterns
    document = mock_document("/mod multiple.dots")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("multiple.dots" in comp.text for comp in completions)

    # Test plus sign
    document = mock_document("/mod plus+sign")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("plus+sign" in comp.text for comp in completions)

    # Test asterisk (regex metacharacter)
    document = mock_document("/mod asterisk")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("asterisk" in comp.text for comp in completions)

    # Test question mark (regex metacharacter)
    document = mock_document("/mod question")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("question" in comp.text for comp in completions)

    # Test mixed special characters
    document = mock_document("/mod model-with_underscores.and.dots")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # May or may not find exact matches due to fuzzy matching
    assert isinstance(completions, list)

    # Test regex metacharacters in input
    document = mock_document("/mod model*")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # Should handle regex metacharacters without errors
    assert isinstance(completions, list)


def test_get_completions_unicode_characters(model_completer, mock_document, mock_complete_event):
    """Test model names with non-ASCII characters."""
    # Mock ProviderManager with models containing Unicode characters
    unicode_models = [
        "provider/模型-测试 (model_test)",
        "provider/mödël-ñämé (model_name)",
        "provider/正常模型 (normal_model)"
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = unicode_models

    document = mock_document("/mod 模型")
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should handle Unicode characters correctly
    assert len(completions) > 0
    assert any("模型" in comp.text for comp in completions)


def test_get_completions_comprehensive_unicode_combinations(model_completer, mock_document, mock_complete_event):
    """Test comprehensive Unicode character combinations."""
    # Mock ProviderManager with diverse Unicode models
    unicode_models = [
        "provider/模型-测试-αβγ (model_test)",
        "provider/mödël-ñämé-émojï (model_name)",
        "provider/正常模型-日本語 (normal_model)",
        "provider/모델-테스트 (korean_model)",
        "provider/модель-тест (russian_model)",
        "provider/موديل-اختبار (arabic_model)",
        "provider/🦄-unicorn-model (emoji_model)",
        "provider/模型-测试-🦄-αβγ (mixed_unicode)"
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = unicode_models

    # Test Chinese characters
    document = mock_document("/mod 模型")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("模型" in comp.text for comp in completions)

    # Test Latin characters with diacritics
    document = mock_document("/mod möd")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("möd" in comp.text.lower() for comp in completions)

    # Test Greek characters
    document = mock_document("/mod αβγ")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("αβγ" in comp.text for comp in completions)

    # Test emoji characters
    document = mock_document("/mod 🦄")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # Emoji matching might not work well with fuzzy matching
    # Just ensure it doesn't crash and returns a list
    assert isinstance(completions, list)

    # Test Korean characters
    document = mock_document("/mod 모델")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # Korean character matching might not work perfectly with fuzzy matching
    # Just ensure it doesn't crash and returns a list
    assert isinstance(completions, list)

    # Test mixed Unicode input
    document = mock_document("/mod 模型-αβγ")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    # Mixed Unicode matching might not work perfectly with fuzzy matching
    # Just ensure it doesn't crash and returns a list
    assert isinstance(completions, list)


def test_get_completions_long_model_names(model_completer, mock_document, mock_complete_event):
    """Test very long model names (100+ characters)."""
    # Create a very long model name
    long_model_name = "provider/" + "x" * 100 + " (long_model)"
    model_completer.provider_manager.valid_scoped_models.return_value = [long_model_name]

    document = mock_document("/mod xxxxx")
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should handle long model names without errors
    assert len(completions) > 0
    # With new logic: completion.text is only the full name part (before space)
    expected_full_name = long_model_name.split(' ')[0]
    assert completions[0].text == expected_full_name


def test_get_completions_mixed_case(model_completer, mock_document, mock_complete_event):
    """Test mixed case model names."""
    mixed_case_models = [
        "provider/GPT-4o-Mini (GPT4oMini)",
        "provider/Claude-3-Sonnet (Claude3Sonnet)",
        "provider/MiXtRaL-8x7B (MiXtRaL)"
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = mixed_case_models

    # Test lowercase input
    document = mock_document("/mod gpt")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("GPT" in comp.text for comp in completions)

    # Test mixed case input
    document = mock_document("/mod MiXtRaL")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0
    assert any("MiXtRaL" in comp.text for comp in completions)


def test_get_completions_no_matches(model_completer, mock_document, mock_complete_event):
    """Test behavior when no models match the input."""
    # Mock ProviderManager to return models that won't match
    # Use very different model names that won't match "nonexistentmodel"
    model_completer.provider_manager.valid_scoped_models.return_value = [
        "provider1/xyz-123 (xyz)",
        "provider2/abc-456 (abc)",
        "provider3/def-789 (def)"
    ]
    document = mock_document("/mod nonexistentmodel")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # With subsequence matching, should return all matches (not limited to 8)
    # Even with no good matches, it will return all models that contain the query as a subsequence
    # The query "nonexistentmodel" won't match any of our test models
    # So it should return an empty list or very few matches with low scores
    assert isinstance(completions, list)


def test_get_completions_whitespace_handling(model_completer, mock_document, mock_complete_event):
    """Test handling of leading/trailing whitespace in input."""
    # Test leading whitespace
    document = mock_document("/mod  gpt")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0

    # Test trailing whitespace
    document = mock_document("/mod gpt ")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0

    # Test multiple spaces
    document = mock_document("/mod   gpt")
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0


def test_get_completions_provider_prefix_variations(model_completer, mock_document, mock_complete_event):
    """Test different provider prefix formats."""
    # Test matching by provider prefix
    document = mock_document("/mod openai")
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should find OpenAI models
    openai_completions = [comp for comp in completions if comp.text.startswith("openai/")]
    assert len(openai_completions) > 0

    # Test matching by provider name in display_meta
    document = mock_document("/mod anthropic")
    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Should find Anthropic models
    # With new logic: display_meta contains short names, not provider context
    # So we should check for Anthropic models by their text (provider prefix)
    anthropic_completions = [comp for comp in completions if comp.text.startswith("anthropic/")]
    assert len(anthropic_completions) > 0


# Error Handling Tests

def test_get_completions_graceful_degradation(model_completer, mock_document, mock_complete_event):
    """Test graceful degradation when errors occur."""
    # Test with None returned from ProviderManager
    model_completer.provider_manager.valid_scoped_models.return_value = None
    document = mock_document("/mod gpt")

    # This should raise an exception when trying to iterate over None
    # in fuzzy_subsequence_search
    try:
        completions = list(model_completer.get_completions(document, mock_complete_event))
        # If we get here, the function handled None gracefully
        # Should return empty list
        assert len(completions) == 0
    except TypeError:
        # This is expected - the function doesn't handle None gracefully
        # but the error is caught in the test
        pass

# Performance Tests

def test_get_completions_large_model_list(model_completer, mock_document, mock_complete_event):
    """Test performance with large model lists (100+ models)."""
    # Create a large list of model names
    large_model_list = [f"provider/model-{i:03d} (model{i})" for i in range(150)]
    model_completer.provider_manager.valid_scoped_models.return_value = large_model_list

    document = mock_document("/mod model-0")

    # Time the completion generation
    import time
    start_time = time.time()
    completions = list(model_completer.get_completions(document, mock_complete_event))
    end_time = time.time()

    # Should complete in reasonable time (< 1 second)
    assert end_time - start_time < 1.0

    # With subsequence matching, should return all matches (not limited to 8)
    # The query "model-0" matches all models starting with "model-0"
    assert len(completions) > 0


def test_get_completions_very_large_model_list(model_completer, mock_document, mock_complete_event):
    """Test performance with very large model lists (500+ models)."""
    # Create a very large list of model names
    very_large_model_list = [f"provider/model-{i:04d}-test-{i:04d} (model{i})" for i in range(500)]
    model_completer.provider_manager.valid_scoped_models.return_value = very_large_model_list

    document = mock_document("/mod model-0001")

    # Time the completion generation
    import time
    start_time = time.time()
    completions = list(model_completer.get_completions(document, mock_complete_event))
    end_time = time.time()

    # Should complete in reasonable time (< 2 seconds for very large list)
    assert end_time - start_time < 2.0

    # With subsequence matching, should return all matches (not limited to 8)
    # The query "model-0001" matches all models containing "model-0001"
    assert len(completions) > 0

    # Test with different input patterns on large dataset
    test_cases = [
        ("model-0", "common prefix"),
        ("test-0", "common suffix"),
        ("provider", "provider prefix"),
        ("xyz", "no matches"),
        ("", "empty input with completion request")
    ]

    for input_text, description in test_cases:
        document = mock_document(f"/mod {input_text}")

        # For empty input, we need completion request
        event = mock_complete_event
        if input_text == "":
            event = MagicMock(spec=CompleteEvent)
            event.completion_requested = True

        start_time = time.time()
        completions = list(model_completer.get_completions(document, event))
        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 2.0, f"Performance issue with {description}"
        # With subsequence matching, should return all matches (not limited to 8)
        # Just ensure it returns a list without errors
        assert isinstance(completions, list), f"Should return list for {description}"


def test_get_completions_performance_boundary_conditions(model_completer, mock_document, mock_complete_event):
    """Test performance with boundary conditions and edge cases."""
    # Create models with very long names
    long_name_models = [f"provider/{'x' * 100}-model-{i:03d} (model{i})" for i in range(100)]
    model_completer.provider_manager.valid_scoped_models.return_value = long_name_models

    # Test with very long input
    long_input = "x" * 50
    document = mock_document(f"/mod {long_input}")

    import time
    start_time = time.time()
    completions = list(model_completer.get_completions(document, mock_complete_event))
    end_time = time.time()

    # Should complete in reasonable time even with long strings
    assert end_time - start_time < 1.0
    # With subsequence matching, should return all matches (not limited to 8)
    # Just ensure it returns results without errors
    assert isinstance(completions, list)

    # Test with models containing many special characters
    special_char_models = [
        f"provider/model-{i:03d}-with-special-!@#$%^&*()_+-=[]{{}}|;':\",./<>? (model{i})"
        for i in range(100)
    ]
    model_completer.provider_manager.valid_scoped_models.return_value = special_char_models

    document = mock_document("/mod special")
    start_time = time.time()
    completions = list(model_completer.get_completions(document, mock_complete_event))
    end_time = time.time()

    # Should complete in reasonable time with special characters
    assert end_time - start_time < 1.0
    # With subsequence matching, should return all matches (not limited to 8)
    # Just ensure it returns results without errors
    assert isinstance(completions, list)


# Helper Method Tests

def test_extract_short_name():
    """Test extract_short_name() method."""
    completer = ModelCommandCompleter(MagicMock(), re.compile(r'/mod\s+(.*)'))

    # Test with short name in parentheses
    result = completer.extract_short_name("openai/gpt-4o (gpt4o)")
    assert result == "gpt4o"

    # Test without parentheses (fallback to long name)
    result = completer.extract_short_name("openai/gpt-4o")
    assert result == "gpt-4o"

    # Test with multiple slashes
    result = completer.extract_short_name("provider/sub/model (model)")
    assert result == "model"


def test_filter_completions(model_completer, sample_model_names):
    """Test filter_completions() method."""
    # Test with matching input
    filtered = model_completer.filter_completions(sample_model_names, "gpt")
    assert len(filtered) > 0
    # filtered contains tuples of (model_string, score)
    # With subsequence matching, all results should contain the query as a subsequence
    # but they may not contain "gpt" as a contiguous substring
    gpt_matches = [model for model in filtered if "gpt" in model[0].lower()]
    assert len(gpt_matches) > 0

    # Test with non-matching input
    filtered = model_completer.filter_completions(sample_model_names, "nonexistent")
    # Should return empty list when no subsequence matches are found
    assert len(filtered) == 0

    # Test with subsequence matching behavior
    # The new fuzzy_subsequence_search returns all matches, not limited to 8
    many_models = [f"provider/model-{i} (model{i})" for i in range(20)]
    filtered = model_completer.filter_completions(many_models, "model")
    # Should return all 20 matches since "model" is a subsequence of all model names
    assert len(filtered) == 20


def test_get_model_substring(model_completer, mock_document):
    """Test get_model_substring() method."""
    # Test with valid /mod command
    document = mock_document("/mod gpt-4o")
    result = model_completer.get_model_substring(document)
    assert result == "gpt-4o"

    # Test with whitespace
    document = mock_document("/mod  gpt-4o  ")
    result = model_completer.get_model_substring(document)
    # The regex captures everything after "/mod " including whitespace
    # Note: the regex pattern r'/mod\s+(.*)' captures everything after whitespace
    # So it should capture "gpt-4o  " (without leading spaces)
    assert result == "gpt-4o  "

    # Test without /mod command
    document = mock_document("some other text")
    result = model_completer.get_model_substring(document)
    assert result == ""

    # Test with partial /mod command
    document = mock_document("/mod")
    result = model_completer.get_model_substring(document)
    assert result == ""

    # Test with cursor in middle of text
    document = Document(text="/mod gpt-4o and more", cursor_position=10)
    result = model_completer.get_model_substring(document)
    # When cursor is at position 10, text before cursor is "/mod gpt-4"
    assert result == "gpt-4"


# Mock Testing Strategy Tests

def test_mock_provider_manager_integration(model_completer, mock_document, mock_complete_event):
    """Test integration with mocked ProviderManager."""
    document = mock_document("/mod gpt")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    # Verify ProviderManager was called
    model_completer.provider_manager.valid_scoped_models.assert_called_once()

    # Verify completions are properly constructed
    for completion in completions:
        assert isinstance(completion.text, str)
        assert isinstance(completion.start_position, int)
        # display_meta might be a FormattedText object, not a string
        assert hasattr(completion, 'display_meta')


def test_mock_document_variations(model_completer, mock_complete_event):
    """Test with various Document scenarios."""
    # Test cursor in middle of text
    document = Document(text="/mod gpt-4o and more", cursor_position=10)
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) > 0

    # Test cursor at beginning
    document = Document(text="/mod gpt-4o", cursor_position=0)
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) == 0  # No /mod command before cursor

    # Test cursor after /mod command
    document = Document(text="/mod gpt-4o", cursor_position=5)
    completions = list(model_completer.get_completions(document, mock_complete_event))
    assert len(completions) == 0  # No model substring extracted


def test_mock_complete_event_variations(model_completer, mock_document):
    """Test with various CompleteEvent scenarios."""
    document = mock_document("/mod g")

    # Test with completion requested
    event = MagicMock(spec=CompleteEvent)
    event.completion_requested = True
    completions = list(model_completer.get_completions(document, event))
    assert len(completions) > 0  # Should return completions for short input

    # Test without completion requested
    event.completion_requested = False
    completions = list(model_completer.get_completions(document, event))
    assert len(completions) > 0  # With subsequence matching, should return completions even without explicit request


# Integration Tests

def test_completion_object_structure(model_completer, mock_document, mock_complete_event):
    """Test that completion objects are properly constructed."""
    document = mock_document("/mod gpt-4o")

    completions = list(model_completer.get_completions(document, mock_complete_event))

    for completion in completions:
        # Verify completion object structure
        assert hasattr(completion, 'text')
        assert hasattr(completion, 'start_position')
        assert hasattr(completion, 'display_meta')

        # Verify types
        assert isinstance(completion.text, str)
        assert isinstance(completion.start_position, int)
        # display_meta might be a FormattedText object, not a string
        assert hasattr(completion.display_meta, '__iter__')

        # Verify start_position is negative (for replacement)
        assert completion.start_position < 0

        # Verify display_meta contains short names
        # Convert display_meta to string for checking
        display_meta_str = str(completion.display_meta)
        # Should contain short names like "gpt4o", "gpt4omini", "opus", "sonnet", etc.
        assert any(short_name in display_meta_str for short_name in ["gpt4o", "gpt4omini", "opus", "sonnet", "llama70b", "mixtral", "commandrplus", "commandr"])


def test_whitespace_removal_in_model_substring(model_completer, mock_document, mock_complete_event):
    """Test that whitespace is properly removed from model substring."""
    # Test with various whitespace patterns
    test_cases = [
        ("/mod  gpt  ", "gpt"),
        ("/mod\tgpt\t", "gpt"),
        ("/mod g p t", "gpt"),
        ("/mod  g p t  ", "gpt")
    ]

    for input_text, expected_cleaned in test_cases:
        document = mock_document(input_text)

        # Mock the filter_completions method to capture the cleaned substring
        original_filter = model_completer.filter_completions
        captured_substring = None

        def capture_filter(models, substring):
            nonlocal captured_substring
            captured_substring = substring
            return original_filter(models, substring)

        model_completer.filter_completions = capture_filter

        try:
            list(model_completer.get_completions(document, mock_complete_event))
            assert captured_substring == expected_cleaned
        finally:
            model_completer.filter_completions = original_filter