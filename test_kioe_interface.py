"""
Unit tests for KIOE Microgrid Interface.
Validates ADR-001 compliance and message flow.
"""

import unittest
from datetime import datetime
from kioe_interface_core import (
    GridMessage,
    MessageGateway,
    CommandType,
    ComponentType,
    MeasurementType,
)


class TestKIOEInterface(unittest.TestCase):
    """Test suite for KIOE interface implementation."""

    def setUp(self):
        """Initialize gateway for each test."""
        self.gateway = MessageGateway()

    def test_discharge_power_command(self):
        """Test discharge power command translation per ADR-001 Phase 2."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_001",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.SET_DISCHARGE_POWER.value,
            value=50000,  # 50 kW
            duration=3600,  # 1 hour
        )

        response = self.gateway.process_grid_message(grid_msg)

        # Verify response structure
        self.assertEqual(response.command_id, "CMD_20260605_001")
        self.assertEqual(response.status, "executing")
        self.assertEqual(response.target, "MICROGRID_A")
        self.assertIsNotNone(response.battery_soc)
        self.assertIsNotNone(response.current_power)
        self.assertEqual(response.system_status, "operational")

    def test_charge_power_command(self):
        """Test charge power command translation."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_002",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.SET_CHARGE_POWER.value,
            value=30000,  # 30 kW
            duration=1800,  # 30 minutes
        )

        response = self.gateway.process_grid_message(grid_msg)

        self.assertEqual(response.command_id, "CMD_20260605_002")
        self.assertEqual(response.status, "executing")
        self.assertIsNotNone(response.measurements)

    def test_get_measurements_command(self):
        """Test measurement request from all components."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_003",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.GET_MEASUREMENTS.value,
        )

        response = self.gateway.process_grid_message(grid_msg)

        # Should have measurements from battery, inverter, controller
        self.assertGreaterEqual(len(response.measurements), 3)
        measurement_types = {m["measurement_type"] for m in response.measurements}
        
        # Verify key measurement types are present
        self.assertIn(MeasurementType.SOC.value, measurement_types)
        self.assertIn(MeasurementType.FREQUENCY.value, measurement_types)

    def test_reactive_power_command(self):
        """Test reactive power (Q) control for grid support."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_004",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.SET_REACTIVE_POWER.value,
            value=10000,  # 10 kVAR
        )

        response = self.gateway.process_grid_message(grid_msg)

        self.assertEqual(response.command_id, "CMD_20260605_004")
        self.assertEqual(response.status, "executing")

    def test_command_history_audit_trail(self):
        """Test command history for audit trail per ADR-001."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_005",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.SET_DISCHARGE_POWER.value,
            value=50000,
        )

        self.gateway.process_grid_message(grid_msg)
        history = self.gateway.get_command_history("CMD_20260605_005")

        # Should have hardware commands for battery, inverter, controller
        self.assertIsNotNone(history)
        self.assertEqual(len(history), 3)
        
        components = {cmd.component for cmd in history}
        self.assertEqual(
            components,
            {ComponentType.BATTERY, ComponentType.INVERTER, ComponentType.CONTROLLER}
        )

    def test_emergency_stop_command(self):
        """Test emergency stop (critical for safety)."""
        grid_msg = GridMessage(
            command_id="CMD_20260605_STOP",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.STOP_ALL.value,
        )

        response = self.gateway.process_grid_message(grid_msg)

        self.assertEqual(response.command_id, "CMD_20260605_STOP")
        self.assertEqual(response.status, "executing")

        history = self.gateway.get_command_history("CMD_20260605_STOP")
        self.assertEqual(len(history), 3)  # All three components receive stop

    def test_message_timestamp_preservation(self):
        """Test that timestamps are preserved through translation."""
        timestamp = "2026-06-05T21:15:30Z"
        grid_msg = GridMessage(
            command_id="CMD_20260605_006",
            timestamp=timestamp,
            target="MICROGRID_A",
            action=CommandType.GET_STATUS.value,
        )

        response = self.gateway.process_grid_message(grid_msg)

        history = self.gateway.get_command_history("CMD_20260605_006")
        for cmd in history:
            self.assertEqual(cmd.timestamp, timestamp)

    def test_multiple_microgrids_isolation(self):
        """Test that multiple microgrids are isolated."""
        msg_a = GridMessage(
            command_id="CMD_A_001",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_A",
            action=CommandType.SET_DISCHARGE_POWER.value,
            value=50000,
        )

        msg_b = GridMessage(
            command_id="CMD_B_001",
            timestamp="2026-06-05T21:00:00Z",
            target="MICROGRID_B",
            action=CommandType.SET_CHARGE_POWER.value,
            value=30000,
        )

        response_a = self.gateway.process_grid_message(msg_a)
        response_b = self.gateway.process_grid_message(msg_b)

        # Responses should be independent
        self.assertEqual(response_a.target, "MICROGRID_A")
        self.assertEqual(response_b.target, "MICROGRID_B")
        self.assertEqual(response_a.command_id, "CMD_A_001")
        self.assertEqual(response_b.command_id, "CMD_B_001")


if __name__ == "__main__":
    unittest.main()
