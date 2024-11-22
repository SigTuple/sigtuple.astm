# -*- coding: utf-8 -*-

import json
import os
import re
from senaite.astm.tests.base import ASTMTestBase
from senaite.astm import codec, logger
from senaite.astm.instruments import cellavision_cellalabs


class CellaVisionCellaLabsTest(ASTMTestBase):
    """Test Cella Vision Cella Labs
    """

    data: any

    async def asyncSetUp(self) -> None:

        self.mapping = cellavision_cellalabs.get_mapping()

        pattern = re.compile(r'cellavision_cellalabs.*\.json$')
        for path in self.json_data_files:
            if pattern.search(path):

                logger.info("Reading JSON Data '%s'" %
                            os.path.basename(path))
                with open(path, 'r') as file:
                    self.data = json.load(file)
        
    def test_encode_message(self):
        """Test multiple sequential connections
        """
        recs = self.data['data']
        byte_msgs = codec.iter_encode(recs)
        self.assertEqual([recs[0]], codec.decode(byte_msgs[0]))
        # self.assertEqual([recs[1]], codec.decode(byte_msgs[1])) TODO: To see verify this test
        self.assertEqual([recs[2]], codec.decode(byte_msgs[2]))

    def test_decode_messages(self):
        recs = self.data['data']
        byte_msgs = codec.iter_encode(recs)

        data = {}
        keys = []

        for line in byte_msgs:
            records = codec.decode(line)

            self.assertTrue(isinstance(records, list), True)
            self.assertTrue(len(records) > 0, True)

            record = records[0]
            rtype = record[0]
            wrapper = self.mapping[rtype](*record)
            data[rtype] = wrapper.to_dict()
            keys.append(rtype)

        for key in keys:
            self.assertTrue(key in data)