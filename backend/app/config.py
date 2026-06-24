from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Clerk
    clerk_secret_key: str
    clerk_webhook_secret: str

    # Database
    database_url: str
    database_url_direct: str

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""
    stripe_price_team: str = ""
    stripe_price_credits_100: str = ""
    stripe_price_credits_500: str = ""
    stripe_price_credits_2000: str = ""

    # AI providers
    openrouter_api_key: str
    groq_api_key: str = ""
    gemini_api_key: str = ""
    mistral_api_key: str = ""

    # E2B
    e2b_api_key: str

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
