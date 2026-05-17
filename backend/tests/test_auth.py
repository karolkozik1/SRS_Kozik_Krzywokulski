from app.auth import hash_password, verify_password, create_access_token, decode_token


def test_hash_password_returns_different_value_than_raw_password():
    raw_password = "TestoweHaslo123!"

    hashed_password = hash_password(raw_password)

    assert hashed_password != raw_password
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0


def test_verify_password_returns_true_for_correct_password():
    raw_password = "TestoweHaslo123!"
    hashed_password = hash_password(raw_password)

    result = verify_password(raw_password, hashed_password)

    assert result is True


def test_verify_password_returns_false_for_wrong_password():
    raw_password = "TestoweHaslo123!"
    wrong_password = "ZleHaslo123!"
    hashed_password = hash_password(raw_password)

    result = verify_password(wrong_password, hashed_password)

    assert result is False


def test_create_and_decode_access_token():
    token = create_access_token(user_id=1, role_id=3)

    payload = decode_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == 3