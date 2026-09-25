"""Provider billing failures stay actionable without exposing provider payloads."""
import httpx
import openai
import pytest

from officekit import api_errors


@pytest.mark.parametrize('body', [
    {'code': 'credit_balance_exhausted'},
    {'error': {'code': 'credit_balance_exhausted'}},
    {'code': 'insufficient_quota'},
])
def test_structured_sdk_credit_error_is_safe_and_actionable(body):
    error = openai.APIError('Provider rejected the request; token=private-value',
                           request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
                           body=body)
    assert api_errors.classify(error) == (502, api_errors.CREDIT_EXHAUSTED)
    assert api_errors.message(error) == api_errors.CREDIT_EXHAUSTED
    assert 'private-value' not in api_errors.message(error)


@pytest.mark.parametrize('text', [
    'credit_balance_exhausted',
    'You have no credits remaining. Add credits to continue using the API.',
    'Your credit balance is too low to access the Anthropic API.',
])
def test_text_only_credit_errors_are_actionable(text):
    assert api_errors.classify(RuntimeError(text)) == (502, api_errors.CREDIT_EXHAUSTED)
    assert api_errors.message(text) == api_errors.CREDIT_EXHAUSTED


def test_unrelated_sdk_errors_remain_generic():
    error = openai.APIError('Internal failure at /private/customer/file',
                           request=httpx.Request('POST', 'https://api.openai.com/v1/responses'),
                           body={'code': 'unexpected_failure'})
    assert api_errors.classify(error) == (500, api_errors.UNEXPECTED)
