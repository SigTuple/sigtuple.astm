# -*- coding: utf-8 -*-

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
from typing import List

from senaite.astm import codec, lims
from senaite.astm import logger
from senaite.astm.lims import post_to_sigtuple
from senaite.astm.astm_client_protocol import ASTMClientProtocol
from senaite.astm.utils import write_message
from senaite.astm import query_template

LOGFILE = "sigtuple-astm-client.log"
DELAY = 60
TEMPLATE: query_template.query_template.QueryTemplate = query_template.cellavision_query_template.CellavisionQueryTemplate()


async def consume(queue, callback=None):
    """ASTM Message consumer coroutine function
    """
    while True:
        message = await queue.get()
        if callable(callback):
            callback(message)


async def send_query_to_astm_server(astm_client: ASTMClientProtocol):
    await asyncio.sleep(DELAY)  
    logger.debug("\n\n==== Simulate sending query to request CBC data from ASTM Server === \n\n")
    TEMPLATE.set_query_record(starting_range=["^202402230004^"])
    query_dict = TEMPLATE.build_query()
    byte_msgs = codec.iter_encode(records=query_dict)
    astm_client.send_outbound_message(message_to_LIS=byte_msgs)
    logger.debug("Query sent succesfully")
 

def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Argument groups
    astm_group = parser.add_argument_group('ASTM SERVER')
    lims_group = parser.add_argument_group('SIGTUPLE LIMS')

    astm_group.add_argument(
        '-l',
        '--listen',
        type=str,
        default='0.0.0.0',
        help='Listen IP address')

    astm_group.add_argument(
        '-p',
        '--port',
        type=str,
        default='4010',
        help='Port to connect')

    astm_group.add_argument(
        '-o',
        '--output',
        type=str,
        help='Output directory to write full messages')
    
    astm_group.add_argument(
        '-j',
        '--jsonfile',
        type=argparse.FileType('r'),
        nargs='+',
        help='JSON file(s) to send')

    lims_group.add_argument(
        '-u',
        '--url',
        type=str,
        help='SENAITE URL address including username and password in the '
             'format: http(s)://<user>:<password>@<senaite_url>')

    lims_group.add_argument(
        '-c',
        '--consumer',
        type=str,
        default='senaite.core.lis2a.import',
        help='SENAITE push consumer interface')

    lims_group.add_argument(
        '-m',
        '--message-format',
        type=str,
        default='json',
        help='Message format to send to SENAITE. '
             'Allowed formats: "astm", "lis2a", "json".')

    lims_group.add_argument(
        '-r',
        '--retries',
        type=int,
        default=3,
        help='Number of attempts of reconnection when SENAITE '
             'instance is not reachable. Only has effect when '
             'argument --url is set')

    lims_group.add_argument(
        '-d',
        '--delay',
        type=int,
        default=5,
        help='Time delay in seconds between retries when '
             'SENAITE instance is not reachable. Only has '
             'effect when argument --url is set')

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose logging')

    parser.add_argument(
        '--logfile',
        default=LOGFILE,
        help='Path to store log files')

    # Parse Arguments
    args = parser.parse_args()

    if args.logfile:
        handler = logging.handlers.RotatingFileHandler(
            args.logfile, maxBytes=5, backupCount=0)
        # Format each log message like this
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(message)s')
        # Attach the formatter to the handler
        handler.setFormatter(formatter)
        # Attach the handler to the logger
        logger.addHandler(handler)
    

    # Get the current event loop.
    loop = asyncio.get_event_loop()

    # Set logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.addHandler(logging.StreamHandler())

    # Validate output path
    output = args.output
    if output and not os.path.isdir(args.output):
        logger.error('Output path must be an existing directory')
        return sys.exit(-1)

    # Validate SIGTUPLE URL
    url = args.url
    if url:
        session = lims.Session(url)
        logger.info('Checking connection to SIGTUPLE ...')
        if not session.auth():
            return sys.exit(-1)
        
    def dispatch_astm_message(message):
        """Dispatch astm message
        """
        logger.debug('Dispatching ASTM Message')
        logger.debug(message)


    # Create a ASTM message consumer task to be scheduled concurrently.
    queue = asyncio.Queue()
    instances: List[ASTMClientProtocol] = []
    
    # Create a TCP client coroutine listening on port of the host address.
    # IMPORTANT: We create a new Protocol for every connection!
    client_coro = loop.create_connection(
        lambda: ASTMClientProtocol(queue=queue, message_format=args.message_format, instances=instances),
        host=args.listen, port=args.port)

    # Run until the future (an instance of Future) has completed.
    client = loop.run_until_complete(client_coro)
    logger.info('Starting client on {}'.format(client[1].client))

    loop.create_task(send_query_to_astm_server(astm_client=client[1]))
    loop.create_task(consume(queue, callback=dispatch_astm_message))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down server...')
        all_tasks = asyncio.gather(
            *asyncio.all_tasks(loop), return_exceptions=True)
        all_tasks.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            loop.run_until_complete(all_tasks)
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()
        logger.info('Server is now down...')


if __name__ == '__main__':
    main()
