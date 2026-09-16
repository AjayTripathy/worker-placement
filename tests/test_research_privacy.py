import json
import pytest
from hosting.gcp.research_privacy import AccountRedactor


def test_positions_preserved_and_accounts_consistently_aliased():
    redact=AccountRedactor(["U12345678", "U87654321"])
    first=b'{"account_id":"U12345678","symbol":"AAPL","quantity":123,"value":10000}'
    second=b'Account U12345678 held AAPL; account U87654321 held MSFT.'
    clean,count=redact.clean(first)
    assert count==1
    assert json.loads(clean)=={'account_id':'ACCOUNT_001','symbol':'AAPL','quantity':123,'value':10000}
    other,count=redact.clean(second)
    assert other==b'Account ACCOUNT_001 held AAPL; account ACCOUNT_002 held MSFT.'
    assert count==2


def test_public_property_account_and_dataset_identifiers_are_preserved():
    source=b'{"accountNumber":123456789,"acct_id":"987654321","value":123456789,"dataset":"F12345678"}'
    assert AccountRedactor(["U12345678"]).clean(source)==(source,0)


def test_research_numbers_and_institution_names_are_unchanged():
    source=b'{"account":"robinhood","ticker":"F","value":10000000,"CUSIP":"123456789"}'
    assert AccountRedactor(["U12345678"]).clean(source)==(source,0)


def test_binary_document_with_identifier_requires_review():
    with pytest.raises(ValueError):AccountRedactor(["U12345678"]).clean(b'%PDF-1.5 account U12345678')
