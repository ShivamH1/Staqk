from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # `.env.local` takes precedence over `.env` (loaded last); both optional.
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), extra="ignore")

    # Clerk
    clerk_secret_key: str
    clerk_webhook_secret: str

    # Database
    database_url: str
    database_url_direct: str

    # Razorpay (payments — credit packs). Optional so the app boots without them;
    # the order endpoint returns 503 until they're set.
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # AI providers
    openrouter_api_key: str
    groq_api_key: str = ""
    gemini_api_key: str = ""
    mistral_api_key: str = ""

    # E2B
    e2b_api_key: str
    # Custom sandbox template id (more RAM/CPU than the 512MB base — needed for
    # Next.js builds). Empty → E2B's default base template.
    e2b_template: str = ""

    # Vercel
    vercel_access_token: str = ""
    vercel_team_id: str = ""

    # Observability
    sentry_dsn: str = ""
    sentry_auth_token: str = ""

    # Email
    resend_api_key: str = ""
    resend_from_email: str = "noreply@staqk.com"

    # Feature flags
    enable_rag: bool = False


settings = Settings()
