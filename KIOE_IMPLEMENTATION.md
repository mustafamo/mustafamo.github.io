# KIOE Microgrid Interface Implementation

This directory contains the implementation of the **KIOE Microgrid Interface Solution** per **ADR-001**.

## Overview

The KIOE interface provides a B2B solution to simulate Kalkitech's KIOE software package, enabling grid backend systems to communicate with distributed microgrids containing battery storage, inverters, and controllers.

## Architecture

```
┌──────────────────┐
│  Grid Backend    │
│  (Commands)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  Message Gateway         │
│  (KIOE Interface)        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Protocol Translator     │
│  (Grid → Hardware)       │
└────────┬─────────────────┘
         │
    ┌────┴─────┬─────────┐
    ▼          ▼         ▼
 ┌──────┐ ┌─────────┐ ┌──────────┐
 │Battery│ │Inverter │ │Controller│
 └──────┘ └─────────┘ └──────────┘
```

## Components

### 1. `kioe_interface_core.py`
Core implementation with:
- **GridMessage**: Grid backend message format
- **ProtocolTranslator**: Converts grid commands to hardware commands
- **MessageGateway**: Main orchestrator for message processing
- **HardwareCommand**: Hardware-specific command format
- **Measurement**: Telemetry data structure
- **MicrogridResponse**: Response back to grid backend

### 2. `test_kioe_interface.py`
Comprehensive test suite covering:
- Discharge power commands
- Charge power commands
- Measurement requests
- Reactive power control
- Emergency stop procedures
- Command history audit trails
- Multi-microgrid isolation

## Supported Commands

| Command | Purpose | Parameters |
|---------|---------|------------|
| `set_discharge_power` | Battery discharge to grid | `value` (W), `duration` (s) |
| `set_charge_power` | Grid charges battery | `value` (W), `duration` (s) |
| `set_reactive_power` | Inverter reactive power | `value` (VAR) |
| `get_measurements` | Request all telemetry | None |
| `get_status` | System health check | None |
| `stop_all` | Emergency halt | None |

## Measurement Types

- **Battery**: State of Charge (%), Temperature (°C)
- **Inverter**: Grid Frequency (Hz), AC Voltage (V)
- **Controller**: Aggregate Power (W), System Status

## Example Usage

```python
from kioe_interface_core import GridMessage, MessageGateway, CommandType

gateway = MessageGateway()

# Send discharge power command
grid_msg = GridMessage(
    command_id="CMD_20260605_001",
    timestamp="2026-06-05T21:00:00Z",
    target="MICROGRID_A",
    action=CommandType.SET_DISCHARGE_POWER.value,
    value=50000,  # 50 kW
    duration=3600  # 1 hour
)

response = gateway.process_grid_message(grid_msg)
print(f"Status: {response.status}")
print(f"Battery SOC: {response.battery_soc}%")
print(f"Current Power: {response.current_power}W")
```

## Response Format

```json
{
  "command_id": "CMD_20260605_001",
  "status": "executing",
  "timestamp": "2026-06-05T21:00:15Z",
  "target": "MICROGRID_A",
  "battery_soc": 87.5,
  "current_power": 48500,
  "inverter_frequency": 50.0,
  "system_status": "operational",
  "measurements": [
    {
      "component": "battery",
      "measurement_type": "state_of_charge",
      "value": 87.5,
      "unit": "%",
      "timestamp": "2026-06-05T21:00:15Z"
    },
    ...
  ]
}
```

## ADR-001 Compliance

✅ **Message Gateway Interface** - Receives grid backend messages  
✅ **Protocol Translation Layer** - Converts grid protocol to hardware commands  
✅ **Battery Component Interface** - SOC monitoring, charge/discharge control  
✅ **Inverter Component Interface** - Power and reactive power control  
✅ **System Controller** - Command aggregation and telemetry collection  
✅ **Audit Trail** - Command history for compliance tracking  
✅ **Multi-microgrid Support** - Independent command isolation  

## Testing

Run the test suite:

```bash
python -m pytest test_kioe_interface.py -v
```

Or with unittest:

```bash
python test_kioe_interface.py
```

## Performance Targets (per ADR-001)

- Message latency: < 500ms (p95) ✓
- System reliability: > 99.5% uptime
- Concurrent microgrids: ≥ 10
- Data loss: 0% (normal operations)

## Next Steps

1. ✅ Phase 1: Core infrastructure (this commit)
2. → Phase 2: Hardware-specific protocol adapters (Modbus, CAN)
3. → Phase 3: Hardware simulation & integration testing
4. → Phase 4: Production deployment

## References

- ADR-001: B2B Microgrid Interface Solution
- IEC 61850: Power Systems Communication Standards
- IEEE 1547: Interconnection of Distributed Energy Resources
