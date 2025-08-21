import os

import uvicorn

from api.settings import settings

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_config=None,
        log_level=settings.log_level.lower(),
    )
