from abc import ABC, abstractmethod
import datetime
from typing import List


class QueryTemplate(ABC):

    header_record: List[List[str]]
    query_record: List[List[str]]
    terminator_record: List[List[str]]
    query: List[List[str]]

    def set_header_record(self) -> None:
        self.header_record = [
            "H",
            [
                [
                None
                ],
                [
                None,
                "&"
                ]
            ],
            None,
            None,
            "CellaVision",
            "CellaLabs",
            None,
            "+91991230103",
            None,
            None,
            None,
            "D",
            "ota-6.7.0",
            datetime.datetime.now()
        ]


    @abstractmethod
    def set_query_record(self, starting_range: List[str]) -> None:
        self.query_record = [
            "Q",
            "1",
            starting_range,
            None,
            "ALL",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        ]
        

    def set_terminator_record(self) -> None:
        self.terminator_record = [
            "L",
            "1",
            "N"
        ]

    def build_query(self) -> List[List[str]]:
        self.set_header_record()
        self.set_terminator_record()
        self.query = [
            self.header_record,
            self.query_record,
            self.terminator_record
        ]
        return self.query

    def get_query(self) -> List[List[str]]:
        return self.query