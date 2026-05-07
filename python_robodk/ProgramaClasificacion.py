from robodk import *
from robolink import *

RDK = Robolink()
robot = RDK.Item('UR3e Base - Clasificación', ITEM_TYPE_ROBOT)

tool = RDK.Item("RobotiQ EPick Vacuum Gripper (1 Cup)", ITEM_TYPE_TOOL)
frame_est = RDK.Item('Sistema - Estantería')

#base = RDK.Item('Estanteria')
#pose_base = base.Pose()


#pose_base = pose_base * transl(0, 0, 280)

#♥ TARGETS

target_Punto_Paso_1 = RDK.Item('Paso', robolink.ITEM_TYPE_TARGET)
target_Punto_Paso_2 = RDK.Item('Target 2', robolink.ITEM_TYPE_TARGET) 
target_Punto_Paso_3 = RDK.Item('Target 3', robolink.ITEM_TYPE_TARGET) 
#target_Pre_Place = RDK.Item('PrePlace', robolink.ITEM_TYPE_TARGET)


target_Place = RDK.Item('Place_base', robolink.ITEM_TYPE_TARGET)
pose_base = target_Place.Pose()


# Parámetros
ancho_caja = 125
fondo_caja = 66
alto_caja = 62.5

gap = 30

dx = ancho_caja + gap
dy = fondo_caja + gap
dz = 215

cols = 3
rows = 2
levels = 3

contador = 0
max_cajas = 20

robot.setPoseFrame(frame_est)
robot.setPoseTool(tool)

for k in range(levels):
    for i in range(rows):
        for j in range(cols):

            if contador >= max_cajas:
                break

            # -------------------
            # PICK
            # -------------------
            # aquí deberías mover al punto de pick
            # o llamar a tu lógica de cinta
            if contador % 2 == 0:
                RDK.RunProgram("Pick1", True)
            else:
                RDK.RunProgram("Pick2", True)
                if contador == 5:
                    RDK.RunProgram("AvanzaPlace", True)
                    RDK.RunProgram("AvanzaPlace", True)
                    RDK.RunProgram("AvanzaPlace", False)
                elif contador == 9:
                    RDK.RunProgram("AvanzaPlace", True)
                    RDK.RunProgram("AvanzaPlace", False)
                elif(contador == 15):
                    RDK.RunProgram("AvanzaPlace", True)
                    RDK.RunProgram("AvanzaPick", False)
                else:
                    RDK.RunProgram("AvanzaPick", False)

            #tool.AttachClosest()   # o caja.AttachTo(tool)

            # -------------------
            # CALCULAR PLACE
            # -------------------
            #offset = transl(
                #j*dx + ancho_caja/2,
                #i*dy + fondo_caja/2,
                #k*dz + alto_caja/2
            #)
            
            if contador <= 5:
                offset = transl(
                    j*dx + ancho_caja/2,
                    -i*dz + fondo_caja,
                    0
                )
            elif contador > 5 and contador <= 11 :
                offset = transl(
                    j*dx + ancho_caja/2,
                    -i*dz,
                    0
                )
            elif contador > 11 and contador <= 17:
                if contador == 16 or contador == 17:
                    offset = transl(
                        j*dx + ancho_caja/2,
                        -i*dz - fondo_caja + 7,
                        0
                    )
                else:
                    offset = transl(
                        j*dx + ancho_caja/2,
                        -i*dz - fondo_caja,
                        0
                    )
            else:
                offset = transl(
                    j*dx + ancho_caja/2,
                    -i*dz + fondo_caja,
                    0
                )
            

            pose_target = pose_base * offset

            robot.setPoseFrame(frame_est)
            robot.setPoseTool(tool)

            # -------------------
            # PLACE
            # -------------------
            robot.MoveJ(target_Punto_Paso_3)

            robot.MoveJ(target_Punto_Paso_2)
            robot.MoveJ(pose_target * robomath.transl([0,-50,0]))
            robot.setSpeed(100,20)
            pause(0.5)
            robot.MoveL(pose_target)

            tool.DetachAll()
            robot.MoveL(pose_target * robomath.transl([0,-50,0]))
            robot.setSpeed(1000,100)
            robot.MoveJ(target_Punto_Paso_2)

            # o mejor:
            # caja.AttachTo(frame_est)

            contador += 1
