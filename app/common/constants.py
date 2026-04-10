class AuthConstants:
    GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"


class ErrorMessages:
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Forbidden"
    NOT_FOUND = "Resource not found"
    INTERNAL_SERVER_ERROR = "Internal server error"
