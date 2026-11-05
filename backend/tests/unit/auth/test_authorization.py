import pytest
from app.auth.authorization import AccountAccessDenied, authorized_account_id


@pytest.mark.parametrize('identity', ['A', 'B'])
def test_returns_authenticated_identity(identity):
    assert authorized_account_id(identity, identity) is identity


@pytest.mark.parametrize(('identity', 'requested'), [
    ('A', 'B'), ('B', 'A'), ('A', ''), ('', ''), (None, None),
    (1, 1), ('A', None), ('A', 'a'), ('A', ' A'), ('A', 'A '), (' ', ' '),
])
def test_denies_without_normalizing_or_disclosing_accounts(identity, requested):
    with pytest.raises(AccountAccessDenied) as exc:
        authorized_account_id(identity, requested)
    assert str(exc.value) == ''
