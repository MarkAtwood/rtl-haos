# tests/test_flex_decoder_id.py
"""Tests for flex decoder ID extraction."""
import pytest

from rtl_manager import _extract_device_id


class TestExtractDeviceId:
    """Tests for _extract_device_id helper function."""

    def test_standard_decoder_top_level_id(self):
        """Standard decoders have top-level id field."""
        data = {
            "model": "Acurite-Tower",
            "id": 12345,
            "temperature_C": 22.5,
        }
        assert _extract_device_id(data) == 12345

    def test_standard_decoder_string_id(self):
        """ID can be a string."""
        data = {
            "model": "Acurite-515",
            "id": "AF:11798",
            "temperature_F": 72.5,
        }
        assert _extract_device_id(data) == "AF:11798"

    def test_flex_decoder_rows_id(self):
        """Flex decoders with get=@...:id have id in rows[0]."""
        data = {
            "model": "EV1527-PIR",
            "count": 1,
            "num_rows": 1,
            "rows": [{"len": 25, "data": "1a16968", "id": 106857, "button": 6}],
            "codes": ["{25}1a16968"],
        }
        assert _extract_device_id(data) == 106857

    def test_flex_decoder_multiple_rows_uses_first(self):
        """When multiple rows exist, use the first one's id."""
        data = {
            "model": "CustomFlex",
            "rows": [
                {"id": 111, "data": "aaa"},
                {"id": 222, "data": "bbb"},
            ],
        }
        assert _extract_device_id(data) == 111

    def test_flex_decoder_codes_fallback(self):
        """Flex decoders without explicit id fall back to codes hex value."""
        data = {
            "model": "GenericFlex",
            "count": 1,
            "num_rows": 1,
            "rows": [{"len": 24, "data": "abcdef"}],  # No id field
            "codes": ["{24}abcdef"],
        }
        assert _extract_device_id(data) == "abcdef"

    def test_flex_decoder_codes_with_bit_count(self):
        """Codes format includes bit count in braces."""
        data = {
            "model": "GenericFlex",
            "codes": ["{32}deadbeef"],
        }
        assert _extract_device_id(data) == "deadbeef"

    def test_no_id_returns_unknown(self):
        """When no ID can be extracted, return 'Unknown'."""
        data = {
            "model": "Mystery",
            "temperature": 25,
        }
        assert _extract_device_id(data) == "Unknown"

    def test_empty_rows_returns_unknown(self):
        """Empty rows array should return Unknown."""
        data = {
            "model": "EmptyFlex",
            "rows": [],
        }
        assert _extract_device_id(data) == "Unknown"

    def test_rows_without_id_falls_back_to_codes(self):
        """Rows without id field should fall back to codes."""
        data = {
            "model": "PartialFlex",
            "rows": [{"len": 20, "data": "12345"}],
            "codes": ["{20}12345"],
        }
        assert _extract_device_id(data) == "12345"

    def test_top_level_id_takes_precedence(self):
        """Top-level id takes precedence over rows[0].id."""
        data = {
            "model": "Hybrid",
            "id": 99999,
            "rows": [{"id": 11111}],
        }
        assert _extract_device_id(data) == 99999

    def test_id_zero_is_valid(self):
        """ID of 0 should be returned (not treated as falsy)."""
        data = {
            "model": "ZeroId",
            "id": 0,
        }
        assert _extract_device_id(data) == 0

    def test_rows_id_zero_is_valid(self):
        """Rows id of 0 should be returned."""
        data = {
            "model": "FlexZero",
            "rows": [{"id": 0, "data": "000"}],
        }
        assert _extract_device_id(data) == 0

    def test_malformed_codes_ignored(self):
        """Malformed codes that don't match pattern are ignored."""
        data = {
            "model": "BadCodes",
            "codes": ["not-a-valid-code"],
        }
        assert _extract_device_id(data) == "Unknown"

    def test_empty_dict(self):
        """Empty dict returns Unknown."""
        assert _extract_device_id({}) == "Unknown"

    def test_non_dict_rows_ignored(self):
        """Non-dict items in rows are handled gracefully."""
        data = {
            "model": "WeirdRows",
            "rows": ["string", 123, None],
        }
        assert _extract_device_id(data) == "Unknown"

    def test_real_world_ev1527(self):
        """Real-world EV1527 PIR sensor data."""
        # Actual output from: -X n=EV1527-PIR,m=OOK_PWM,s=464,l=1404,r=1800,bits=25,get=@0:{20}:id,get=@20:{4}:button
        data = {
            "time": "2024-01-15 10:30:00",
            "model": "EV1527-PIR",
            "count": 1,
            "num_rows": 1,
            "rows": [
                {
                    "len": 25,
                    "data": "1a16968",
                    "id": 106857,
                    "button": 6,
                }
            ],
            "codes": ["{25}1a16968"],
        }
        assert _extract_device_id(data) == 106857

    def test_real_world_generic_remote(self):
        """Generic remote without explicit id extraction."""
        data = {
            "time": "2024-01-15 10:30:00",
            "model": "Generic-Remote",
            "count": 3,
            "num_rows": 3,
            "rows": [
                {"len": 24, "data": "c0ffee"},
                {"len": 24, "data": "c0ffee"},
                {"len": 24, "data": "c0ffee"},
            ],
            "codes": ["{24}c0ffee"],
        }
        # No id in rows, should fall back to codes
        assert _extract_device_id(data) == "c0ffee"
