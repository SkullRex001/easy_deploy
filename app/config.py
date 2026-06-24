from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    site_dir: Path = Path("/var/www/sites")
    base_domain: str = "avs13.online"
    max_uncompressed:int = 20*1024*1024
    max_files:int = 100
    clone_timeout: int = 60
    
    
    class Config:
        env_file = ".env"


settings = Settings()