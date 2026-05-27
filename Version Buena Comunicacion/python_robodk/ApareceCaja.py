# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html

from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox

RDK = robolink.Robolink()

cinta = RDK.Item('cinta')
INCREMENTO_MM = -1550
caja_grande = RDK.Item('tinker')
caja_grande.setParam('Collisions', '0')


# Conjunto original (Frame con TODAS las cajitas + tinker)
caja = RDK.Item('Frame 6')
tinker = RDK.Item('Frame_6_Copia')

# Frame de la cinta
SR_Cinta = RDK.Item('Frame 10')

def hacer_visible_recursivo(item):
    item.setVisible(True)
    for hijo in item.Childs():
        hacer_visible_recursivo(hijo)

if cinta.Valid() and caja.Valid():
    # -------------------------------------------------
    # BORRAR COPIAS EXISTENTES EN "Sistema - Estantería"
    # -------------------------------------------------
    estanteria = RDK.Item('Sistema - Estantería')

    if estanteria.Valid():
        hijos = estanteria.Childs()  # copia de la lista
        for item in hijos:
            if item.Valid() and item.Name().startswith('Prism'):
                item.Delete()

    if tinker.Valid():
        tinker.Delete()

    #Copiar una caja
    caja.Copy()
    caja_copia = RDK.Paste()
    caja_copia.setName('Frame_6_Copia')

    # Colocar la copia en el inicio de la cinta
    caja_copia.setParent(SR_Cinta)
    caja_copia.setPose(caja.Pose())
    caja_copia.setVisible(True)

    hacer_visible_recursivo(caja_copia)

