# -*- coding: utf-8 -*-

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys

from senaite.astm import codec, logger
from senaite.astm.astm_pull_consumer_protocol import ASTMPullConsumerProtocol
from senaite.astm.utils import write_message

LOGFILE = "sigtuple-astm-pull-comsumer.log"


async def consume(queue, callback=None):
    """ASTM Message consumer coroutine function
    """
    while True:
        message = await queue.get()
        if callable(callback):
            callback(message)

def read_json_file(path: str) -> dict:
    data = {}
    with open(path, 'r') as file:
        data = json.load(file)
    return data


def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Argument groups
    astm_group = parser.add_argument_group('ASTM PULL CONSUMER')

    astm_group.add_argument(
        '-a',
        '--address',
        type=str,
        default='127.0.0.1',
        help='ASTM Server IP')

    astm_group.add_argument(
        '-p',
        '--port',
        type=str,
        default='4010',
        help='ASTM Server Port')

    astm_group.add_argument(
        '-j',
        '--jsonfile',
        type=argparse.FileType('rb'),
        nargs='+',
        help='JSON file(s) to send')

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

    # Set logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    # Validate JSON file path
    jsonfilepath = args.jsonfile
    if jsonfilepath and not os.path.isfile(args.jsonfile):
        logger.error('JSON path must be an existing file')
        return sys.exit(-1)
    
    byte_msgs = codec.iter_encode(jsonfilepath['data'])
    
    # Get the current event loop.
    loop = asyncio.get_event_loop()


    # Create a ASTM message consumer task to be scheduled concurrently.
    queue = asyncio.Queue()

    # Create a TCP server coroutine listening on port of the host address.
    # IMPORTANT: We create a new Protocol for every connection!
    server_coro = loop.create_server(
        lambda: ASTMPullConsumerProtocol(queue=queue, message_format=args.message_format, pull_consumer_messages=byte_msgs),
        host=args.listen, port=args.port)

    # Run until the future (an instance of Future) has completed.
    server = loop.run_until_complete(server_coro)

    for socket in server.sockets:
        ip, port = socket.getsockname()
        logger.info('Starting server on {}:{}'.format(ip, port))
        logger.info('ASTM server ready to handle connections ...')

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
