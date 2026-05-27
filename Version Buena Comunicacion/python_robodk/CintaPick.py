# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()

cinta = RDK.Item('cinta 2')
INCREMENTO_MM = -960    
#caja = RDK.Item('Frame 11')
SR_Cinta = RDK.Item('Frame_despaletizadas')

if cinta.Valid():
    cinta.setSpeed(500)       
    cinta.setAcceleration(100) 
    cinta.MoveJ(cinta.Joints() + INCREMENTO_MM)
