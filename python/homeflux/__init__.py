import os
import logging

logging.basicConfig()
logging.getLogger('asyncio').setLevel(logging.INFO)
logging.getLogger('asyncio.coroutines').setLevel(logging.INFO)
logging.getLogger('websockets').setLevel(logging.INFO)
logging.getLogger('websockets.server').setLevel(logging.INFO)
logging.getLogger('websockets.protocol').setLevel(logging.INFO)
logging.getLogger('websockets.client').setLevel(logging.INFO)

if os.getenv('HOMEFLUX_DEBUG', False):
    logging.getLogger('homeflux').setLevel(10)
