# app/subdomain.py
import secrets
from pathlib import Path

from app.config import settings


class SubdomainError(RuntimeError):
    pass


class SubdomainGenerator:
    ADJECTIVES = [
        "blue", "swift", "calm", "bright", "bold", "warm", "cool", "keen",
        "lush", "neat", "pure", "vast", "wise", "brave", "quick", "soft",
    ]
    NOUNS = [
        "fox", "hawk", "pine", "river", "lark", "reef", "owl", "wolf",
        "moss", "fern", "dune", "peak", "wave", "leaf", "stone", "cloud",
    ]
    BLOCKLIST = {
        "www", "api", "app", "admin", "mail", "static", "cdn",
        "ftp", "ns", "dev", "test", "staging", "root", "blog",
    }

    MAX_ATTEMPTS = 10

    def __init__(self, sites_dir: Path):
        self.sites_dir = sites_dir or settings.site_dir

    def _random_name(self) -> str:
        adj = secrets.choice(self.ADJECTIVES)
        noun = secrets.choice(self.NOUNS)
        num = secrets.randbelow(1000)
        return f"{adj}-{noun}-{num}"

    def generate(self) -> str:
        """Return a unique subdomain, checked against existing folders + blocklist."""
        for _ in range(self.MAX_ATTEMPTS):
            name = self._random_name()

            if name in self.BLOCKLIST:
                continue

            # the folder existing IS the record of it being taken
            if not (self.sites_dir / name).exists():
                return name

        raise SubdomainError("could not allocate a unique subdomain")


