'''
Basic abstraction for binding to the alerts exchange
'''

from __future__ import absolute_import

# standard libs
import logging
import traceback
import uuid

# internal imports
from . import exceptions
from .message import Message
from .service import Service
from .spimescape import Spimescape
from .utilities import fancy_doc

__all__ = ['Gogol']

logger = logging.getLogger(__name__)


@fancy_doc
class Gogol(Spimescape):
    def __init__(self, exchange='requests', keys=['#'], name=None, **kwargs):
        '''
        exchange (str): (overrides Service default)
        keys (list): (overrides Service default)

        '''
        logger.debug('Gogol initializing')
        if name is None:
            name = __name__ + '-' + uuid.uuid1().hex[:12]
        Spimescape.__init__(self, exchange=exchange, keys=keys, name=name, **kwargs)
        if isinstance(keys, str):
           keys = [keys]
        self._bindings += [["alerts", a_key] for a_key in keys]

    def this_consume(self, message, method):
        raise NotImplementedError('you must set this_consume to a valid function')

    def on_alert_message(self, channel, method, properties, message):
        logger.debug('in process_message callback')
        try:
            message_unpacked = Message.from_encoded(message, properties.content_encoding)
            self.this_consume(message_unpacked, method)
        except exceptions.DriplineException as err:
            logger.warning(str(err))
        except Exception as err:
            logger.warning('got an exception:\n{}'.format(str(err)))
            logger.debug('traceback follows:\n{}'.format(traceback.format_exc()))
            raise

    def start(self):
        '''
        Begin consuming by calling `self.run` (from Spimescape)
        '''
        logger.debug("AlertConsumer consume starting")
        self.run()
