'''
The portal abstraction is a bit of a mess. Generally speaking it is the crossroad
between abstractions relating to communicating via AMQP and communicating with hardware.
'''

from __future__ import absolute_import

import datetime
import json
import os
import time
import traceback
import uuid

from .endpoint import Endpoint
from .message import Message, AlertMessage, RequestMessage
from .provider import Provider
from .service import Service
from .utilities import fancy_doc

__all__ = ['Spimescape']

import logging
logger = logging.getLogger(__name__)


@fancy_doc
class Spimescape(Service):
    """
    Like a node, but pythonic
    """
    def __init__(self, **kwargs):
        '''
        '''
        if 'exchange' not in kwargs or kwargs['exchange'] is None:
            kwargs['exchange'] = 'requests'
        Service.__init__(self, **kwargs)
        self.add_endpoint(self)

        self._responses = {}

    @property
    def keys(self):
        return [key+'.#' for key in self.endpoints.keys()]
    @keys.setter
    def keys(self, value):
        logger.debug('cannot set keys, use self.endpoints')
        return

    def add_endpoint(self, endpoint):
        '''
        '''
        if endpoint.name in self.endpoints:
            raise ValueError('endpoint ({}) already present'.format(endpoint.name))
        setattr(endpoint, 'store_value', self.send_alert)
        setattr(endpoint, 'service', self)
        self._bindings.append(["requests", endpoint.name+'.#'])
        Provider.add_endpoint(self, endpoint)

    def on_request_message(self, channel, method, header, body):
        logger.info('request received by {}'.format(self.name))
        target = method.routing_key.split('.')[0]
        # messages to "broadcast" should be handled by the service
        if target == 'broadcast':
            method.routing_key = method.routing_key.replace('broadcast', self.name)
            self.handle_request(channel, method, header, body)
        else:
            self.endpoints[target].handle_request(channel, method, header, body)
        logger.info('request processing complete\n{}')

    def _handle_reply(self, channel, method, header, body):
        logger.info("got a reply")
        self._responses[header.correlation_id] = (method, header, body)
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.warning('ack-d')
        logger.info('reply processing complete\n{}'.format('-'*29))
