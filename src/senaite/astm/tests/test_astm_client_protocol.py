# -*- coding: utf-8 -*-

from unittest.mock import MagicMock
from unittest.mock import Mock

from senaite.astm.constants import ACK
from senaite.astm.constants import CRLF
from senaite.astm.constants import ENQ
from senaite.astm.constants import EOT
from senaite.astm.constants import NAK
from senaite.astm.astm_client_protocol import ASTMClientProtocol
from senaite.astm.tests.base import ASTMTestBase


class ASTMClientProtocolTest(ASTMTestBase):
    """Test ASTM Communication Protocol
    """

    async def asyncSetUp(self):
        self.protocol = ASTMClientProtocol()

        self.lines = [
            b'\x021H|\\^&|||C111^Roche^c111^4.2.2.1730^1^13147|||||host|RSUPL^REAL|P|1|20230727162028\r\x179B\r\n',
            b'\x022P|1||\r\x174B\r\n',
            b'\x023O|1||T20-10143GA D07^^2||R||||||N|||||||||||20230727162028|||F\r\x17C0\r\n',
            b'\x024R|1|^^^550|95.2|U/L||N||F||$SYS$||20230727162028\r\x17A2\r\n',
            b'\x025C|1|I||I\r\x174F\r\n',
            b'\x026M|1|RR^BM^c111^1|137|137\\136\\430\\421\\414\\409\\590\\615\\656\\691\\719\\744\\763\\776\\786\\795\\942\\998\\1032\\1055\\1071\\1087\\1106\\1121\\1136\\1154\\1168\\1185\\1199\\1219\\1237\\1252\\1271\\1287|0.005564\r\x17AD\r\n',
            b'\x027L|1|N\r\x030A\r\n',
        ]

    def get_mock_transport(self, ip="127.0.0.1", port=12345):
        transport = MagicMock()
        transport.get_extra_info = Mock(return_value=(ip, port))
        transport.write = MagicMock()
        return transport

    def test_connection_made(self):
        # Mock transport and protocol objects
        transport = self.get_mock_transport()

        # Call connection_made on the protocol
        self.protocol.connection_made(transport)

        # Assert that the transport is set correctly
        self.assertEqual(self.protocol.transport, transport)

    def test_astm_communication(self):
        # Mock transport and protocol objects
        transport = self.get_mock_transport()
        self.protocol.transport = transport

        # Establish the connection to build setup the environment
        self.protocol.connection_made(transport)

        # Check that the protocol is not in transfer state
        self.assertFalse(self.protocol.in_transfer_state)

        # Send ENQ
        self.protocol.data_received(ENQ)

        # We should be now in transfer state
        self.assertTrue(self.protocol.in_transfer_state)

        # We expect an ACK as response
        transport.write.assert_called_with(ACK)

        # Sending ENQ again is not allowed
        self.protocol.data_received(ENQ)

        # The protocol should answer with NAK
        transport.write.assert_called_with(NAK)

        # read instrument file
        path = self.get_instrument_file_path("yumizen_h500.txt")
        lines = self.read_file_lines(path)
        for line in lines:
            # Test fixture: Remove trailing \r\n
            message = line.strip(CRLF)
            self.protocol.data_received(message)
            # We expect an ACK as response
            transport.write.assert_called_with(ACK)

        # all messages (without STX, sequence and checksum) should be
        # collected in the protocol
        self.assertTrue(len(self.protocol.messages) == len(lines))

        # Send EOT
        self.protocol.data_received(EOT)
        # We expect an ACK as response
        transport.write.assert_called_with(ACK)

        # Protocol messages should be flushed
        self.assertTrue(len(self.protocol.messages) == 0)

        # Protocol should be no longer in transfer state
        self.assertFalse(self.protocol.in_transfer_state)

    def test_astm_outbound_communication(self):
        # Mock transport and protocol objects
        transport = self.get_mock_transport()
        self.protocol.transport = transport

        # Establish the connection to build setup the environment
        self.protocol.connection_made(transport)

        # Check that the protocol has not sent enq for outbound communication
        self.assertFalse(self.protocol.is_enq_sent_for_outbound_communication)

        # Check that the protocol is outbound connection is not active
        self.assertFalse(self.protocol.is_outbound_connection_active)

        # Check that the protocol attribute `message_to_LIS` is empty
        self.assertEqual(self.protocol.message_to_LIS, [])

        # Check that the protocol attribute `last_sent_outbound_message_idx` is -1
        self.assertEqual(self.protocol.last_sent_outbound_message_idx, -1)

        # initialize outbound communication
        self.protocol.send_outbound_message(message_to_LIS=self.lines)

        # We expect an ENQ to establish connection
        transport.write.assert_called_with(ENQ)

        # Check the protocol attribute `message_to_LIS`, `last_sent_outbound_message_idx` and `is_enq_sent_for_outbound_communication`
        self.assertNotEqual(self.protocol.message_to_LIS, [])
        self.assertEqual(self.protocol.last_sent_outbound_message_idx, -1)
        self.assertTrue(self.protocol.is_enq_sent_for_outbound_communication)

        # We expect and ACK as response
        self.protocol.data_received(ACK)

        # Check the protocol attribute `is_outbound_connection_active`, and `is_enq_sent_for_outbound_communication`
        self.assertNotEqual(self.protocol.last_sent_outbound_message_idx, -1)
        self.assertTrue(self.protocol.is_outbound_connection_active)
        self.assertFalse(self.protocol.is_enq_sent_for_outbound_communication)

        idx = 0
        for line in self.lines:
            # We expect an ASTM client to send each one by one
            transport.write.assert_called_with(line)

            # Check the protocol attribute `last_sent_outbound_message_idx`
            self.assertEqual(self.protocol.last_sent_outbound_message_idx, idx)

            # We expect and ACK as response
            self.protocol.data_received(ACK)

            idx += 1

        # We expect an ASTM client to send EOT for termination
        transport.write.assert_called_with(EOT)

        # Check the protocol attribute
        self.assertEqual(self.protocol.last_sent_outbound_message_idx, -1)
        self.assertFalse(self.protocol.is_outbound_connection_active)
        self.assertFalse(self.protocol.is_enq_sent_for_outbound_communication)
        self.assertEqual(self.protocol.message_to_LIS, [])