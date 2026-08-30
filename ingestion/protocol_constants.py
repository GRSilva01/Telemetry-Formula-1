import struct

HEADER_FORMAT = "<HBBBB B Q f I I B B"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

TRACK_MAP = {
    0: "Melbourne", 3: "Bahrain", 4: "Catalunya", 5: "Monaco",
    6: "Montreal", 7: "Silverstone", 9: "Hungaroring", 10: "Spa",
    11: "Monza", 12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi",
    15: "Austin", 16: "Sao Paulo", 17: "Austria", 19: "Mexico",
    20: "Baku", 26: "Zandvoort", 27: "Imola", 29: "Jeddah",
    30: "Miami", 31: "Las Vegas", 32: "Qatar"
}