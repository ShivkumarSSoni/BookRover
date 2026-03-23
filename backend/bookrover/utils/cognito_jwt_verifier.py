"""Cognito JWT verification utility for BookRover.

Verifies Cognito ID tokens in production (APP_ENV=prod). Fetches the User
Pool's JWKS once per instance, locates the matching public key by key ID
(kid), validates the RS256 signature, and returns the verified email claim.

This utility is ONLY active when APP_ENV=prod.  In dev/test mode the auth
router uses the lightweight base64url dev-token mechanism instead.

Uses ``joserfc`` for all cryptographic operations — it depends only on the
``cryptography`` package and has no exposure to the CVE-2024-23342 timing
side-channel that affected the ``ecdsa`` transitive dependency of
``python-jose``.
"""

import json
import logging
import urllib.request
import urllib.error

from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry

logger = logging.getLogger(__name__)

_JWKS_URL_TEMPLATE = (
    "https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    "/.well-known/jwks.json"
)


class CognitoJWTVerifier:
    """Verifies AWS Cognito ID tokens and extracts the caller's email.

    Fetches the User Pool's JWKS once per instance (lazy, then cached) and
    builds a ``joserfc`` ``KeySet`` from it. Verifies the token signature,
    issuer, and (optionally) audience before returning the email claim.

    Attributes:
        _user_pool_id: Cognito User Pool ID (e.g. ``ap-south-1_XXXXXXXX``).
        _region: AWS region where the User Pool lives.
        _client_id: App Client ID used for audience validation; empty string
            means audience checking is skipped.
        _jwks_url: Fully resolved JWKS endpoint URL.
        _key_set: Cached ``KeySet`` instance; ``None`` until first fetch.
    """

    def __init__(
        self,
        user_pool_id: str,
        region: str,
        client_id: str = "",
    ) -> None:
        """Initialise the verifier with User Pool coordinates.

        Args:
            user_pool_id: Cognito User Pool ID.
            region: AWS region of the User Pool.
            client_id: App Client ID for audience validation (optional).
        """
        self._user_pool_id = user_pool_id
        self._region = region
        self._client_id = client_id
        self._jwks_url = _JWKS_URL_TEMPLATE.format(
            region=region, user_pool_id=user_pool_id
        )
        self._key_set: KeySet | None = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_jwks(self) -> dict:
        """Download the JWKS document from Cognito's well-known endpoint.

        Uses Python's built-in ``urllib.request`` (no extra dependency).

        Returns:
            Parsed JWKS JSON as a dict.

        Raises:
            RuntimeError: If the endpoint is unreachable or returns a
                non-200 response.
        """
        try:
            with urllib.request.urlopen(self._jwks_url, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Unable to fetch JWKS from {self._jwks_url}: {exc}"
            ) from exc

    def _get_key_set(self) -> KeySet:
        """Return the cached ``KeySet``, fetching and building it on first call.

        Returns:
            ``joserfc`` ``KeySet`` populated from the Cognito JWKS endpoint.
        """
        if self._key_set is None:
            jwks_dict = self._fetch_jwks()
            self._key_set = KeySet.import_key_set(jwks_dict)
            logger.debug("JWKS fetched and KeySet built", extra={"url": self._jwks_url})
        return self._key_set

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def verify(self, token: str) -> str:
        """Verify a Cognito ID token and return the caller's email address.

        Validation steps:
        1. Decode the token and verify its RS256 signature against the JWKS.
        2. Validate ``iss`` matches this User Pool's issuer URL.
        3. Validate ``aud`` matches the App Client ID (if configured).
        4. Extract and return the ``email`` claim.

        Args:
            token: Raw JWT string from the ``Authorization: Bearer`` header.

        Returns:
            Verified email address from the token's ``email`` claim.

        Raises:
            ValueError: If the token is missing, malformed, expired,
                has an invalid signature, or contains no email claim.
        """
        key_set = self._get_key_set()

        try:
            token_obj = jwt.decode(token, key_set, algorithms=["RS256"])
        except JoseError as exc:
            raise ValueError(f"JWT verification failed: {exc}") from exc

        if not token_obj.header.get("kid"):
            raise ValueError("Token header is missing the 'kid' field.")

        issuer = (
            f"https://cognito-idp.{self._region}.amazonaws.com"
            f"/{self._user_pool_id}"
        )

        claims_options: dict = {
            "iss": {"essential": True, "value": issuer},
            "exp": {"essential": True},
        }
        if self._client_id:
            claims_options["aud"] = {"essential": True, "value": self._client_id}

        try:
            registry = JWTClaimsRegistry(**claims_options)
            registry.validate(token_obj.claims)
        except JoseError as exc:
            raise ValueError(f"JWT verification failed: {exc}") from exc

        email: str | None = token_obj.claims.get("email")
        if not email:
            raise ValueError("Token contains no 'email' claim.")

        return email
