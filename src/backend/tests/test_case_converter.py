"""Unit tests for the naming-convention helpers used by the ORM base."""

from utils.case_converter import camel_case_to_snake_case, pluralize_snake_case


def test_camel_case_to_snake_case():
    assert camel_case_to_snake_case("Chat") == "chat"
    assert camel_case_to_snake_case("ChatMessage") == "chat_message"
    assert camel_case_to_snake_case("HTTPResponse") == "http_response"


def test_pluralize_snake_case():
    assert pluralize_snake_case("User") == "users"
    assert pluralize_snake_case("Chat") == "chats"
