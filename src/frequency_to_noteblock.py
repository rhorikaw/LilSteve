from collections import defaultdict


class TranslationError(Exception):
    '''Error raised if frequency does not have a noteblock translation'''
    def __init__(self, t, f):
        self.t = t
        self.f = f
        super().__init__()

    def __str__(self):
        return "The frequency " + str(self.f) + " at time " + str(self.t) + " does not map to a noteblock in minecraft"


def translate_to_noteblock_number(freq_dict) -> dict:
    '''Takes frequencies and translates to noteblock strings'''
    BLOCK_TRANSLATION = {
        184.997: "F_sharp_3",
        195.998: "G3",
        207.652: "G_sharp_3",
        220: "A3",
        233.082: "A_sharp_3",
        246.941: "B3",
        261.625: "C4",
        277.182: "C_sharp_4",
        293.664: "D4",
        311.127: "D_sharp_4",
        329.627: "E4",
        349.228: "F4",
        369.994: "F_sharp_4",
        391.995: "G4",
        415.304: "G_sharp_4",
        439.999: "A4",
        466.163: "A_sharp_4",
        493.883: "B4",
        523.25: "C4",
        554.365: "C_sharp_5",
        587.329: "D5",
        622.253: "D_sharp_5",
        659.254: "E5",
        698.455: "F5",
        739.988: "F_sharp_5"
    }

    noteblock_dict = defaultdict(str)
    for time, freq in freq_dict.items():
        if freq not in BLOCK_TRANSLATION:
            raise TranslationError(time, freq)
        noteblock_dict[time] = BLOCK_TRANSLATION[freq]
    return noteblock_dict
