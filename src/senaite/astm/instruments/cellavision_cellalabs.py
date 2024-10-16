# -*- coding: utf-8 -*-

from senaite.astm import records
from senaite.astm.fields import ComponentField
from senaite.astm.fields import DateTimeField
from senaite.astm.fields import NotUsedField
from senaite.astm.fields import SetField
from senaite.astm.fields import TextField
from senaite.astm.mapping import Component

VERSION = "1.0.0"
# Supports H500 and H550
HEADER_RX = r".*CellaVision"



def get_metadata(wrapper):
    """Additional metadata

    :param wrapper: The wrapper instance
    :returns: dictionary of additional metadata
    """
    return {
        "version": VERSION,
        "header_rx": HEADER_RX,
    }


def get_mapping():
    """Returns the wrappers for this instrument
    """
    return {
        "H": HeaderRecord,
        "P": PatientRecord,
        "O": OrderRecord,
        "R": ResultRecord,
        "C": CommentRecord,
        "Q": RequestInformationRecord,
        "M": ManufacturerInfoRecord,
        "L": TerminatorRecord,
    }


class HeaderRecord(records.HeaderRecord):
    """Message Header Record (H)
    """


class PatientRecord(records.PatientRecord):
    """Patient Information Record (P)
    """


class OrderRecord(records.OrderRecord):
    """Order Record (O)
    """


class CommentRecord(records.CommentRecord):
    """Comment Record (C)
    """


class ResultRecord(records.ResultRecord):
    """Record to transmit analytical data.
    """


class RequestInformationRecord(records.RequestInformationRecord):
    """Request information Record (Q)
    """


class ManufacturerInfoRecord(records.ManufacturerInfoRecord):
    """Manufacturer Specific Records (M)
    """


class TerminatorRecord(records.TerminatorRecord):
    """Message Termination Record (L)
    """
