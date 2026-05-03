from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    FIREBASE_CREDENTIALS_PATH: str
    BASE_URL: str
    IS_ML_STUB: bool = True
    SAVE_UPLOADED_IMAGES: bool = False
    UPLOAD_SAVE_PATH: str = "./uploaded_images"
    SIMULATE_PROGRESS: bool = True
    DEBUG_LOGGING: bool = True
    SHOW_ROI_WINDOWS: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
