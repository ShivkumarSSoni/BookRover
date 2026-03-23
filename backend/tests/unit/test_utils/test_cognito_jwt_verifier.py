"""Unit tests for CognitoJWTVerifier.

Verifies the JWT verification utility in isolation.  All network calls
(JWKS fetch) are mocked — no real AWS or internet access required.

Test RSA keys are generated once per module using the ``cryptography``
library and signed using ``joserfc``.
"""

import base64
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey

from bookrover.utils.cognito_jwt_verifier import CognitoJWTVerifier

# ---------------------------------------------------------------------------
# Module-level RSA key generation
# ---------------------------------------------------------------------------
# Generated once — shared across all tests in this module.  Generating a
# 2048-bit RSA key takes ~100 ms; doing it inside each test would be slow.

_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)

_PRIVATE_KEY_PEM: bytes = _PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

_TEST_KID = "test-key-id-001"
_TEST_REGION = "ap-south-1"
_TEST_POOL_ID = "ap-south-1_TestPool"
_TEST_CLIENT_ID = "test-client-id"
_TEST_ISSUER = (
    f"https://cognito-idp.{_TEST_REGION}.amazonaws.com/{_TEST_POOL_ID}"
)

# joserfc signing key (private) — kid embedded via parameters.
_SIGNING_KEY = RSAKey.import_key(_PRIVATE_KEY, parameters={"kid": _TEST_KID})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jwks() -> dict:
    """Build a minimal JWKS document from the test RSA private key.

    The ``n`` and ``e`` values are base64url-encoded big-endian integers
    of the public key.  This matches the format Cognito returns.

    Returns:
        JWKS-format dict with a single RSA public key entry.
    """
    pub_numbers = _PRIVATE_KEY.public_key().public_numbers()

    def _encode_int(value: int) -> str:
        length = (value.bit_length() + 7) // 8
        raw = value.to_bytes(length, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": _TEST_KID,
                "alg": "RS256",
                "n": _encode_int(pub_numbers.n),
                "e": _encode_int(pub_numbers.e),
            }
        ]
    }


def _make_token(
    email: str = "user@example.com",
    kid: str = _TEST_KID,
    issuer: str = _TEST_ISSUER,
    audience: str = _TEST_CLIENT_ID,
    exp_offset: int = 3600,
    include_email: bool = True,
    include_kid: bool = True,
) -> str:
    """Sign a test Cognito-like ID token with the test RSA private key.

    Args:
        email: Value to place in the ``email`` claim.
        kid: Key ID to embed in the JOSE header.
        issuer: Value for the ``iss`` claim.
        audience: Value for the ``aud`` claim.
        exp_offset: Seconds from now until the token expires.
        include_email: Whether to include the ``email`` claim.
        include_kid: Whether to include the ``kid`` header.

    Returns:
        Signed JWT string.
    """
    now = int(time.time())
    claims: dict = {
        "sub": "test-sub-id",
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + exp_offset,
        "token_use": "id",
    }
    if include_email:
        claims["email"] = email

    header: dict = {"alg": "RS256"}
    if include_kid:
        header["kid"] = kid

    # Use a key without kid in header when include_kid is False
    signing_key = _SIGNING_KEY if include_kid else RSAKey.import_key(_PRIVATE_KEY)
    return jwt.encode(header, claims, signing_key)


def _make_verifier(client_id: str = _TEST_CLIENT_ID) -> CognitoJWTVerifier:
    """Construct a CognitoJWTVerifier pointed at the test User Pool.

    Args:
        client_id: App Client ID; empty string skips audience validation.

    Returns:
        CognitoJWTVerifier instance with cached KeySet pre-loaded.
    """
    verifier = CognitoJWTVerifier(
        user_pool_id=_TEST_POOL_ID,
        region=_TEST_REGION,
        client_id=client_id,
    )
    # Pre-populate the KeySet cache so no network call is needed.
    verifier._key_set = KeySet.import_key_set(_make_jwks())
    return verifier


# ---------------------------------------------------------------------------
# verify() — happy paths
# ---------------------------------------------------------------------------


def test_verify_returns_email_for_valid_token():
    """A correctly signed token with all valid claims returns its email."""
    verifier = _make_verifier()
    token = _make_token(email="alice@example.com")

    assert verifier.verify(token) == "alice@example.com"


def test_verify_returns_email_without_audience_validation():
    """Verifier with empty client_id skips audience claim validation."""
    verifier = _make_verifier(client_id="")
    now = int(time.time())
    claims = {
        "sub": "sub-xyz",
        "email": "bob@example.com",
        "iss": _TEST_ISSUER,
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode({"alg": "RS256", "kid": _TEST_KID}, claims, _SIGNING_KEY)

    assert verifier.verify(token) == "bob@example.com"


# ---------------------------------------------------------------------------
# verify() — error paths
# ---------------------------------------------------------------------------


def test_verify_raises_value_error_for_expired_token():
    """An expired token (exp in the past) must raise ValueError."""
    verifier = _make_verifier()
    token = _make_token(exp_offset=-1)  # Already expired.

    with pytest.raises(ValueError, match="JWT verification failed"):
        verifier.verify(token)


def test_verify_raises_value_error_for_wrong_issuer():
    """A token with a mismatched issuer must raise ValueError."""
    verifier = _make_verifier()
    token = _make_token(issuer="https://cognito-idp.us-east-1.amazonaws.com/wrong-pool")

    with pytest.raises(ValueError, match="JWT verification failed"):
        verifier.verify(token)


def test_verify_raises_value_error_for_wrong_audience():
    """A token with a mismatched audience must raise ValueError."""
    verifier = _make_verifier(client_id="expected-client")
    token = _make_token(audience="completely-different-client")

    with pytest.raises(ValueError, match="JWT verification failed"):
        verifier.verify(token)


def test_verify_raises_value_error_for_unknown_kid():
    """A token whose kid is absent from the JWKS must raise ValueError."""
    verifier = _make_verifier()
    # Build a token signed with a different key (unknown kid) so signature fails.
    different_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    signing_key = RSAKey.import_key(different_key, parameters={"kid": "unknown-key-id"})
    now = int(time.time())
    claims = {
        "sub": "s", "email": "x@x.com", "iss": _TEST_ISSUER,
        "aud": _TEST_CLIENT_ID, "iat": now, "exp": now + 3600,
    }
    token = jwt.encode({"alg": "RS256", "kid": "unknown-key-id"}, claims, signing_key)

    with pytest.raises(ValueError, match="JWT verification failed"):
        verifier.verify(token)


def test_verify_raises_value_error_for_missing_kid_header():
    """A token with no kid header must raise ValueError."""
    verifier = _make_verifier()
    token = _make_token(include_kid=False)

    with pytest.raises(ValueError, match="missing the 'kid' field"):
        verifier.verify(token)


def test_verify_raises_value_error_for_token_with_no_email_claim():
    """A valid-signature token that omits the email claim raises ValueError."""
    verifier = _make_verifier()
    token = _make_token(include_email=False)

    with pytest.raises(ValueError, match="no 'email' claim"):
        verifier.verify(token)


def test_verify_raises_value_error_for_completely_malformed_token():
    """A string that is not a JWT at all must raise ValueError."""
    verifier = _make_verifier()

    with pytest.raises(ValueError):
        verifier.verify("not.a.jwt")


# ---------------------------------------------------------------------------
# JWKS fetching
# ---------------------------------------------------------------------------


def test_get_key_set_fetches_once_and_caches():
    """KeySet is built only once; subsequent calls use the in-memory cache."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(_make_jwks()).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    verifier = CognitoJWTVerifier(
        user_pool_id=_TEST_POOL_ID,
        region=_TEST_REGION,
    )

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        # First call — should fetch.
        verifier._get_key_set()
        # Second call — should use cache.
        verifier._get_key_set()

    assert mock_open.call_count == 1


def test_fetch_jwks_raises_runtime_error_on_network_failure():
    """A network error during JWKS fetch raises RuntimeError."""
    import urllib.error

    verifier = CognitoJWTVerifier(
        user_pool_id=_TEST_POOL_ID,
        region=_TEST_REGION,
    )

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        with pytest.raises(RuntimeError, match="Unable to fetch JWKS"):
            verifier._fetch_jwks()


def test_jwks_url_is_constructed_correctly():
    """The JWKS URL must embed region and user_pool_id correctly."""
    verifier = CognitoJWTVerifier(
        user_pool_id="eu-west-1_MyPool",
        region="eu-west-1",
    )

    assert verifier._jwks_url == (
        "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_MyPool"
        "/.well-known/jwks.json"
    )
