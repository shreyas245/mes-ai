"""Connector factory (Abstract Factory / Factory Method, GoF Creational).

The gateway config names a protocol per source; the factory builds the right
``Connector`` without the caller importing concrete classes. New protocols
register here only.
"""

from __future__ import annotations

from collections.abc import Callable

from edge_gateway.connectors.base import Connector
from edge_gateway.connectors.modbus import ModbusConnector
from edge_gateway.connectors.mqtt import MqttSparkplugConnector
from edge_gateway.connectors.opcua import OpcUaConnector

_BUILDERS: dict[str, Callable[[dict], Connector]] = {
    "opcua": lambda cfg: OpcUaConnector(endpoint=cfg["endpoint"]),
    "mqtt": lambda cfg: MqttSparkplugConnector(
        broker=cfg["broker"], group_id=cfg.get("group_id", "mes")
    ),
    "modbus": lambda cfg: ModbusConnector(
        host=cfg["host"], port=int(cfg.get("port", 502))
    ),
}


def create_connector(protocol: str, config: dict) -> Connector:
    try:
        return _BUILDERS[protocol](config)
    except KeyError as exc:
        raise ValueError(f"unknown protocol '{protocol}'") from exc


def register_protocol(name: str, builder: Callable[[dict], Connector]) -> None:
    _BUILDERS[name] = builder
