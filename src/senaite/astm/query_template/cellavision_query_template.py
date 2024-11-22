from typing import List
from senaite.astm.query_template.query_template import QueryTemplate


class CellavisionQueryTemplate(QueryTemplate):

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