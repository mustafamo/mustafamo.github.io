# ADR-001: B2B Microgrid Interface Solution - KIOE Package Simulation

**Date:** 2026-06-05  
**Status:** Proposed  
**Deciders:** Architecture Team  
**Affects:** Grid Backend Integration, Microgrid Control System  

## Context

We need to establish a B2B (Business-to-Business) interface solution that simulates the Kalkitech KIOE (Kalkitech Integrated Operating Environment) software package. This package serves as a critical bridge between grid backend systems and distributed energy resource (DER) microgrids.

### Current Problem

- Grid backend systems generate control messages and request measurements from distributed microgrid installations
- These messages need to be translated into hardware-compatible commands and measurement protocols
- The microgrid system consists of multiple interconnected components:
  - Battery Energy Storage System (BESS)
  - Inverter (DC to AC conversion)
  - System Controller (centralized logic)

### Business Requirements

- Support real-time communication between grid operators and microgrid assets
- Enable dynamic energy dispatch and demand response
- Maintain data consistency and message reliability
- Provide monitoring and diagnostics capabilities

## Decision

We will implement a **KIOE-compatible interface layer** that:

1. **Accepts Grid Backend Messages** - Receive standardized control commands and measurement requests from the grid management system
2. **Translates Messages** - Convert grid protocol messages to hardware-specific commands and measurement queries
3. **Manages Microgrid Components**:
   - **Battery Controller**: State of charge (SOC), charging/discharging commands, power limits
   - **Inverter**: AC/DC conversion control, frequency management, reactive power control
   - **System Controller**: Aggregate commands, manage component coordination, handle failover logic
4. **Returns Measurements** - Send back telemetry data in grid-compatible formats

## Architectural Components

### 1. Message Gateway Interface
```
Grid Backend <---> [Message Gateway] <---> KIOE Translator <---> Hardware Controllers
```

### 2. Protocol Translation Layer
- **Input**: Grid backend protocol (REST/MQTT/TCP)
- **Output**: Hardware-specific commands (Modbus, CAN, proprietary protocols)

### 3. Microgrid Control Stack

#### Battery Component Interface
- Real-time SOC monitoring
- Charge/discharge setpoint management
- Power ramp rate limiting
- Temperature and health monitoring

#### Inverter Component Interface
- Active/reactive power control
- Voltage and frequency regulation
- Anti-islanding protection
- Grid connection state management

#### System Controller
- Component state aggregation
- Conflict resolution
- Failover and redundancy management
- Telemetry collection and reporting

## Consequences

### Positive
✅ **Standardized Integration** - KIOE compatibility ensures interoperability with grid operators  
✅ **Scalability** - Support multiple microgrids with consistent interface  
✅ **Reliability** - Clear separation between grid communication and hardware control  
✅ **Maintainability** - Centralized message translation logic  
✅ **Monitoring** - Comprehensive audit trail of grid-to-microgrid transactions  

### Negative / Risks
⚠️ **Complexity** - Requires understanding of both grid protocols and hardware interfaces  
⚠️ **Latency** - Message translation adds processing overhead (mitigate with async processing)  
⚠️ **Vendor Lock-in** - Deep KIOE dependency (mitigate with abstraction layer)  
⚠️ **Testing Burden** - Comprehensive integration testing required with hardware simulations  

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
- Define KIOE message schema and hardware command protocols
- Create message validation framework
- Implement basic gateway structure

### Phase 2: Component Integration (Weeks 3-4)
- Battery interface implementation
- Inverter interface implementation
- System controller orchestration

### Phase 3: Testing & Simulation (Weeks 5-6)
- Hardware simulator development
- End-to-end integration testing
- Performance and reliability validation

### Phase 4: Deployment (Week 7+)
- Production rollout with pilot sites
- Monitoring and optimization

## Data Flow Example

```
1. Grid Backend sends:
   {
     "command_id": "CMD_20260605_001",
     "timestamp": "2026-06-05T21:00:00Z",
     "target": "MICROGRID_A",
     "action": "set_discharge_power",
     "value": 50000,  // 50 kW
     "duration": 3600 // 1 hour
   }

2. KIOE Translator converts to:
   - Battery: "SET_DISCHARGE_POWER: 50000W"
   - Inverter: "SET_AC_OUTPUT: 50000W"
   - Controller: "MONITOR_SOC, REPORT_EVERY_30S"

3. Measurements returned:
   {
     "command_id": "CMD_20260605_001",
     "status": "executing",
     "battery_soc": 87.5,
     "current_power": 48500,
     "timestamp": "2026-06-05T21:00:15Z"
   }
```

## Alternatives Considered

### Alternative 1: Direct Protocol Mapping
- **Pros**: Minimal overhead, simple implementation
- **Cons**: Not KIOE compatible, requires custom integration per grid operator
- **Rejected**: Does not meet B2B standardization requirement

### Alternative 2: Third-Party Gateway (e.g., Industrial IoT Platform)
- **Pros**: Feature-rich, vendor support
- **Cons**: Cost, vendor lock-in, may not support KIOE specifics
- **Rejected**: Custom solution provides better control and cost efficiency

## Success Criteria

- ✅ KIOE message compliance validation passes 100% of test cases
- ✅ Message latency < 500ms (p95)
- ✅ System reliability > 99.5% uptime
- ✅ Support minimum 10 simultaneous microgrid connections
- ✅ Zero data loss during normal operations

## References

- KIOE Software Package Documentation (Kalkitech)
- IEC 61850 - Power Systems Communication Standards
- IEEE 1547 - Interconnection of Distributed Energy Resources
- Microgrid Technical Requirements Specification (Internal)

## Next Steps

1. Present ADR to architecture review board
2. Gather stakeholder feedback and refine
3. Initiate Phase 1 development sprint
4. Establish hardware simulation environment
