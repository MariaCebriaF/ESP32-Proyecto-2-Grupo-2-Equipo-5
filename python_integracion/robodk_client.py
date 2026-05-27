from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ORDER_PROGRAM_NAME = "Pedidos_PickPlace"
DEFAULT_STORAGE_PROGRAM_NAME = "ProgramaClasificacion"
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
        storage_program_name: str = DEFAULT_STORAGE_PROGRAM_NAME,
    ) -> None:
        self.mode = mode
        self.robot_name = robot_name
        self.target_template = target_template
        self.order_program_name = order_program_name
        self.order_execution = order_execution
        self.storage_program_name = storage_program_name
        self._rdk = None
        self._item_type_robot = None
        self._item_type_program = None
        self._robolink = None

    @classmethod
    def from_env(cls) -> "RoboDKClient":
        return cls(
            mode=os.getenv("ROBODK_MODE", "auto").lower(),
            robot_name=os.getenv("ROBODK_ROBOT_NAME", "robot_pedidos"),
            target_template=os.getenv("ROBODK_TARGET_TEMPLATE", "{position}"),
            order_program_name=os.getenv("ROBODK_ORDER_PROGRAM_NAME", DEFAULT_ORDER_PROGRAM_NAME),
            order_execution=os.getenv("ROBODK_ORDER_EXECUTION", "program").lower(),
            storage_program_name=os.getenv("ROBODK_STORAGE_PROGRAM_NAME", DEFAULT_STORAGE_PROGRAM_NAME),
        )

    def execute_order(self, medicine_type: str | None, position: str | None, medicine_id: int | None = None) -> RobotResult:
        medicine_type = str(medicine_type or "").strip().lower()
        position = str(position or "").strip()
        medicine_id = _valid_medicine_id(medicine_id) or _medicine_id(medicine_type)

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
            rdk, _item_type_robot, _item_type_program = self._connect()
        except Exception as exc:
            if self.mode == "real":
                return RobotResult(False, "real", f"No se pudo conectar con RoboDK: {exc}")
            return RobotResult(True, "sim", f"RoboDK no disponible; simulando pedido id={medicine_id} {medicine_type}: {exc}")

        program = self._find_program(self.order_program_name)
        if not program.Valid():
            visible = self._visible_program_names()
            detail = f"No existe el programa '{self.order_program_name}' en la estacion"
            if visible:
                detail += f". Programas visibles: {', '.join(visible)}"
            if self.order_execution == "program_only":
                return RobotResult(False, "real", detail)
            fallback = self.move_to_position(position)
            if fallback.ok:
                return RobotResult(True, fallback.mode, f"{detail}; {fallback.message}")
            return RobotResult(False, fallback.mode, f"{detail}. {fallback.message}")

        rdk.setParam("pedido_id", medicine_id)
        rdk.setParam("pedido_tipo", medicine_type)
        rdk.setParam("pedido_posicion", position)
        rdk.setParam("pedido_resultado", "")
        rdk.RunProgram(program.Name(), True)

        result = str(rdk.getParam("pedido_resultado") or "").strip().lower()
        if result and result != "ok":
            return RobotResult(False, "real", f"RoboDK ejecuto '{self.order_program_name}' pero devolvio {result}")

        detail = f"id={medicine_id} {medicine_type}"
        if position:
            detail += f" en {position}"
        return RobotResult(True, "real", f"RoboDK ejecuto '{program.Name()}' para {detail}")

    def execute_storage(self, medicine_type: str | None, position: str | None, medicine_id: int | None = None) -> RobotResult:
        medicine_type = str(medicine_type or "").strip().lower()
        position = str(position or "").strip()
        medicine_id = _valid_medicine_id(medicine_id) or _medicine_id(medicine_type)

        if self.mode == "sim":
            detail = f"id={medicine_id} {medicine_type}".strip()
            if position:
                detail += f" en {position}"
            return RobotResult(True, "sim", f"Simulacion RoboDK: almacenamiento {detail}")

        try:
            rdk, _item_type_robot, _item_type_program = self._connect()
        except Exception as exc:
            if self.mode == "real":
                return RobotResult(False, "real", f"No se pudo conectar con RoboDK: {exc}")
            return RobotResult(True, "sim", f"RoboDK no disponible; simulando almacenamiento: {exc}")

        program = self._find_program(self.storage_program_name)
        if not program.Valid():
            visible = self._visible_program_names()
            detail = f"No existe el programa de almacenamiento '{self.storage_program_name}' en la estacion"
            if visible:
                detail += f". Programas visibles: {', '.join(visible)}"
            return RobotResult(False, "real", detail)

        rdk.setParam("almacen_tipo_id", medicine_id or 0)
        rdk.setParam("almacen_tipo", medicine_type)
        rdk.setParam("almacen_posicion", position)
        rdk.setParam("almacen_resultado", "")
        rdk.RunProgram(program.Name(), True)

        result = str(rdk.getParam("almacen_resultado") or "").strip().lower()
        if result and result != "ok":
            return RobotResult(False, "real", f"RoboDK ejecuto '{program.Name()}' pero devolvio {result}")

        detail = f"id={medicine_id} {medicine_type}".strip()
        if position:
            detail += f" en {position}"
        return RobotResult(True, "real", f"RoboDK ejecuto '{program.Name()}' para almacenar {detail}")

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

        self._robolink = robolink
        self._rdk = robolink.Robolink()
        self._item_type_robot = robolink.ITEM_TYPE_ROBOT
        self._item_type_program = robolink.ITEM_TYPE_PROGRAM
        return self._rdk, self._item_type_robot, self._item_type_program

    def _find_program(self, name: str):
        rdk, _item_type_robot, item_type_program = self._connect()
        robolink = self._robolink
        names = _program_name_candidates(name)
        item_types = [
            item_type_program,
            getattr(robolink, "ITEM_TYPE_PROGRAM_PYTHON", None),
            None,
        ]

        for candidate in names:
            for item_type in item_types:
                if item_type is None:
                    program = rdk.Item(candidate)
                else:
                    program = rdk.Item(candidate, item_type)
                if program.Valid():
                    return program
        return rdk.Item(names[0])

    def _visible_program_names(self) -> list[str]:
        try:
            rdk, _item_type_robot, item_type_program = self._connect()
            robolink = self._robolink
            program_types = {
                item_type_program,
                getattr(robolink, "ITEM_TYPE_PROGRAM_PYTHON", None),
            }
            return [
                item.Name()
                for item in rdk.ItemList()
                if item.Type() in program_types
            ]
        except Exception:
            return []

    def _target_name(self, position: str) -> str:
        clean = position.replace("-", "_")
        return self.target_template.format(position=position, position_clean=clean)


def _medicine_id(medicine_type: str) -> int | None:
    return MEDICINE_IDS.get(medicine_type.strip().lower())


def _program_name_candidates(name: str) -> list[str]:
    clean = str(name or "").strip()
    if not clean:
        return [DEFAULT_ORDER_PROGRAM_NAME, f"{DEFAULT_ORDER_PROGRAM_NAME}.py"]
    names = [clean]
    if clean.endswith(".py"):
        names.append(clean[:-3])
    else:
        names.append(f"{clean}.py")
    return list(dict.fromkeys(names))


def _valid_medicine_id(value: int | None) -> int | None:
    try:
        medicine_id = int(value)
    except (TypeError, ValueError):
        return None
    return medicine_id if medicine_id in {1, 2, 3} else None
