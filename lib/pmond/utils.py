

UNITS = {
    "B":   2**0,
    "b":   2**0,
    "KiB": 2**10,
    "kb":  2**10,
    "KB":  10**3,
    "MiB": 2**20,
    "mb":  2**20,
    "MB":  10**6,
    "GiB": 2**30,
    "gb":  2**30,
    "GB":  10**9
}

def normalizeBytes(v, unit):
    return v * UNITS[unit]
