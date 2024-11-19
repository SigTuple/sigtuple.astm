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

PRIORITY = (
    "R",    # R: Routine
    "S",    # S: Stat (Urgent)
)

ACTION_CODES = (
    "A",    # A: Perform the analysis on slide
    "C",    # C: Don’t perform any analysis on slide
)

REPORT_TYPES = (
    "F",    # F: Sending result
    "X",    # X: Order cancel by CDMS user
)

RESULT_ABNORMALITY_FLAG = (
    # if Type of analysis is WBC or BFWBC:
    "N",    # N: Normal 
    # if Type of analysis is WBC or BFWBC:
    "L",    # L: Significantly decreased
    "l",    # l: Decreased
    "N",    # N: Normal
    "h",    # h: Increased
)

RESULT_STATUS = (
    "F",    # F: Final result
)

PATIENT_SEX = (
    "F",    # F: Female
    "M",    # M: Male
    "U",    # U: Unknown
)


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
    # 7.1.5: SenderID
    sender = TextField()

    # 7.1.6: SenderFacility
    address = TextField()

    # 7.1.8: SenderTelephoneNumber
    phone = TextField()

    # 7.1.10: ReceiverID
    receiver = TextField()

    # 7.1.14: DateAndTimeOfMessage
    timestamp = TextField()


class PatientRecord(records.PatientRecord):
    """Patient Information Record (P)
    """
    # 8.1.3: Practice Assigned Patient ID
    practice_id = TextField()

    # 8.1.6: PatientName
    name = ComponentField(
        Component.build(
            TextField("last_name"),
            TextField("first_name"),
        )
    )

    # 8.1.8: BirthDate
    birthdate = TextField()

    # 8.1.9: PatientSex
    sex = SetField(values=PATIENT_SEX)

    # 8.1.10: PatientRace-EthnicOrigin
    race = TextField()

    # 8.1.26: Location
    location = TextField()


class OrderRecord(records.OrderRecord):
    """Order Record (O)
    """
    # 9.4.3: Speciment ID
    sample_id = TextField(default="")

    # 9.4.5: Universal Test ID
    test = ComponentField(
        Component.build(
            NotUsedField(name='_'),
            TextField("type_of_analysis"),
            NotUsedField(name='__'),
            NotUsedField(name='___'),
        )
    )

    # 9.4.6: Priority
    priority = SetField(values=PRIORITY)

    # 9.4.8: CollectionDateTime
    sampled_at = DateTimeField()

    # 9.4.12: ActionCode
    action_code = SetField(values=ACTION_CODES)

    # 9.4.14: RelevantClinicalInformation
    clinical_info = TextField()

    # 9.4.17: OrderingPhysician
    physician = TextField()

    # 9.4.19: Abnormality flags
    user_field_1 = ComponentField(
        Component.build(
            TextField("name_of_abnormality"),
            TextField(name='abnormality_flag')
        )
    )

    # 9.4.21: Test specific parameters
    laboratory_field_1 = ComponentField(
        Component.build(
            TextField("value"),
            NotUsedField(name='_')
        )
    )

    # 9.4.22: Values from cell counters
    laboratory_field_2 = ComponentField(
        Component.build(
            TextField("wbc_count"),
            TextField("rbc_concentration"),
            TextField("hgb_count"),
            TextField("hct_count"),
            TextField("mcv_count"),
            TextField("mch_count"),
            TextField("mchc_count"),
            TextField("platelet_count"),
            TextField("reserved_component_1"),
            TextField("reserved_component_2"),
            TextField("reserved_component_3"),
            TextField("reserved_component_4"),
            TextField("reserved_component_5"),
            TextField("neutrophil_count"),
            TextField("lymphocyte_count"),
            TextField("monocyte_count"),
            TextField("Eosinophil_count"),
            TextField("Basophil_count"),
            TextField("nrbc_count"),
            TextField("other_count"),
            TextField("reserved_component_6"),
            TextField("reserved_component_7"),
            TextField("reserved_component_8"),
            TextField("reserved_component_9"),
            TextField("reserved_component_10"),
        )
    )

    # 9.4.25: Instrument Section ID
    instrument_section = TextField()

    # 9.4.26: Report Types
    report_type = SetField(values=REPORT_TYPES)


class CommentRecord(records.CommentRecord):
    """Comment Record (C)
    """


class ResultRecord(records.ResultRecord):
    """Record to transmit analytical data.
    """
    # 10.1.3: Universal Test ID
    test = ComponentField(
        Component.build(
            NotUsedField(name='_'),
            TextField("type_of_analysis"),
            NotUsedField(name='__'),
            TextField("value_of_type"),
        )
    )

    # 10.1.4: DataValue
    value = TextField()

    # 10.1.5: Units
    units = TextField()

    # 10.1.6: ReferenceRanges
    references = TextField()

    # 10.1.7: ResultAbnormalityFlag
    abnormal_flag = SetField(values=RESULT_ABNORMALITY_FLAG)

    # 10.1.9: ResultStatus
    status = SetField(values=RESULT_STATUS)

    # 10.1.11: Operator Identification
    operator = ComponentField(
        Component.build(
            NotUsedField(name='_'),
            TextField("full_name_of_user"),
        )
    )

    # 10.1.13: DateTimeTestCompleted
    completed_at = DateTimeField()


class RequestInformationRecord(records.RequestInformationRecord):
    """Request information Record (Q)
    """
    # 12.1.3: Starting Range ID
    starting_range = ComponentField(
        Component.build(
            NotUsedField(name='_'),
            TextField("order_id"),
            NotUsedField(name='__'),
        )
    )


class ManufacturerInfoRecord(records.ManufacturerInfoRecord):
    """Manufacturer Specific Records (M)
    """


class TerminatorRecord(records.TerminatorRecord):
    """Message Termination Record (L)
    """
