from __future__ import annotations

import os
from dataclasses import dataclass


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
    ) -> None:
        self.mode = mode
        self.robot_name = robot_name
        self.target_template = target_template
        self._rdk = None
        self._item_type_robot = None

    @classmethod
    def from_env(cls) -> "RoboDKClient":
        return cls(
            mode=os.getenv("ROBODK_MODE", "auto").lower(),
            robot_name=os.getenv("ROBODK_ROBOT_NAME", "robot_pedidos"),
            target_template=os.getenv("ROBODK_TARGET_TEMPLATE", "{position}"),
        )

    def move_to_position(self, position: str) -> RobotResult:
        if self.mode == "sim":
            return RobotResult(True, "sim", f"Simulacion RoboDK: mover a {position}")

        try:
            rdk, item_type_robot = self._connect()
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
            return self._rdk, self._item_type_robot

        from robodk import robolink

        self._rdk = robolink.Robolink()
        self._item_type_robot = robolink.ITEM_TYPE_ROBOT
        return self._rdk, self._item_type_robot

    def _target_name(self, position: str) -> str:
        clean = position.replace("-", "_")
        return self.target_template.format(position=position, position_clean=clean)

