"""Regression tests for parsing C++ log definitions.

AP_FLAKE8_CLEAN
"""

import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from vehicle_test_suite import TestSuite as VehicleTestSuite


class LoggerDocumentationTest(unittest.TestCase):
    log_fields = '      "BATI", "Qff", "TimeUS,CapD,CapF", "saa", "F//" }, // extra closing brace }\n'
    common_structures = (
        "const LogStructure log_structure[] = {\n"
        "    LOG_COMMON_STRUCTURES\n"
        "};\n"
    )

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        vehicle = self.root / "ArduCopter"
        vehicle.mkdir()
        self.log_cpp = vehicle / "Log.cpp"

        self.suite = VehicleTestSuite.__new__(VehicleTestSuite)
        self.suite.rc_thread = None
        self.suite.rootdir = lambda: str(self.root)
        self.suite.vehicle_code_dirpath = lambda: str(vehicle)
        self.suite.progress = lambda message: None

    def test_adjacent_amp_hour_multipliers_in_header(self):
        (self.root / "LogStructure.h").write_text(
            "#define LOG_COMMON_STRUCTURES \\\n"
            "    { LOG_BATI_MSG, sizeof(log_BATI), \\\n" + self.log_fields,
            encoding="utf-8",
        )
        self.log_cpp.write_text(self.common_structures, encoding="utf-8")
        formats = self.suite.all_log_format_ids()
        self.assertEqual(formats["BATI"]["multipliers"], "F//")

    def test_adjacent_amp_hour_multipliers_in_vehicle_log(self):
        self.log_cpp.write_text(
            "const LogStructure log_structure[] = {\n"
            "    { LOG_BATI_MSG, sizeof(log_BATI),\n" + self.log_fields + "};\n",
            encoding="utf-8",
        )
        formats = self.suite.all_log_format_ids()
        self.assertEqual(formats["BATI"]["multipliers"], "F//")

    def test_write_with_adjacent_amp_hour_multipliers(self):
        self.log_cpp.write_text(
            self.common_structures +
            'void write_log()\n'
            '{\n'
            '    AP::logger().Write("TEST", "CapD,CapF",\n'
            '                       "aa", "//", "ff", 1.0f, 2.0f); // two capacities\n'
            '}\n',
            encoding="utf-8",
        )
        formats = self.suite.all_log_format_ids()
        self.assertEqual(formats["TEST"]["labels"], "CapD,CapF")


if __name__ == "__main__":
    unittest.main()
