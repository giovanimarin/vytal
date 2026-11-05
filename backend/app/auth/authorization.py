"""Account ownership policy, independent of HTTP and persistence."""


class AccountAccessDenied(Exception):
    """The requested account is not the authenticated principal."""


def authorized_account_id(authenticated_id: str, requested_id: str) -> str:
    """Return only the validated principal; never normalize client identifiers."""
    if (
        not isinstance(authenticated_id, str)
        or not authenticated_id.strip()
        or not isinstance(requested_id, str)
        or requested_id != authenticated_id
    ):
        raise AccountAccessDenied()
    return authenticated_id
