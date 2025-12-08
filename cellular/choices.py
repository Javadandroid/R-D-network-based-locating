from django.db import models

class RadioType(models.TextChoices):
    GSM = 'gsm', '2G (GSM)'
    WCDMA = 'wcdma', '3G (WCDMA)'
    LTE = 'lte', '4G (LTE)'
    NR = 'nr', '5G (NR)'