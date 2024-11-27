from senaite.astm.cbc_transcoder.i_cbc_transcoder import ICBCTranscoder


class CellavisionCellalabsCBCTranscoder(ICBCTranscoder):

    def transcode(self, astm_data):
        raise NotImplementedError