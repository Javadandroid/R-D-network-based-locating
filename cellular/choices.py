from django.db import models

class RadioType(models.TextChoices):
    GSM = 'gsm', '2G (GSM)'
    UMTS = 'umts', '3G (WCDMA، TD-CDMA, TD-SCDMA)'
    LTE = 'lte', '4G (LTE)'
    NR = 'nr', '5G (NR)'


class DatasetSource(models.TextChoices):
    MLS = 'MLS', 'Mozilla Location Service'
    OPENCELLID = 'OPENCELLID', 'OpenCellID'
    MANUAL = 'MANUAL', 'Manual Entry'
    GOOGLE = 'GOOGLE', 'Google / Road Survey'
    COMBAIN = 'COMBAIN', 'Combain'
    OTHER = 'OTHER', 'Other / Unknown'
