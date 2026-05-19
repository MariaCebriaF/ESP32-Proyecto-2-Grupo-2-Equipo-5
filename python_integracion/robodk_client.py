from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ORDER_PROGRAM_NAME = "Pedidos_PickPlace"
MEDICINE_IDS = {
    "paracetamol": 1,
    "ibuprofeno": 2,
    "enantyum": 3,
    "amoxicilina": 3,
}


@dataclass(frozen=True)
class RobotResult:
    ok: bool
    mode: str
    message: str


class RoboDKClient:
    def __init__(
        self,
        mode: str = "auto",
        robot_name: str = "robot_pedidos",
        target_template: str = "{position}",
        order_program_name: str = DEFAULT_ORDER_PROGRAM_NAME,
        order_execution: str = "program",
    ) -> None:
        self.mode = mode
        self.robot_name = robot_name
        self.target_template = target_template
        self.order_program_name = order_program_name
        self.order_execution = order_execution
        self._rdk = None
        self._item_type_robot = None
        self._item_type_program = None

    @classmethod
    def from_env(cls) -> "RoboDKClient":
        return cls(
            mode=os.getenv("ROBODK_MODE", "auto").lower(),
            robot_name=os.getenv("ROBODK_ROBOT_NAME", "robot_pedidos"),
            target_template=os.getenv("ROBODK_TARGET_TEMPLATE", "{position}"),
            order_program_name=os.getenv("ROBODK_ORDER_PROGRAM_NAME", DEFAULT_ORDER_PROGRAM_NAME),
            order_execution=os.getenv("ROBODK_ORDER_EXECUTION", "program").lower(),
        )

    def execute_order(self, medicine_type: str | None, position: str | None) -> RobotResult:
        medicine_type = str(medicine_type or "").strip().lower()
        position = str(position or "").strip()
        medicine_id = _medicine_id(medicine_type)

        if self.order_execution == "move":
            return self.move_to_position(position)

        if not medicine_type:
            return RobotResult(False, self.mode, "El tipo de medicamento esta vacio")
        if medicine_id is None:
            return RobotResult(False, self.mode, f"Medicamento sin id RoboDK configurado: {medicine_type}")

        if self.mode == "sim":
            detail = f"id={medicine_id} {medicine_type}"
            if position:
                detail += f" en {position}"
            return RobotResult(True, "sim", f"Simulacion RoboDK: ejecutar pedido {detail}")

        try:
            rdk, _item_type_robot, item_type_program = self._connect()
        except Exception as exc:
            if self.mode == "real":
                return RobotResult(False, "real", f"No se pudo conectar con RoboDK: {exc}")
            return RobotResult(True, "sim", f"RoboDK no disponible; simulando pedido id={medicine_id} {medicine_type}: {exc}")

        program = rdk.Item(self.order_program_name, item_type_program)
        if not program.Valid():
            if self.order_execution == "program_only":
                return RobotResult(False, "real", f"No existe el programa '{self.order_program_name}' en la estacion")
            fallback = self.move_to_position(position)
            if fallback.ok:
                return RobotResult(True, fallback.mode, f"No existe el programa '{self.order_program_name}'; {fallback.message}")
            return RobotResult(False, fallback.mode, f"No existe el programa '{self.order_program_name}'. {fallback.message}")

        rdk.setParam("pedido_id", medicine_id)
        rdk.setParam("pedido_tipo", medicine_type)
        rdk.setParam("pedido_posicion", position)
        rdk.setParam("pedido_resultado", "")
        rdk.RunProgram(self.order_program_name, True)

        result = str(rdk.getParam("pedido_resultado") or "").strip().lower()
        if result and result != "ok":
            return RobotResult(False, "real", f"RoboDK ejecuto '{self.order_program_name}' pero devolvio {result}")

        detail = f"id={medicine_id} {medicine_type}"
        if position:
            detail += f" en {position}"
        return RobotResult(True, "real", f"RoboDK ejecuto '{self.order_program_name}' para {detail}")

    def move_to_position(self, position: str) -> RobotResult:
        position = str(position or "").strip()
        if not position:
            return RobotResult(False, self.mode, "La posicion RoboDK esta vacia")

        if self.mode == "sim":
            return RobotResult(True, "sim", f"Simulacion RoboDK: mover a {position}")

        try:
            rdk, item_type_robot, _item_type_program = self._connect()
        except Exception as exc:
            if self.mode == "real":
                return RobotResult(False, "real", f"No se pudo conectar con RoboDK: {exc}")
            return RobotResult(True, "sim", f"RoboDK no disponible; simulando movimiento a {position}: {exc}")

        robot = rdk.Item(self.robot_name, item_type_robot)
        if not robot.Valid():
            return RobotResult(False, "real", f"No existe el robot '{self.robot_name}' en la estacion")

        target_name = self._target_name(position)
        target = rdk.Item(target_name)
        if not target.Valid():
            return RobotResult(False, "real", f"No existe el target '{target_name}' en la estacion")

        robot.MoveJ(target)
        return RobotResult(True, "real", f"RoboDK movio {self.robot_name} a {target_name}")

    def _connect(self):
        if self._rdk is not None:
            return self._rdk, self._item_type_robot, self._item_type_program

        from robodk import robolink

        self._rdk = robolink.Robolink()
        self._item_type_robot = robolink.ITEM_TYPE_ROBOT
        self._item_type_program = robolink.ITEM_TYPE_PROGRAM
        return self._rdk, self._item_type_robot, self._item_type_program

    def _target_name(self, position: str) -> str:
        clean = position.replace("-", "_")
        return self.target_template.format(position=position, position_clean=clean)


def _medicine_id(medicine_type: str) -> int | None:
    return MEDICINE_IDS.get(medicine_type.strip().lower())
