# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import time

from senaite.astm import logger
from senaite.astm.constants import ACK, ENQ, EOT


def main():
    # Argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Argument groups
    astm_group = parser.add_argument_group('ASTM SERVER')

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
        '-d',
        '--delay',
        type=float,
        default=10,
        help='Delay in seconds between two frames.')
    
    astm_group.add_argument(
        '-i',
        '--infile',
        type=argparse.FileType('rb'),
        nargs='+',
        help='ASTM file(s) to send')

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose logging')

    # Parse Arguments
    args = parser.parse_args()

    # Set logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    lines = args.infile[0].readlines()
    logger.info(lines)

    # Get the current event loop.
    loop = asyncio.get_event_loop()

    task = create_client(args.address, args.port, delay=args.delay, lines=lines)
    loop.create_task(task)
    
    try:
        all_tasks = asyncio.gather(
            *asyncio.all_tasks(loop), return_exceptions=True)
        loop.run_until_complete(all_tasks)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    finally:
        loop.close()
        logger.info('Done')

async def create_client(address, port, delay, lines):
    # open a new conection for every message
    reader, writer = await asyncio.open_connection(address, port)
    i = 0
    n = len(lines)
    while(True):
        response = await reader.read(1000)
        if response:
            logger.info('<- Got response: {!r}'.format(response))
            if response == ACK:
                if i < n:
                    line = lines[i]
                    writer.write(line)
                    logger.info(f'-> Sent Message line {line}')
                    i += 1
                else:
                    writer.write(EOT)
                    logger.info(f'-> Sent Message EOT {EOT}')
            else:
                writer.write(ACK)
                logger.info('-> Sent Acknowledgment')
                # if response == b'\x023L|1|N\r\x0306\r\n':
                #     writer.write(ENQ)
                #     logger.info(f'-> Sent Message ENQ {ENQ}')
                # else:
                #     writer.write(ACK)
                #     logger.info('-> Sent Acknowledgment')
        time.sleep(1)

if __name__ == '__main__':
    main()
