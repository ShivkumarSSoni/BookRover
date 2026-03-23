"""Cognito JWT verification utility for BookRover.

Verifies Cognito ID tokens in production (APP_ENV=prod). Fetches the User
Pool's JWKS once per instance, locates the matching public key by key ID
(kid), validates the RS256 signature, and returns the verified email claim.

This utility is ONLY active when APP_ENV=prod.  In dev/test mode the auth
router uses the lightweight base64url dev-token mechanism instead.
"""

import json
import logging
import urllib.request
import urllib.error

from jose import JWTError, jwk, jwt

logger = logging.getLogger(__name__)

_JWKS_URL_TEMPLATE = (
    "https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    "/.well-known/jwks.json"
)


class CognitoJWTVerifier:
    """Verifies AWS Cognito ID tokens and extracts the caller's email.

    Fetches the User Pool's JWKS once per instance (lazy, then cached).
    Verifies the token signature, issuer, and (optionally) audience before
    returning the email claim.

    Attributes:
        _user_pool_id: Cognito User Pool ID (e.g. ``ap-south-1_XXXXXXXX``).
        _region: AWS region where the User Pool lives.
        _client_id: App Client ID used for audience validation; empty string
            means audience checking is skipped.
        _jwks_url: Fully resolved JWKS endpoint URL.
        _jwks: Cached JWKS document; ``None`` until first fetch.
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
        self._jwks: dict | None = None

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

    def _get_jwks(self) -> dict:
        """Return the cached JWKS document, fetching it on first call.

        Returns:
            JWKS JSON document as a dict.
        """
        if self._jwks is None:
            self._jwks = self._fetch_jwks()
            logger.debug("JWKS fetched", extra={"url": self._jwks_url})
        return self._jwks

    def _find_key(self, kid: str) -> dict:
        """Find the JWK entry matching the given key ID.

        Args:
            kid: Key ID from the token's JOSE header.

        Returns:
            Matching JWK entry dict.

        Raises:
            ValueError: If no key with that ``kid`` exists in the JWKS.
        """
        jwks = self._get_jwks()
        for key_entry in jwks.get("keys", []):
            if key_entry.get("kid") == kid:
                return key_entry
        raise ValueError(
            f"No matching key found in JWKS for kid={kid!r}. "
            "The token may have been signed by a different User Pool."
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def verify(self, token: str) -> str:
        """Verify a Cognito ID token and return the caller's email address.

        Validation steps:
        1. Extract ``kid`` from the JOSE header (unverified).
        2. Fetch the matching RSA public key from the JWKS endpoint.
        3. Decode and verify signature with ``RS256``.
        4. Validate ``iss`` matches this User Pool's issuer URL.
        5. Validate ``aud`` matches the App Client ID (if configured).
        6. Extract and return the ``email`` claim.

        Args:
            token: Raw JWT string from the ``Authorization: Bearer`` header.

        Returns:
            Verified email address from the token's ``email`` claim.

        Raises:
            ValueError: If the token is missing, malformed, expired,
                has an invalid signature, or contains no email claim.
        """
        try:
            headers = jwt.get_unverified_headers(token)
        except JWTError as exc:
            raise ValueError(f"Cannot parse token headers: {exc}") from exc

        kid = headers.get("kid")
        if not kid:
            raise ValueError("Token header is missing the 'kid' field.")

        key_entry = self._find_key(kid)

        try:
            public_key = jwk.construct(key_entry)
        except Exception as exc:
            raise ValueError(f"Cannot construct public key: {exc}") from exc

        issuer = (
            f"https://cognito-idp.{self._region}.amazonaws.com"
            f"/{self._user_pool_id}"
        )
        options = {"verify_aud": bool(self._client_id)}
        audience = self._client_id if self._client_id else None

        try:
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=issuer,
                audience=audience,
                options=options,
            )
        except JWTError as exc:
            raise ValueError(f"JWT verification failed: {exc}") from exc

        email: str | None = claims.get("email")
        if not email:
            raise ValueError("Token contains no 'email' claim.")

        return email
