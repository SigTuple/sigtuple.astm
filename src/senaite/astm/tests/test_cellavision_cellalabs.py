# -*- coding: utf-8 -*-

import json
import os
import re
from senaite.astm.tests.base import ASTMTestBase
from senaite.astm import codec, logger

class CellaVisionCellaLabsTest(ASTMTestBase):
    """Test Cella Vision Cella Labs
    """

    data: any

    async def asyncSetUp(self) -> None:
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
