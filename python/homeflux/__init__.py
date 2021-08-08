import os

import logzero

_level = 10 if os.getenv('HOMEFLUX_DEBUG', False) else 20
log = logzero.setup_logger('homeflux', level=_level)

