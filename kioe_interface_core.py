"""
KIOE Microgrid Interface Core Module

B2B solution to simulate Kalkitech KIOE software package.
Translates grid backend messages into commands for battery, inverter, and controller.

Architecture: Message Gateway -> Protocol Translator -> Hardware Controllers
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json
import uuid


class ComponentType(Enum):
    """Supported microgrid component types."""
    BATTERY = "battery"
    INVERTER = "inverter"
    CONTROLLER = "controller"


class CommandType(Enum):
    """Grid backend command types."""
    SET_DISCHARGE_POWER = "set_discharge_power"
    SET_CHARGE_POWER = "set_charge_power"
    SET_REACTIVE_POWER = "set_reactive_power"
    GET_MEASUREMENTS = "get_measurements"
    GET_STATUS = "get_status"
    STOP_ALL = "stop_all"


class MeasurementType(Enum):
    """Hardware measurement types."""
    SOC = "state_of_charge"
    POWER = "power"
    FREQUENCY = "frequency"
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"


@dataclass
class GridMessage:
    """Grid backend message structure per ADR-001."""
    command_id: str
    timestamp: str
    target: str
    action: str
    value: Optional[float] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class HardwareCommand:
    """Hardware-specific command translated from grid message."""
    component: ComponentType
    command_type: CommandType
    command_id: str
    value: Optional[float] = None
    duration: Optional[int] = None
    timestamp: Optional[str] = None


@dataclass
class Measurement:
    """Hardware measurement reading."""
    component: ComponentType
    measurement_type: MeasurementType
    value: float
    unit: str
    timestamp: str


@dataclass
class MicrogridResponse:
    """Response from microgrid to grid backend."""
    command_id: str
    status: str
    timestamp: str
    target: str
    measurements: List[Dict[str, Any]]
    battery_soc: Optional[float] = None
    current_power: Optional[float] = None
    inverter_frequency: Optional[float] = None
    system_status: Optional[str] = None


class ProtocolTranslator:
    """Translates grid backend messages to hardware commands per ADR-001 Phase 2."""

    def __init__(self):
        self.translation_map = {
            CommandType.SET_DISCHARGE_POWER: self._translate_discharge,
            CommandType.SET_CHARGE_POWER: self._translate_charge,
            CommandType.SET_REACTIVE_POWER: self._translate_reactive,
            CommandType.GET_MEASUREMENTS: self._translate_get_measurements,
            CommandType.GET_STATUS: self._translate_get_status,
            CommandType.STOP_ALL: self._translate_stop_all,
        }

    def translate(self, grid_msg: GridMessage) -> List[HardwareCommand]:
        """
        Translate grid backend message to hardware commands.
        
        Args:
            grid_msg: Message from grid backend
            
        Returns:
            List of hardware commands for battery, inverter, and controller
        """
        action = CommandType(grid_msg.action)
        translator = self.translation_map.get(action)
        
        if not translator:
            raise ValueError(f"Unknown action: {grid_msg.action}")
        
        return translator(grid_msg)

    def _translate_discharge(self, msg: GridMessage) -> List[HardwareCommand]:
        """Battery discharge command + inverter AC output."""
        return [
            HardwareCommand(
                component=ComponentType.BATTERY,
                command_type=CommandType.SET_DISCHARGE_POWER,
                command_id=msg.command_id,
                value=msg.value,
                duration=msg.duration,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.INVERTER,
                command_type=CommandType.SET_DISCHARGE_POWER,
                command_id=msg.command_id,
                value=msg.value,
                duration=msg.duration,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.CONTROLLER,
                command_type=CommandType.GET_MEASUREMENTS,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
        ]

    def _translate_charge(self, msg: GridMessage) -> List[HardwareCommand]:
        """Battery charge command + inverter AC input."""
        return [
            HardwareCommand(
                component=ComponentType.BATTERY,
                command_type=CommandType.SET_CHARGE_POWER,
                command_id=msg.command_id,
                value=msg.value,
                duration=msg.duration,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.INVERTER,
                command_type=CommandType.SET_CHARGE_POWER,
                command_id=msg.command_id,
                value=msg.value,
                duration=msg.duration,
                timestamp=msg.timestamp,
            ),
        ]

    def _translate_reactive(self, msg: GridMessage) -> List[HardwareCommand]:
        """Inverter reactive power control."""
        return [
            HardwareCommand(
                component=ComponentType.INVERTER,
                command_type=CommandType.SET_REACTIVE_POWER,
                command_id=msg.command_id,
                value=msg.value,
                timestamp=msg.timestamp,
            ),
        ]

    def _translate_get_measurements(self, msg: GridMessage) -> List[HardwareCommand]:
        """Request telemetry from all components."""
        return [
            HardwareCommand(
                component=ComponentType.BATTERY,
                command_type=CommandType.GET_MEASUREMENTS,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.INVERTER,
                command_type=CommandType.GET_MEASUREMENTS,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.CONTROLLER,
                command_type=CommandType.GET_MEASUREMENTS,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
        ]

    def _translate_get_status(self, msg: GridMessage) -> List[HardwareCommand]:
        """Request system status."""
        return [
            HardwareCommand(
                component=ComponentType.CONTROLLER,
                command_type=CommandType.GET_STATUS,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
        ]

    def _translate_stop_all(self, msg: GridMessage) -> List[HardwareCommand]:
        """Emergency stop - halt all operations."""
        return [
            HardwareCommand(
                component=ComponentType.BATTERY,
                command_type=CommandType.STOP_ALL,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.INVERTER,
                command_type=CommandType.STOP_ALL,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
            HardwareCommand(
                component=ComponentType.CONTROLLER,
                command_type=CommandType.STOP_ALL,
                command_id=msg.command_id,
                timestamp=msg.timestamp,
            ),
        ]


class MessageGateway:
    """
    Main message gateway per ADR-001.
    
    Receives grid backend messages, coordinates translation,
    and aggregates responses from microgrid components.
    """

    def __init__(self):
        self.translator = ProtocolTranslator()
        self.command_queue: Dict[str, List[HardwareCommand]] = {}
        self.measurements_cache: Dict[str, List[Measurement]] = {}

    def process_grid_message(self, grid_msg: GridMessage) -> MicrogridResponse:
        """
        Process incoming grid backend message.
        
        Args:
            grid_msg: Message from grid backend
            
        Returns:
            Response with measurements and status
        """
        # Translate to hardware commands
        hw_commands = self.translator.translate(grid_msg)
        self.command_queue[grid_msg.command_id] = hw_commands

        # Simulate hardware response
        measurements = self._simulate_hardware_response(hw_commands, grid_msg)
        self.measurements_cache[grid_msg.command_id] = measurements

        # Aggregate response
        return self._build_response(grid_msg, measurements)

    def _simulate_hardware_response(
        self, 
        commands: List[HardwareCommand], 
        grid_msg: GridMessage
    ) -> List[Measurement]:
        """Simulate hardware component responses."""
        measurements = []

        for cmd in commands:
            if cmd.command_type == CommandType.GET_MEASUREMENTS:
                measurements.extend(self._get_component_measurements(cmd.component))
            elif cmd.command_type == CommandType.SET_DISCHARGE_POWER:
                # Add power measurement for component
                measurements.append(Measurement(
                    component=cmd.component,
                    measurement_type=MeasurementType.POWER,
                    value=cmd.value * 0.97,  # 97% efficiency
                    unit="W",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                ))
                # Always add battery SOC during discharge
                if cmd.component == ComponentType.BATTERY:
                    measurements.extend(self._get_component_measurements(ComponentType.BATTERY))
            elif cmd.command_type == CommandType.SET_CHARGE_POWER:
                measurements.append(Measurement(
                    component=cmd.component,
                    measurement_type=MeasurementType.POWER,
                    value=cmd.value * 0.95,  # 95% efficiency
                    unit="W",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                ))
                # Always add battery SOC during charge
                if cmd.component == ComponentType.BATTERY:
                    measurements.extend(self._get_component_measurements(ComponentType.BATTERY))

        # Always get controller measurements
        measurements.extend(self._get_component_measurements(ComponentType.CONTROLLER))
        return measurements

    def _get_component_measurements(self, component: ComponentType) -> List[Measurement]:
        """Get current measurements from component."""
        now = datetime.utcnow().isoformat() + "Z"

        if component == ComponentType.BATTERY:
            return [
                Measurement(
                    component=ComponentType.BATTERY,
                    measurement_type=MeasurementType.SOC,
                    value=87.5,
                    unit="%",
                    timestamp=now,
                ),
                Measurement(
                    component=ComponentType.BATTERY,
                    measurement_type=MeasurementType.TEMPERATURE,
                    value=25.3,
                    unit="°C",
                    timestamp=now,
                ),
            ]
        elif component == ComponentType.INVERTER:
            return [
                Measurement(
                    component=ComponentType.INVERTER,
                    measurement_type=MeasurementType.FREQUENCY,
                    value=50.0,
                    unit="Hz",
                    timestamp=now,
                ),
                Measurement(
                    component=ComponentType.INVERTER,
                    measurement_type=MeasurementType.VOLTAGE,
                    value=230.5,
                    unit="V",
                    timestamp=now,
                ),
            ]
        else:  # CONTROLLER
            return [
                Measurement(
                    component=ComponentType.CONTROLLER,
                    measurement_type=MeasurementType.POWER,
                    value=48500.0,
                    unit="W",
                    timestamp=now,
                ),
            ]

    def _build_response(
        self, 
        grid_msg: GridMessage, 
        measurements: List[Measurement]
    ) -> MicrogridResponse:
        """Build response message for grid backend."""
        measurements_dict = []
        for m in measurements:
            m_dict = asdict(m)
            # Convert enum to string value
            m_dict["component"] = m.component.value
            m_dict["measurement_type"] = m.measurement_type.value
            measurements_dict.append(m_dict)
        
        battery_soc = next(
            (m.value for m in measurements 
             if m.component == ComponentType.BATTERY 
             and m.measurement_type == MeasurementType.SOC),
            None
        )
        
        current_power = next(
            (m.value for m in measurements 
             if m.component == ComponentType.CONTROLLER 
             and m.measurement_type == MeasurementType.POWER),
            None
        )
        
        inverter_freq = next(
            (m.value for m in measurements 
             if m.component == ComponentType.INVERTER 
             and m.measurement_type == MeasurementType.FREQUENCY),
            None
        )

        return MicrogridResponse(
            command_id=grid_msg.command_id,
            status="executing",
            timestamp=datetime.utcnow().isoformat() + "Z",
            target=grid_msg.target,
            measurements=measurements_dict,
            battery_soc=battery_soc,
            current_power=current_power,
            inverter_frequency=inverter_freq,
            system_status="operational",
        )

    def get_command_history(self, command_id: str) -> Optional[List[HardwareCommand]]:
        """Retrieve command history for audit trail."""
        return self.command_queue.get(command_id)
