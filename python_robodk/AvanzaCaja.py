# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
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

if cinta.Valid() and caja.Valid():

    # Avanzar Cinta
    cinta.setSpeed(1000)
    cinta.setAcceleration(100)

    joints = cinta.Joints()
    joints[0] += INCREMENTO_MM
    cinta.MoveJ(joints)
