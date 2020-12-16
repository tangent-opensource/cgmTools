
import maya.cmds as mc

## add the CGM menu
def init_cgm_toolbox():
    print("+ CGMToolbox init")
    import cgmToolbox
    reload(cgmToolbox)

mc.evalDeferred(init_cgm_toolbox, lp=True)

