"""Dev launcher: uvicorn with reload, binding 127.0.0.1:8741."""

from __future__ import annotations

import uvicorn

from apulu_hq.config import settings


def main() -> None:
    uvicorn.run(
        "apulu_hq.api:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
