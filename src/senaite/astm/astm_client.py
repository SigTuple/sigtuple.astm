# -*- coding: utf-8 -*-

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
import time
from typing import List

from senaite.astm import codec, lims
from senaite.astm import logger
from senaite.astm.lims import post_to_senaite
from senaite.astm.astm_client_protocol import ASTMClientProtocol
from senaite.astm.utils import write_message

LOGFILE = "sigtuple-astm-client.log"


async def consume(queue, callback=None):
    """ASTM Message consumer coroutine function
    """
    while True:
        message = await queue.get()
        if callable(callback):
            callback(message)

async def send_report_data_to_lis_from_mandara(astm_client: ASTMClientProtocol):
    logger.info("Before send_report_data_to_lis_from_mandara")
    await asyncio.sleep(30)  # Wait 240 seconds, then stop
    logger.info("\n\nSimulate sending approved report data to LIS\n\n")
    with open("src/senaite/astm/tests/data/cobas_c111.txt", "rb") as file:
        lines = file.readlines()  # Each line is an element in the list
        astm_client.send_outbound_message(message_to_LIS=lines)
    logger.info("after opening")

async def send_query_data_to_lis_from_device(astm_client: ASTMClientProtocol):
    logger.info("Before send_query_data_to_lis_from_device")
    await asyncio.sleep(10)  # Wait 30 seconds, then stop
    logger.info("\n\nSimulate sending query CBC request from device to LIS\n\n")
    with open("src/senaite/astm/tests/json_data/cellavision_results.json", "r") as file:
        cellavision_cellalabs_query_json = json.load(file)
        byte_msgs = codec.iter_encode(cellavision_cellalabs_query_json['data'])
        astm_client.send_outbound_message(message_to_LIS=byte_msgs)
    logger.info("after opening")
 

def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Argument groups
    astm_group = parser.add_argument_group('ASTM SERVER')
    lims_group = parser.add_argument_group('SENAITE LIMS')

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
    
    # # Validate JSON file path
    # try:
    #     jsondata = json.load(args.jsonfile[0])
    #     data = jsondata['data']
    # except Exception as e:
    #     logger.error(e)
    #     return sys.exit(-1)
    # byte_msgs = codec.iter_encode(data)

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

    # Validate SENAITE URL
    url = args.url
    if url:
        session = lims.Session(url)
        logger.info('Checking connection to SENAITE ...')
        if not session.auth():
            return sys.exit(-1)

    # Create a ASTM message consumer task to be scheduled concurrently.
    queue = asyncio.Queue()
    instances: List[ASTMClientProtocol] = []
    
    # loop.create_task(consume(queue, callback=dispatch_astm_message))
    # loop.create_task(send_query_data_to_lis_from_device(instances=instances))
    # loop.create_task(send_report_data_to_lis_from_mandara(instances=instances))


    # Create a TCP client coroutine listening on port of the host address.
    # IMPORTANT: We create a new Protocol for every connection!
    client_coro = loop.create_connection(
        lambda: ASTMClientProtocol(queue=queue, message_format=args.message_format, instances=instances),
        host=args.listen, port=args.port)

    # Run until the future (an instance of Future) has completed.
    client = loop.run_until_complete(client_coro)
    logger.info('Starting client on {}'.format(client[1].client))

    # loop.create_task(send_query_data_to_lis_from_device(astm_client=client[1]))
    loop.create_task(send_report_data_to_lis_from_mandara(astm_client=client[1]))

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
