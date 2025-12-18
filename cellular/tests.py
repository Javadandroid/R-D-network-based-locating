from django.test import TestCase

from cellular.serializers import LocateUserResponseSerializer


class LocateUserResponseSerializationTests(TestCase):
    def test_debug_allows_nulls_for_multi_tower_cases(self):
        payload = {
            "location": {"lat": 35.7, "lon": 51.4, "google": "35.7,51.4"},
            "radius": 123.45,
            "debug": {"source": "COMPOSITE", "bearing_used": None, "signal": None, "confidence": None},
        }
        ser = LocateUserResponseSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
