from abc import ABC, abstractmethod


class ICBCTranscoder(ABC):

    @abstractmethod
    def transcode(self, astm_data):
        raise NotImplementedError