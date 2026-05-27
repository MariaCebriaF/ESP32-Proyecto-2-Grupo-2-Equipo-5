from robodk import *
from robolink import *

RDK = Robolink()

robot = RDK.Item('UR3e - pedidos', ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)
frame_est = RDK.Item('Sistema - Estantería')
frame_pedidos = RDK.Item('Frame_pedidos')

t_paso3 = RDK.Item('Paso_ped3', ITEM_TYPE_TARGET)
t_paso4 = RDK.Item('Paso_ped4', ITEM_TYPE_TARGET)
t_paso5 = RDK.Item('Paso_ped5', ITEM_TYPE_TARGET)
t_paso6 = RDK.Item('Paso_ped6', ITEM_TYPE_TARGET)

t_reposo  = RDK.Item('Reposo_pedidos', ITEM_TYPE_TARGET)
t_paso1   = RDK.Item('Paso_ped1', ITEM_TYPE_TARGET)
t_paso2   = RDK.Item('Paso_ped2', ITEM_TYPE_TARGET)
t_preplace = RDK.Item('Pre_pedidos', ITEM_TYPE_TARGET)
t_place = RDK.Item('Place_pedido', ITEM_TYPE_TARGET)

t_pick_ref = RDK.Item('Pick_base_antes', ITEM_TYPE_TARGET)
pose_ref = t_pick_ref.Pose()

robot.setPoseFrame(frame_est)
robot.setPoseTool(tool)

pose_base = RDK.Item('Place_base', ITEM_TYPE_TARGET).Pose()
pose_target = pose_base

# BASE DE DATOS

medicamentos = {
    "ibuprofeno": [],
    "paracetamol": [],
    "enantyum": []
}

alias_medicamentos = {
    "amoxicilina": "enantyum"
}

medicamento_por_id = {
    1: "paracetamol",
    2: "ibuprofeno",
    3: "enantyum"
}


# PARÁMETROS

ancho_caja = 125
fondo_caja = 66
alto_caja = 62.5
gap = 30
dx = ancho_caja + gap
dz = 215
cols = 3
rows = 2
levels = 3
contador = 0
max_cajas = 18

# GENERAR POSICIONES

for k in range(levels):
    for i in range(rows):
        for j in range(cols):
            if contador >= max_cajas:
                break

            if contador <= 5:
                offset = transl(j*dx + ancho_caja/2, -i*dz + fondo_caja, 0)
                if contador == 0 or contador == 3:
                    medicamentos["ibuprofeno"].append(pose_target * offset)
                elif contador <= 2:
                    medicamentos["paracetamol"].append(pose_target * offset)
                else:
                    medicamentos["enantyum"].append(pose_target * offset)

            elif contador <= 11:
                offset = transl(j*dx + ancho_caja/2, -i*dz, 0)
                if contador == 6 or contador == 9:
                    medicamentos["ibuprofeno"].append(pose_target * offset)
                elif contador <= 8:
                    medicamentos["paracetamol"].append(pose_target * offset)
                else:
                    medicamentos["enantyum"].append(pose_target * offset)

            elif contador <= 17:
                if contador == 16 or contador == 17:
                    offset = transl(j*dx + ancho_caja/2, -i*dz - fondo_caja + 7, 0)
                else:
                    offset = transl(j*dx + ancho_caja/2, -i*dz - fondo_caja, 0)
                if contador == 12 or contador == 15:
                    medicamentos["ibuprofeno"].append(pose_target * offset)
                elif contador <= 14:
                    medicamentos["paracetamol"].append(pose_target * offset)
                else:
                    medicamentos["enantyum"].append(pose_target * offset)

            contador += 1

# FUNCIÓN PEDIDO

def pedir_medicamento(tipo):
    tipo = alias_medicamentos.get(tipo, tipo)

    if tipo not in medicamentos or not medicamentos[tipo]:
        print("Sin stock de", tipo)
        RDK.setParam("pedido_resultado", "sin_stock")
        return False

    pose_place_pos = medicamentos[tipo].pop()

    pose_place = Mat(pose_ref)
    pose_place[0,3] = pose_place_pos[0,3]
    pose_place[1,3] = pose_place_pos[1,3]
    pose_place[2,3] = pose_place_pos[2,3]

    pose_up = Mat(pose_place)
    pose_up[1,3] += 100
    pose_pick = Mat(pose_place)
    pose_pick[1,3] += 60

    robot.MoveJ(t_paso3)
    robot.MoveJ(t_paso4)
    robot.MoveJ(t_paso5)
    robot.MoveJ(t_paso6)

    robot.MoveJ(pose_up)
    robot.setSpeed(100, 20)
    pause(0.5)
    robot.MoveL(pose_pick)

    tool.AttachClosest()
    robot.MoveL(pose_up)
    robot.setSpeed(1000, 100)

    robot.MoveJ(t_paso6)
    robot.MoveJ(t_paso5)
    robot.MoveJ(t_paso4)
    robot.MoveJ(t_paso3)

    robot.setPoseFrame(frame_pedidos)
    
    # PLACE
    robot.MoveJ(t_reposo)
    robot.MoveJ(t_paso1)
    robot.MoveJ(t_paso2)

    robot.MoveJ(t_preplace)
    robot.setSpeed(100, 20)
    pause(0.5)
    robot.MoveL(t_place)

    tool.DetachAll()
    robot.MoveL(t_preplace)
    robot.setSpeed(1000, 100)

    robot.MoveJ(t_paso2)
    robot.MoveJ(t_paso1)
    robot.MoveJ(t_reposo)
    RDK.setParam("pedido_resultado", "ok")
    return True

def tipo_desde_parametros():
    pedido_id = RDK.getParam("pedido_id")
    try:
        pedido_id = int(str(pedido_id).strip())
    except (TypeError, ValueError):
        pedido_id = 0

    if pedido_id in medicamento_por_id:
        return medicamento_por_id[pedido_id], pedido_id

    tipo = RDK.getParam("pedido_tipo")
    if tipo is None or tipo == "":
        return "enantyum", 3

    tipo = str(tipo).strip().lower()
    return alias_medicamentos.get(tipo, tipo), 0


#  EJECUTAR

tipo_recibido, id_recibido = tipo_desde_parametros()
print("Medicamento recibido:", tipo_recibido, "id:", id_recibido)

pedir_medicamento(tipo_recibido)
