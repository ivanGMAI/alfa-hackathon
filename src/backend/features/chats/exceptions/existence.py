from shared.exceptions import NotFoundException


class ChatNotFoundException(NotFoundException):
    detail = "Chat not found"
