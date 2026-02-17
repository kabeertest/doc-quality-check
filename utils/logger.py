import logging
import os
import json


def get_logger(name: str = 'doc_quality'):
    """Return a configured logger. Enables file logging when debug is enabled in config or DOC_QC_DEBUG env var."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    # Console handler (INFO by default)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)


    # Check config.json or env var to enable debug file logging
    enable_debug = False

    # 1) Environment variable override
    if os.environ.get('DOC_QC_DEBUG', '').lower() in ('1', 'true', 'yes'):
        enable_debug = True

    # 2) Try to read config.json directly to avoid importing modules package
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg_path = os.path.join(project_root, 'config.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            enable_debug = enable_debug or bool(cfg.get('ui_settings', {}).get('enable_debug', False))
    except Exception:
        # If anything fails, silently continue without config-based debug
        pass

    if enable_debug:
        fh = logging.FileHandler('doc_quality_debug.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        ch.setLevel(logging.DEBUG)

    return logger
