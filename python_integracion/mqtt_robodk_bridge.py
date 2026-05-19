from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from db import DEFAULT_DATABASE_URL, database_url, register_storage_event, reserve_order, update_order_status, validate_schema
from robodk_client import RoboDKClient


DEFAULT_BASE_TOPIC = "giirob/pr2/grupo2equipo5"
DEFAULT_MQTT_URL = "mqtt://broker.hivemq.com:1883"


def build_topics(base_topic: str) -> dict[str, str]:
    return {
        "storage_register": f"{base_topic}/almacen/registro",
        "storage_status": f"{base_topic}/almacen/status",
        "order_request": f"{base_topic}/pedido/request",
        "order_status": f"{base_topic}/pedido/status",
        "robot_status": f"{base_topic}/robodk/status",
    }


class Bridge:
    def __init__(self, db_url: str, base_topic: str, client: mqtt.Client) -> None:
        self.db_url = db_url
        self.topics = build_topics(base_topic)
        self.client = client
        self.robot = RoboDKClient.from_env()

    def on_connect(self, client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None) -> None:
        print(f"MQTT conectado: {reason_code}")
        client.subscribe(self.topics["storage_register"])
        client.subscribe(self.topics["order_request"])
        self.publish(self.topics["robot_status"], {"estado": "ready", "service": "python-robodk-bridge"})

    def on_message(self, _client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            print(f"Ignorado payload no JSON en {msg.topic}: {msg.payload!r}")
            return

        if msg.topic == self.topics["storage_register"]:
            self.handle_storage(payload)
        elif msg.topic == self.topics["order_request"]:
            self.handle_order(payload)

    def handle_storage(self, payload: dict[str, Any]) -> None:
        try:
            inserted = register_storage_event(payload, self.db_url)
            estado = "registrado" if inserted else "duplicado"
            self.publish(
                self.topics["storage_status"],
                {
                    "id_evento": payload.get("id_evento"),
                    "estado": estado,
                    "tipo": payload.get("tipo"),
                    "posicion": payload.get("posicion"),
                    "origen": "python-db",
                },
            )
        except Exception as exc:
            self.publish(
                self.topics["storage_status"],
                {
                    "id_evento": payload.get("id_evento"),
                    "estado": "error",
                    "mensaje": str(exc),
                    "origen": "python-db",
                },
            )

    def handle_order(self, payload: dict[str, Any]) -> None:
        try:
            reservation = reserve_order(payload, self.db_url)
        except Exception as exc:
            self.publish(
                self.topics["order_status"],
                {
                    "id_pedido": payload.get("id_pedido"),
                    "estado": "error",
                    "mensaje": str(exc),
                    "origen": "python-db",
                },
            )
            return

        if not reservation.ok:
            self.publish(
                self.topics["order_status"],
                {
                    "id_pedido": reservation.id_pedido,
                    "estado": reservation.estado,
                    "tipo": reservation.tipo,
                    "cantidad": reservation.cantidad,
                    "mensaje": reservation.mensaje,
                    "origen": "python-db",
                },
            )
            return

        self.publish(
            self.topics["order_status"],
            {
                "id_pedido": reservation.id_pedido,
                "estado": "preparando",
                "tipo": reservation.tipo,
                "cantidad": reservation.cantidad,
                "posicion": reservation.posicion,
                "mensaje": f"Pedido reservado; enviando RoboDK a {reservation.posicion}",
                "origen": "python-db-robodk",
            },
        )

        result = self.robot.execute_order(reservation.tipo, reservation.posicion)
        final_state = "completado" if result.ok else "error_robot"
        update_order_status(str(reservation.id_pedido), final_state, result.message, self.db_url)
        self.publish(
            self.topics["order_status"],
            {
                "id_pedido": reservation.id_pedido,
                "estado": final_state,
                "tipo": reservation.tipo,
                "cantidad": reservation.cantidad,
                "posicion": reservation.posicion,
                "robot_mode": result.mode,
                "mensaje": result.message,
                "origen": "python-db-robodk",
            },
        )

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.client.publish(topic, json.dumps(payload, ensure_ascii=True))
        print(f"PUBLICADO {topic}: {payload}")


def create_client(mqtt_url: str) -> mqtt.Client:
    parsed = urlparse(mqtt_url)
    host = parsed.hostname or "broker.hivemq.com"
    port = parsed.port or 1883

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"python-robodk-bridge-{int(time.time())}")
    username = os.getenv("MQTT_USERNAME") or (parsed.username if parsed.username else None)
    password = os.getenv("MQTT_PASSWORD") or (parsed.password if parsed.password else None)
    if username:
        client.username_pw_set(username, password=password)
    client.connect(host, port, 60)
    return client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Puente Python entre MQTT, PostgreSQL y RoboDK")
    parser.add_argument("--database-url", default=database_url(), help="URL PostgreSQL")
    parser.add_argument("--mqtt-url", default=os.getenv("MQTT_URL", DEFAULT_MQTT_URL), help="URL MQTT")
    parser.add_argument("--base-topic", default=os.getenv("MQTT_BASE_TOPIC", DEFAULT_BASE_TOPIC), help="Topic base")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_url = args.database_url or DEFAULT_DATABASE_URL
    validate_schema(db_url)

    client = create_client(args.mqtt_url)
    bridge = Bridge(db_url, args.base_topic, client)
    client.on_connect = bridge.on_connect
    client.on_message = bridge.on_message

    print(f"PostgreSQL: {db_url}")
    print(f"MQTT: {args.mqtt_url}")
    print(f"Base topic: {args.base_topic}")
    client.loop_forever()


if __name__ == "__main__":
    main()
