from shared.exceptions import RuleException


def check_chat_permission(chat_owner_id: int, user_id: int) -> None:
    if chat_owner_id != user_id:
        raise RuleException
