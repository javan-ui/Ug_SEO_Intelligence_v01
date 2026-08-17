from __future__ import annotations

import logging
from pathlib import Path


def try_generate_pdf(html_path: Path, pdf_path: Path, logger: logging.Logger) -> tuple[bool, str | None]:
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return True, None
    except Exception as exc:  # optional dependency and system libraries vary
        logger.warning("PDF generation unavailable: %s", exc)
        return False, str(exc)