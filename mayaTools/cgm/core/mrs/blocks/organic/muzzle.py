"""
------------------------------------------
cgm.core.mrs.blocks.organic.lowerFace
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

================================================================
"""
# From Python =============================================================
import copy
import re
import pprint
import time
import os

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
import Red9.core.Red9_AnimationUtils as r9Anim
#r9Meta.cleanCache()#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< TEMP!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


import cgm.core.cgm_General as cgmGEN
from cgm.core.rigger import ModuleShapeCaster as mShapeCast

import cgm.core.cgmPy.os_Utils as cgmOS
import cgm.core.cgmPy.path_Utils as cgmPATH
import cgm.core.mrs.assets as MRSASSETS
path_assets = cgmPATH.Path(MRSASSETS.__file__).up().asFriendly()

import cgm.core.mrs.lib.ModuleControlFactory as MODULECONTROL
reload(MODULECONTROL)
from cgm.core.lib import curve_Utils as CURVES
import cgm.core.lib.rigging_utils as CORERIG
from cgm.core.lib import snap_utils as SNAP
import cgm.core.lib.attribute_utils as ATTR
import cgm.core.rig.joint_utils as JOINT
import cgm.core.classes.NodeFactory as NODEFACTORY
import cgm.core.lib.transform_utils as TRANS
import cgm.core.lib.distance_utils as DIST
import cgm.core.lib.position_utils as POS
import cgm.core.lib.math_utils as MATH
import cgm.core.rig.constraint_utils as RIGCONSTRAINT
import cgm.core.rig.general_utils as RIGGEN
import cgm.core.lib.constraint_utils as CONSTRAINT
import cgm.core.lib.locator_utils as LOC
import cgm.core.lib.rayCaster as RAYS
import cgm.core.lib.shape_utils as SHAPES
import cgm.core.mrs.lib.block_utils as BLOCKUTILS
import cgm.core.mrs.lib.builder_utils as BUILDERUTILS
import cgm.core.mrs.lib.shared_dat as BLOCKSHARE
import cgm.core.tools.lib.snap_calls as SNAPCALLS
import cgm.core.rig.ik_utils as IK
import cgm.core.cgm_RigMeta as cgmRIGMETA
import cgm.core.lib.nameTools as NAMETOOLS
import cgm.core.cgmPy.validateArgs as VALID

for m in DIST,POS,MATH,IK,CONSTRAINT,LOC,BLOCKUTILS,BUILDERUTILS,CORERIG,RAYS,JOINT,RIGCONSTRAINT,RIGGEN:
    reload(m)
    
# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta

#=============================================================================================================
#>> Block Settings
#=============================================================================================================
__version__ = 'alpha.10.31.2018'
__autoTemplate__ = False
__menuVisible__ = True

#These are our base dimensions. In this case it is for human
__dimensions_by_type = {'box':[22,22,22],
                        'human':[15.2, 23.2, 19.7]}

__l_rigBuildOrder__ = ['rig_dataBuffer',
                       'rig_skeleton',
                       'rig_shapes',
                       'rig_controls',
                       'rig_frame',
                       'rig_cleanUp']




d_wiring_skeleton = {'msgLinks':[],
                     'msgLists':['moduleJoints','skinJoints']}
d_wiring_prerig = {'msgLinks':['moduleTarget','prerigNull','noTransPrerigNull']}
d_wiring_template = {'msgLinks':['templateNull','noTransTemplateNull'],
                     }
d_wiring_extraDags = {'msgLinks':['bbHelper'],
                      'msgLists':[]}
#>>>Profiles ==============================================================================================
d_build_profiles = {}


d_block_profiles = {'default':{},
                    'jawOnly':{'baseSize':[17.6,7.2,8.4],
                               'faceType':'default',
                               'muzzleSetup':'simple',
                               'noseSetup':'none',
                               'jawSetup':'simple',
                               'lipSetup':'none',
                               'teethSetup':'none',
                               'cheekSetup':'none',
                               'tongueSetup':'none',
                               'uprJaw':False,
                               'chinSetup':'none',
                               },
                    }
"""
'eyebrow':{'baseSize':[17.6,7.2,8.4],
           'browType':'full',
           'profileOptions':{},
           'paramStart':.2,
            'paramMid':.5,
            'paramEnd':.7,                               
           },"""
#>>>Attrs =================================================================================================
l_attrsStandard = ['side',
                   'position',
                   'baseAim',
                   'baseDat',
                   'attachPoint',
                   'nameList',
                   'loftDegree',
                   'loftSplit',
                   'scaleSetup',
                   'moduleTarget',]

d_attrsToMake = {'faceType':'default:muzzle:beak',
                 'muzzleSetup':'none:simple',
                 'noseSetup':'none:simple',
                 'jawSetup':'none:simple:slide',
                 'lipSetup':'none:default',
                 'teethSetup':'none:oneJoint:twoJoint',
                 'cheekSetup':'none:single',
                 'tongueSetup':'none:single:ribbon',
                 #Jaw...
                 'uprJawSetup':'none:default',
                 'chinSetup':'none:default',
                 #Nose...
                 'nostrilSetup':'none:default',
                 'bridgeSetup':'none:default',
                 'numJointsNostril':'int',
                 'numJointsNoseTip':'int',
                 #Lips...
                 'lipSealSetup':'none:default',
                 'numJointsLipUpr':'int',
                 'numJointsLipLwr':'int',
                 'paramUprStart':'float',
                 'paramLwrStart':'float',
                 #'lipCorners':'bool',
                 #Tongue...
                 'numJointsTongue':'int',
                 }

d_defaultSettings = {'version':__version__,
                     'attachPoint':'end',
                     'side':'none',
                     'loftDegree':'cubic',
                     'numJointsLipUpr':3,
                     'numJointsLipLwr':3,
                     'numJointsNoseTip':1,
                     'numJointsNostril':1,
                     'paramUprStart':.15,
                     'paramLwrStart':.15,
                     'numJointsTongue':3,
                     #'baseSize':MATH.get_space_value(__dimensions[1]),
                     }

#=============================================================================================================
#>> Define
#=============================================================================================================
def mirror_self(self,primeAxis = 'Left'):
    _str_func = 'mirror_self'
    _idx_state = self.getState(False)
    
    log.debug("|{0}| >> define...".format(_str_func)+ '-'*80)
    ml_mirrorHandles = self.msgList_get('defineSubHandles')
    r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                             mode = '',primeAxis = primeAxis.capitalize() )    
    
    if _idx_state > 0:
        log.debug("|{0}| >> template...".format(_str_func)+ '-'*80)
        ml_mirrorHandles = self.msgList_get('templateHandles')
        r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                                     mode = '',primeAxis = primeAxis.capitalize() )
    
    if _idx_state > 1:
        log.debug("|{0}| >> prerig...".format(_str_func)+ '-'*80)        
        ml_mirrorHandles = self.msgList_get('prerigHandles') + self.msgList_get('jointHandles')
        r9Anim.MirrorHierarchy().makeSymmetrical([mObj.mNode for mObj in ml_mirrorHandles],
                                                 mode = '',primeAxis = primeAxis.capitalize() )       

@cgmGEN.Timer
def define(self):
    _str_func = 'define'    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    _short = self.mNode
    
    #Attributes =========================================================
    ATTR.set_alias(_short,'sy','blockScale')    
    self.setAttrFlags(attrs=['sx','sz','sz'])
    self.doConnectOut('sy',['sx','sz'])

    ATTR.set_min(_short, 'loftSplit', 1)
    ATTR.set_min(_short, 'paramUprStart', 0.0)
    ATTR.set_min(_short, 'paramLwrStart', 0.0)
    
    
    #Buffer our values...
    _str_faceType = self.getEnumValueString('faceType')
    _str_muzzleSetup = self.getEnumValueString('muzzleSetup')
    _str_noseSetup = self.getEnumValueString('noseSetup')
    _str_uprJawSetup = self.getEnumValueString('uprJawSetup')    
    _str_lipsSetup = self.getEnumValueString('lipsSetup')
    _str_teethSetup = self.getEnumValueString('teethSetup')
    _str_cheekSetup = self.getEnumValueString('cheekSetup')
    _str_tongueSetup = self.getEnumValueString('tongueSetup')
    

    #Cleaning =========================================================        
    _shapes = self.getShapes()
    if _shapes:
        log.debug("|{0}| >>  Removing old shapes...".format(_str_func))        
        mc.delete(_shapes)
        defineNull = self.getMessage('defineNull')
        if defineNull:
            log.debug("|{0}| >>  Removing old defineNull...".format(_str_func))
            mc.delete(defineNull)
    ml_handles = []
    
    mNoTransformNull = self.getMessageAsMeta('noTransDefineNull')
    if mNoTransformNull:
        mNoTransformNull.delete()
    
    #rigBlock Handle ===========================================================
    log.debug("|{0}| >>  RigBlock Handle...".format(_str_func))            
    _size = MATH.average(self.baseSize[1:])
    _crv = CURVES.create_fromName(name='locatorForm',#'axis3d',#'arrowsAxis', 
                                  direction = 'z+', size = _size/4)
    SNAP.go(_crv,self.mNode,)
    CORERIG.override_color(_crv, 'white')        
    CORERIG.shapeParent_in_place(self.mNode,_crv,False)
    mHandleFactory = self.asHandleFactory()
    self.addAttr('cgmColorLock',True,lock=True, hidden=True)
    mDefineNull = self.atUtils('stateNull_verify','define')
    mNoTransformNull = self.atUtils('noTransformNull_verify','define')
    
    #Bounding sphere ==================================================================
    _bb_shape = CURVES.create_controlCurve(self.mNode,'cubeOpen', size = 1.0, sizeMode='fixed')
    mBBShape = cgmMeta.validateObjArg(_bb_shape, 'cgmObject',setClass=True)
    mBBShape.p_parent = mDefineNull    
    mBBShape.tz = -.5
    mBBShape.ty = -.5
    
    
    CORERIG.copy_pivot(mBBShape.mNode,self.mNode)
    mHandleFactory.color(mBBShape.mNode,controlType='sub')
    mBBShape.setAttrFlags()
    
    mBBShape.doStore('cgmName', self.mNode)
    mBBShape.doStore('cgmType','bbVisualize')
    mBBShape.doName()    
    
    self.connectChildNode(mBBShape.mNode,'bbHelper')
    self.doConnectOut('baseSize', "{0}.scale".format(mBBShape.mNode))
    
    
    #Make our handles creation data =======================================================
    d_pairs = {}
    d_creation = {}
    l_order = []
    d_curves = {}
    d_curveCreation = {}
    
    
    #Jaw ---------------------------------------------------------------------
    if self.jawSetup:
        log.debug("|{0}| >>  Jaw setup...".format(_str_func))
        _str_jawSetup = self.getEnumValueString('jawSetup')
        
        _d_pairs = {'jawLeft':'jawRight',
                    'jawTopLeft':'jawTopRight',
                    'chinLeft':'chinRight',
                    'cheekBoneLeft':'cheekBoneRight',
                    }
        d_pairs.update(_d_pairs)
    
        _d = {'jawLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':True,
                            'vectorLine':False,'scaleSpace':[.75,-.5,-1]},
              'jawRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':True,
                             'vectorLine':False,'scaleSpace':[-.75,-.5,-1]},
              'jawTopLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':False,
                            #'defaults':{'tx':-1},
                             'vectorLine':False,'scaleSpace':[1,.9,-1]},
              'jawTopRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':0,
                             #'defaults':{'tx':1},                             
                              'vectorLine':False,'scaleSpace':[-1,.9,-1]},              
              'chinLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':0,
                          'scaleSpace':[.25,-1,1]},
              'chinRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':0,
                          'scaleSpace':[-.25,-1,1]},
              #'chin':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':1,
              #              'vectorLine':False,'scaleSpace':[0,-1,1]},
              'cheekBoneLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':0,
                               'vectorLine':False,'scaleSpace':[.7,.4,.5]},
              'cheekBoneRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':0,
                                'vectorLine':False,'scaleSpace':[-.7,.4,.5]},
              }
        
        d_creation.update(_d)
        l_order.extend(['jawLeft','jawRight','chinLeft','chinRight',
                        'jawTopLeft','jawTopRight','cheekBoneLeft','cheekBoneRight'])
        
        _d_curveCreation = {'jawLine':{'keys':['jawTopLeft','jawLeft','chinLeft',
                                               'chinRight','jawRight','jawTopRight'],
                                       'rebuild':False},
                            'cheekLineLeft':{'keys':['jawTopLeft','cheekBoneLeft'],
                                       'rebuild':False},
                            'cheekLineRight':{'keys':['jawTopRight','cheekBoneRight'],
                                             'rebuild':False},
                            'smileLineLeft':{'keys':['cheekBoneLeft','chinLeft'],
                                             'rebuild':False},
                            'smileLineRight':{'keys':['cheekBoneRight','chinRight'],
                                              'rebuild':False},                            
                            }
        
        if self.noseSetup:
            _d_curveCreation['cheekLineLeft']['keys'].append('sneerLeft')
            _d_curveCreation['cheekLineRight']['keys'].append('sneerRight')
            
        d_curveCreation.update(_d_curveCreation)
        
    #lip ---------------------------------------------------------------------
    if self.lipSetup:
        log.debug("|{0}| >>  lip setup...".format(_str_func))
        _str_jawSetup = self.getEnumValueString('lipSetup')
        
        _d_pairs = {'mouthLeft':'mouthRight',
                    }
        d_pairs.update(_d_pairs)
    
        _d = {'mouthLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':True,
                            'vectorLine':False,'scaleSpace':[.4,-.2,1],
                            'defaults':{'tz':.5}},
              'mouthCenter':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':False,
                             'vectorLine':False,'scaleSpace':[0,-.2,1],
                             'defaults':{'tz':1}},
              'mouthRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':True,
                             'vectorLine':False,'scaleSpace':[-.4,-.2,1],
                             'defaults':{'tz':.5}},
              }
        d_creation.update(_d)
        l_order.extend(['mouthLeft','mouthRight','mouthCenter'])
        
        _d_curveCreation = {'lip':{'keys':['mouthLeft','mouthCenter','mouthRight'],
                                   'rebuild':True}}
        d_curveCreation.update(_d_curveCreation)
        
    #Cheek ---------------------------------------------------------------------
    if self.cheekSetup:
        log.debug("|{0}| >>  cheek setup...".format(_str_func))
        _str_jawSetup = self.getEnumValueString('cheekSetup')
        
        """
        _d_pairs = {'cheekLeft':'cheekRight',
                    }
        d_pairs.update(_d_pairs)
    
        _d = {'cheekLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':True,
                            'vectorLine':False,'scaleSpace':[1,-.1,.5]},
              'cheekRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':True,
                             'vectorLine':False,'scaleSpace':[-1,-.1,.5]},
              }
        d_creation.update(_d)
        l_order.extend(['cheekLeft','cheekRight'])"""


    #nose ---------------------------------------------------------------------
    if self.noseSetup:
        log.debug("|{0}| >>  nose setup...".format(_str_func))
        _str_jawSetup = self.getEnumValueString('noseSetup')
        
        _d_pairs = {'noseLeft':'noseRight',
                    'sneerLeft':'sneerRight',
                    }
        d_pairs.update(_d_pairs)
    
        _d = {'noseTip':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':False,
                         'vectorLine':False,'scaleSpace':[0,.5,1],
                         'defaults':{'tz':2}},
              'noseBase':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':False,
                         'vectorLine':False,'scaleSpace':[0,.2,1],
                         'defaults':{'tz':1}},
              #'bridgeHelp':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':False,
              #            'vectorLine':False,'scaleSpace':[0,.7,1],
              #            'defaults':{'tz':1}},
              'bridge':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':0,
                         'vectorLine':False,'scaleSpace':[0,.9,1],
                         'defaults':{'tz':.25}},              
              'noseLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':True,
                            'vectorLine':False,'scaleSpace':[.4,.3,1],
                            'defaults':{'tz':.1}},
              'noseRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':True,
                             'vectorLine':False,'scaleSpace':[-.4,.3,1],
                             'defaults':{'tz':.1}},
              'sneerLeft':{'color':'blueBright','tagOnly':True,'arrow':False,'jointLabel':True,
                          'vectorLine':False,'scaleSpace':[.2,.8,.75],
                          },
              'sneerRight':{'color':'redBright','tagOnly':True,'arrow':False,'jointLabel':True,
                           'vectorLine':False,'scaleSpace':[-.2,.8,.75],
                           },              
              }
        d_creation.update(_d)
        l_order.extend(['noseLeft','noseRight',
                        'sneerLeft','sneerRight',
                        'noseTip','noseBase','bridge'])
        

        _d_curveCreation = {'noseProfile':{'keys':['bridge','noseTip','noseBase'],
                                   'rebuild':False},
                            'noseCross':{'keys':['noseRight','noseTip','noseLeft'],
                                           'rebuild':False},
                            'noseRight':{'keys':['sneerRight','noseRight'],
                                         'rebuild':False},
                            'noseLeft':{'keys':['sneerLeft','noseLeft'],
                                         'rebuild':False},                            
                            'noseUnder':{'keys':['noseRight','noseBase','noseLeft'],
                                           'rebuild':False},
                            'bridgeTop':{'keys':['sneerRight','bridge','sneerLeft'],
                                         'rebuild':False},
                            }
        d_curveCreation.update(_d_curveCreation)        
        
    
    #make em...
    log.debug("|{0}| >>  Make the handles...".format(_str_func))    
    md_res = self.UTILS.create_defineHandles(self, l_order, d_creation, _size / 10, mDefineNull, mBBShape)

    md_handles = md_res['md_handles']
    ml_handles = md_res['ml_handles']

    idx_ctr = 0
    idx_side = 0
    d = {}
    
    for tag,mHandle in md_handles.iteritems():
        mHandle._verifyMirrorable()
        _center = True
        for p1,p2 in d_pairs.iteritems():
            if p1 == tag or p2 == tag:
                _center = False
                break
        if _center:
            log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
            mHandle.mirrorSide = 0
            mHandle.mirrorIndex = idx_ctr
            idx_ctr +=1
        mHandle.mirrorAxis = "translateX,rotateY,rotateZ"

    #Self mirror wiring -------------------------------------------------------
    for k,m in d_pairs.iteritems():
        md_handles[k].mirrorSide = 1
        md_handles[m].mirrorSide = 2
        md_handles[k].mirrorIndex = idx_side
        md_handles[m].mirrorIndex = idx_side
        md_handles[k].doStore('mirrorHandle',md_handles[m].mNode)
        md_handles[m].doStore('mirrorHandle',md_handles[k].mNode)
        idx_side +=1

    #Curves -------------------------------------------------------------------------
    log.debug("|{0}| >>  Make the curves...".format(_str_func))    
    md_resCurves = self.UTILS.create_defineCurve(self, d_curveCreation, md_handles, mNoTransformNull)
    self.msgList_connect('defineHandles',ml_handles)#Connect    
    self.msgList_connect('defineSubHandles',ml_handles)#Connect
    self.msgList_connect('defineCurves',md_resCurves['ml_curves'])#Connect
    
    return


#=============================================================================================================
#>> Template
#=============================================================================================================
def templateDelete(self):
    _str_func = 'templateDelete'
    log.debug("|{0}| >> ...".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    ml_defSubHandles = self.msgList_get('defineSubHandles')
    for mObj in ml_defSubHandles:
        mObj.template = False    
            
    try:self.defineLoftMesh.template = False
    except:pass
    self.bbHelper.v = True
    
    for mObj in self.msgList_get('defineCurves'):
        mObj.template=0
        mObj.v=1
    
    
@cgmGEN.Timer
def template(self):
    try:    
        _str_func = 'template'
        log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
        log.debug("{0}".format(self))
        
        _short = self.p_nameShort
        #_baseNameAttrs = ATTR.datList_getAttrs(self.mNode,'nameList')
        
        #Initial checks ===============================================================================
        log.debug("|{0}| >> Initial checks...".format(_str_func)+ '-'*40)    

        #Create temple Null  ==================================================================================
        mTemplateNull = BLOCKUTILS.templateNull_verify(self)
        mNoTransformNull = self.atUtils('noTransformNull_verify','template')
        
        mHandleFactory = self.asHandleFactory()
        
        self.bbHelper.v = False
        _size = MATH.average(self.baseSize[1:])        
        
        #Gather all our define dhandles and curves -----------------------------
        log.debug("|{0}| >> Get our define curves/handles...".format(_str_func)+ '-'*40)    

        md_handles = {}
        md_dCurves = {}
        d_pos = {}
        
        ml_defineHandles = self.msgList_get('defineSubHandles')
        for mObj in ml_defineHandles:
            md_handles[mObj.handleTag] = mObj
            d_pos[mObj.handleTag] = mObj.p_position
            
        for mObj in self.msgList_get('defineCurves'):
            md_dCurves[mObj.handleTag] = mObj
            mObj.template=1
        pprint.pprint(vars())
        
        #
        d_pairs = {}
        d_creation = {}
        l_order = []
        d_curveCreation = {}
        ml_subHandles = []
        md_loftCreation = {}
        
        DGETAVG = DIST.get_average_position
        CRVPCT = CURVES.getPercentPointOnCurve
        
        pSmileR = False
        pSmileL = False
        
        #Main setup -----------------------------------------------------
        if self.jawSetup:
            log.debug("|{0}| >>  Jaw setup...".format(_str_func))
            _str_jawSetup = self.getEnumValueString('jawSetup')
        
            _d_pairs = {'jawLineLeftMid':'jawLineRightMid',
                        'jawEdgeLeftMid':'jawEdgeRightMid',
                        'cheekLineLeftMid':'cheekLineRightMid',
                        'cheekLeft':'cheekRight',
                        }
            
            pMidChinR = DIST.get_average_position([md_handles['jawRight'].p_position,
                                                   md_handles['chinRight'].p_position])
            pMidChinL = DIST.get_average_position([md_handles['jawLeft'].p_position,
                                                   md_handles['chinLeft'].p_position])
            
            pMidJawR = DIST.get_average_position([md_handles['jawRight'].p_position,
                                                   md_handles['jawTopRight'].p_position])
            pMidJawL = DIST.get_average_position([md_handles['jawLeft'].p_position,
                                                   md_handles['jawTopLeft'].p_position])
            
            pMidCheekR = DIST.get_average_position([md_handles['cheekBoneRight'].p_position,
                                                  md_handles['jawTopRight'].p_position])
            pMidCheekL = DIST.get_average_position([md_handles['cheekBoneLeft'].p_position,
                                                  md_handles['jawTopLeft'].p_position])
            
            pNeckBase = DIST.get_average_position([md_handles['jawLeft'].p_position,
                                                      md_handles['jawRight'].p_position])
            
            pChin = DGETAVG([md_handles['chinLeft'].p_position,
                             md_handles['chinRight'].p_position])
            pJawUnder = DIST.get_average_position([pNeckBase,
                                                  pChin])
            
            pCheekL =  DIST.get_average_position([md_handles['cheekBoneLeft'].p_position,
                                                   md_handles['jawLeft'].p_position])
            pCheekR =  DIST.get_average_position([md_handles['cheekBoneRight'].p_position,
                                                  md_handles['jawRight'].p_position])            

            l_order.extend(['jawLineLeftMid','jawLineRightMid',
                            'cheekLineLeftMid','cheekLineRightMid',
                            'jawEdgeLeftMid','jawEdgeRightMid',
                            'cheekLeft','cheekRight',
                            'neckBase','jawUnder','chin'])
            
            _d = {'jawLineLeftMid':{'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                             'vectorLine':False,'pos':pMidChinL},
                  'jawLineRightMid':{'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                              'vectorLine':False,'pos':pMidChinR},
                  'jawEdgeLeftMid':{'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                                    'vectorLine':False,'pos':pMidJawL},
                  'jawEdgeRightMid':{'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                     'vectorLine':False,'pos':pMidJawR},
                  'cheekLineLeftMid':{'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                                    'vectorLine':False,'pos':pMidCheekL},
                  'cheekLineRightMid':{'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                     'vectorLine':False,'pos':pMidCheekR},
                  'jawUnder':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':0,
                              'vectorLine':False,'pos':pJawUnder},
                  'neckBase':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':0,
                              'vectorLine':False,'pos':pNeckBase},
                  'cheekLeft':{'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                                      'vectorLine':False,'pos':pCheekL},
                  'cheekRight':{'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                       'vectorLine':False,'pos':pCheekR},                  
                  'chin':{'color':'yellowBright','tagOnly':True,'arrow':False,'jointLabel':0,
                          'vectorLine':False,'pos':pChin},                  
                  }
            
            if self.lipSetup:
                pSmileR = DIST.get_average_position([md_handles['cheekBoneRight'].p_position,
                                                        md_handles['chinRight'].p_position])
                pSmileL = DIST.get_average_position([md_handles['cheekBoneLeft'].p_position,
                                                            md_handles['chinLeft'].p_position])
                _d['smileLeft'] = {'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                                   'vectorLine':False,'pos':pSmileL}
                _d['smileRight'] = {'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                   'vectorLine':False,'pos':pSmileR}
                
                l_order.extend(['smileLeft','smileRight'])
                _d_pairs['smileLeft']='smileRight'
        
            d_creation.update(_d)
            d_pairs.update(_d_pairs)
            
            _d_curveCreation = {'jawTemplate1':{'keys':['jawTopRight','jawEdgeRightMid','jawRight','neckBase',
                                                        'jawLeft','jawEdgeLeftMid','jawTopLeft'],
                                                'rebuild':True},
                                'jawTemplate2':{'keys':['cheekLineRightMid','cheekRight','jawLineRightMid',
                                                        'jawUnder',
                                                        'jawLineLeftMid','cheekLeft','cheekLineLeftMid'],
                                                'rebuild':True},
                                'jawTemplate3':{'keys':['cheekBoneRight','smileRight','chinRight','chin',
                                                        'chinLeft','smileLeft','cheekBoneLeft'],
                                                'rebuild':True},
                                }
            

            
            """_d_curveCreation = {'jawTemplate1':{'keys':['jawTopLeft','jawEdgeLeftMid','jawLeft','neckBase',
                                                        'jawRight','jawEdgeRightMid','jawTopRight'],
                                                    'rebuild':True},
                                'jawTemplate2':{'keys':['cheekLineLeftMid','cheekLeft','jawLineLeftMid',
                                                        'jawUnder',
                                                        'jawLineRightMid','cheekRight','cheekLineRightMid'],
                                                    'rebuild':True},
                                'jawTemplate3':{'keys':['cheekBoneLeft','smileLeft','chinLeft','chin',
                                                        'chinRight','smileRight','cheekBoneRight'],
                                                    'rebuild':True},
                                }
            """
            """
            _d_curveCreation = {'jawTemplateLeft1':{'keys':['jawTopLeft','cheekLineLeftMid','cheekBoneLeft'],
                                                    'rebuild':0},
                                'jawTemplateLeft2':{'keys':['jawEdgeLeftMid','cheekLeft','smileLeft'],
                                                    'rebuild':0},
                                'jawTemplateLeft3':{'keys':['jawLeft','jawLineLeftMid','chinLeft'],
                                                    'rebuild':0},
                                'neckTemplate':{'keys':['neckBase','jawUnder','chin'],
                                                'rebuild':0},                                
                                'jawTemplateRight1':{'keys':['jawTopRight','cheekLineRightMid','cheekBoneRight'],
                                                    'rebuild':0},
                                'jawTemplateRight2':{'keys':['jawEdgeRightMid','cheekRight','smileRight'],
                                                    'rebuild':0},
                                'jawTemplateRight3':{'keys':['jawRight','jawLineRightMid','chinRight'],
                                                    'rebuild':0},                                
                                }"""
            
            """
            _d_curveCreation = {'jawTemplateLeft1':{'keys':['jawTopLeft','jawEdgeLeftMid','jawLeft'],
                                                    'rebuild':True},
                                'jawTemplateLeft2':{'keys':['cheekLineLeftMid','cheekLeft','jawLineLeftMid'],
                                                    'rebuild':True},
                                'jawTemplateLeft3':{'keys':['cheekBoneLeft','smileLeft','chinLeft'],
                                                    'rebuild':True},
                                'jawTemplateRight1':{'keys':['jawTopRight','jawEdgeRightMid','jawRight'],
                                                    'rebuild':True},
                                'jawTemplateRight2':{'keys':['cheekLineRightMid','cheekRight','jawLineRightMid'],
                                                    'rebuild':True},
                                'jawTemplateRight3':{'keys':['cheekBoneRight','smileRight','chinRight'],
                                                    'rebuild':True},                                
                                }"""
            
            d_curveCreation.update(_d_curveCreation)
            md_loftCreation['jaw'] = ['jawTemplate1','jawTemplate2','jawTemplate3',]
            
            
        if self.noseSetup:
            log.debug("|{0}| >>  nose setup...".format(_str_func))
            _str_noseSetup = self.getEnumValueString('nose')
            _d_pairs = {}
            
            for k in ['edgeOrbTop','smileUpr',
                      'bridgePlane','bridgeBase',
                      'sneerLow','bridgeStartBase','bridgeStartPlane',
                      'nostrilBase','nostrilTop','bulbTopBase','bulbTopPlane',
                      'nostrilFront',
                      'bulbBase','bulbPlane',
                      'bulbUnder',
                      'nostrilUnderEdge','nostrilUnderInner','nostrilUnderFront',
                      ]:
                _d_pairs[k+'Left'] = k+'Right'
                
            """
            _d_pairs = {'eyeOrbTopRight':'eyeOrbTopLeft',
                        'smileUprRight':'smileUprLeft',
                        
                        'bridgePlaneRight':'bridgePlaneLeft',
                        'bridgeBaseRight':'bridgeBaseLeft',
                        
                        'sneerLowRight':'sneerLowLeft',
                        'bridgeStartBaseRight':'bridgeStartBaseLeft',
                        'bridgeStartPlaneRight':'bridgeStartPlaneLeft',
                        
                        'nostrilBaseRight':'nostrilBaseLeft',
                        'bulbTopBaseRight':'bulbTopBaseLeft',
                        'bulbTopPlaneRight':'bulbTopPlaneLeft',
                        
                        'nostrilUnderEdgeRight':'nostrilUnderEdgeLeft',
                        'nostrilUnderInnerRight':'nostrilUnderInnerLeft'
                        }"""
            
            l_order.extend(['bulbTopCenter','bridgeStartCenter','bulbUnderCenter'])
            
            
            _d_pos = {'edgeOrbTopLeft':DGETAVG([md_handles['cheekBoneLeft'].p_position,
                                                   md_handles['sneerLeft'].p_position]),
                      'edgeOrbTopRight':DGETAVG([md_handles['cheekBoneRight'].p_position,
                                                md_handles['sneerRight'].p_position]),
                      'smileUprLeft':DGETAVG([pSmileL,
                                              md_handles['cheekBoneLeft'].p_position,
                                              md_handles['noseLeft'].p_position]),
                      'smileUprRight':DGETAVG([pSmileR,
                                               md_handles['cheekBoneRight'].p_position,
                                               md_handles['noseRight'].p_position]),
                      
                      'bridgePlaneRight':CRVPCT(md_dCurves['bridgeTop'].mNode,.3),
                      'bridgePlaneLeft':CRVPCT(md_dCurves['bridgeTop'].mNode,.7),
                      'bridgeBaseRight':CRVPCT(md_dCurves['bridgeTop'].mNode,.15),
                      'bridgeBaseLeft':CRVPCT(md_dCurves['bridgeTop'].mNode,.85),
                      
                      'nostrilUnderEdgeRight':CRVPCT(md_dCurves['noseUnder'].mNode,.15),
                      'nostrilUnderEdgeLeft':CRVPCT(md_dCurves['noseUnder'].mNode,.85),
                      'nostrilUnderInnerRight':CRVPCT(md_dCurves['noseUnder'].mNode,.4),
                      'nostrilUnderInnerLeft':CRVPCT(md_dCurves['noseUnder'].mNode,.6),
                      
                      'sneerLowRight':CRVPCT(md_dCurves['noseRight'].mNode,.5),
                      'sneerLowLeft':CRVPCT(md_dCurves['noseLeft'].mNode,.5),
                      
                      
                      'nostrilBaseRight':CRVPCT(md_dCurves['noseRight'].mNode,.8),
                      'nostrilBaseLeft':CRVPCT(md_dCurves['noseLeft'].mNode,.8),
                      
                      'bulbTopCenter':CRVPCT(md_dCurves['noseProfile'].mNode,.35),
                      'bridgeStartCenter':CRVPCT(md_dCurves['noseProfile'].mNode,.2),
                      'bulbUnderCenter':CRVPCT(md_dCurves['noseProfile'].mNode,.8),
                      }
            
            _d = {'bulbTopCenter':{'color':'yellowWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                   'vectorLine':False,
                                   'pos':_d_pos['bulbTopCenter'],
                                   },
                  'bridgeStartCenter':{'color':'yellowWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                       'vectorLine':False,
                                       'pos':_d_pos['bridgeStartCenter'],
                                       },
                  'bulbUnderCenter':{'color':'yellowWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                                     'vectorLine':False,
                                     'pos':_d_pos['bulbUnderCenter'],
                                     },
                  }            
            
            #We need to subprocess a few more points of data and push them back to to our _d_pos
            #curve pos points, name of handle, percent on that curve
            _d_split = {'noseBridge':{'l_pos':[_d_pos['sneerLowRight'],
                                               _d_pos['bridgeStartCenter'],
                                               _d_pos['sneerLowLeft'],
                                               ],
                                      'handles':{'bridgeStartBaseRight':.15,
                                                 'bridgeStartPlaneRight':.35,
                                                 'bridgeStartPlaneLeft':.65,
                                                 'bridgeStartBaseLeft':.85}},
                        'noseBulbTop':{'l_pos':[_d_pos['nostrilBaseRight'],
                                               _d_pos['bulbTopCenter'],
                                               _d_pos['nostrilBaseLeft'],
                                               ],
                                      'handles':{'nostrilTopRight':.1,
                                                 'bulbTopBaseRight':.2,
                                                 'bulbTopPlaneRight':.35,
                                                 'bulbTopPlaneLeft':.65,
                                                 'bulbTopBaseLeft':.8,
                                                 'nostrilTopLeft':.9,}},
                        'bulb':{'l_pos':[d_pos['noseRight'],
                                         d_pos['noseTip'],
                                         d_pos['noseLeft'],
                                                ],
                                'handles':{'nostrilFrontRight':.1,
                                           'bulbBaseRight':.2,
                                           'bulbPlaneRight':.35,
                                           'bulbPlaneLeft':.65,
                                           'bulbBaseLeft':.8,
                                           'nostrilFrontLeft':.9}},
                        'bulbUnder':{'l_pos':[_d_pos['nostrilUnderEdgeRight'],
                                              _d_pos['bulbUnderCenter'],
                                              _d_pos['nostrilUnderEdgeLeft'],
                                              ],
                                'handles':{'nostrilUnderFrontRight':.15,
                                           'bulbUnderRight':.3,
                                           'bulbUnderLeft':.7,
                                           'nostrilUnderFrontLeft':.85,}}
                        }
            
            for k,dTmp in _d_split.iteritems():
                #Make our new curve
                _crv = CORERIG.create_at(create='curve',l_pos= dTmp['l_pos'])
                for h,v in dTmp['handles'].iteritems():
                    _d_pos[h] = CRVPCT(_crv,v)
                mc.delete(_crv)

            for k,v in _d_pairs.iteritems():
                l_order.extend([k,v])
                p_k = _d_pos.get(k)
                p_v = _d_pos.get(v)
                
                if p_k:
                    _d[k] = {'color':'blueSky','tagOnly':True,'arrow':False,'jointLabel':0,
                             'vectorLine':False,
                             'pos':p_k}
                if p_v:
                    _d[v] = {'color':'redWhite','tagOnly':True,'arrow':False,'jointLabel':0,
                             'vectorLine':False,
                             'pos':p_v}

            d_creation.update(_d)
            d_pairs.update(_d_pairs)
            
            #Curve declarations.....
            d_curveCreation['bridgeTop'] = {'keys':['sneerRight',
                                                        'bridgeBaseRight',
                                                        'bridgePlaneRight',
                                                        'bridge',
                                                        'bridgePlaneLeft',
                                                        'bridgeBaseLeft',
                                                        'sneerLeft'],
                                                'rebuild':1}
            d_curveCreation['bridgeStart'] = {'keys':['sneerLowRight',
                                                          'bridgeStartBaseRight',
                                                          'bridgeStartPlaneRight',
                                                          'bridgeStartCenter',
                                                          'bridgeStartPlaneLeft',
                                                          'bridgeStartBaseLeft',
                                                          'sneerLowLeft'],
                                                  'rebuild':1}
            d_curveCreation['bulbTop'] = {'keys':['nostrilBaseRight',
                                                  'nostrilTopRight',
                                                  'bulbTopBaseRight',
                                                  'bulbTopPlaneRight',
                                                  'bulbTopCenter',
                                                  'bulbTopPlaneLeft',
                                                  'bulbTopBaseLeft',
                                                  'nostrilTopLeft',
                                                  'nostrilBaseLeft'],
                                          'rebuild':1}
            d_curveCreation['bulb'] = {'keys':['noseRight',
                                               'nostrilFrontRight',
                                               'bulbBaseRight',
                                               'bulbPlaneRight',
                                               'noseTip',
                                               'bulbPlaneLeft',
                                               'bulbBaseLeft',
                                               'nostrilFrontLeft',
                                               'noseLeft'],
                                          'rebuild':1}
            
            d_curveCreation['bulbUnder'] = {'keys':['nostrilUnderEdgeRight',
                                                    'nostrilUnderFrontRight',
                                                    'bulbUnderRight',
                                                    'bulbUnderCenter',
                                                    'bulbUnderLeft',
                                                    'nostrilUnderFrontLeft',
                                                    'nostrilUnderEdgeLeft'],
                                            'rebuild':1}            
            d_curveCreation['noseUnderTrace'] = {'keys':['noseRight',
                                                         'nostrilUnderEdgeRight',
                                                         'nostrilUnderInnerRight',
                                                         'noseBase',
                                                         'nostrilUnderInnerLeft',
                                                         'nostrilUnderEdgeLeft',
                                                         'noseLeft'],
                                                 'rebuild':1}
            d_curveCreation['noseUnderSmallTrace'] = {'keys':['nostrilUnderInnerRight',
                                                              'noseBase',
                                                              'nostrilUnderInnerLeft'],
                                                 'rebuild':1}            
            
            d_curveCreation['noseSideRight'] = {'keys':['sneerRight', 'sneerLowRight',
                                                        'nostrilBaseRight','noseRight'],
                                                'rebuild':1}
            d_curveCreation['eyeOrbRight'] = {'keys':['edgeOrbTopRight', 'smileUprRight'],
                                                'rebuild':1}
            d_curveCreation['eyeCheekMeetRight'] = {'keys':['cheekBoneRight', 'smileRight'],
                                               'rebuild':1}
            d_curveCreation['noseSideLeft'] = {'keys':['sneerLeft', 'sneerLowLeft',
                                                       'nostrilBaseLeft','noseLeft'],
                                                'rebuild':1}
            d_curveCreation['eyeOrbLeft'] = {'keys':['edgeOrbTopLeft', 'smileUprLeft'],
                                              'rebuild':1}
            d_curveCreation['eyeCheekMeetLeft'] = {'keys':['cheekBoneLeft', 'smileLeft'],
                                                    'rebuild':1}
            
            
            #LoftDeclarations....
            md_loftCreation['nose'] = ['bridgeTop','bridgeStart','bulbTop','bulb','bulbUnder','noseUnderTrace']
            md_loftCreation['noseToCheekRight'] = ['noseSideRight','eyeOrbRight','eyeCheekMeetRight']
            md_loftCreation['noseToCheekLeft'] = ['noseSideLeft','eyeOrbLeft','eyeCheekMeetLeft']
            md_loftCreation['nose'].reverse()
            
            """
            _d_curveCreation = {'jawTemplate1':{'keys':['jawTopLeft','jawEdgeLeftMid','jawLeft','neckBase',
                                                        'jawRight','jawEdgeRightMid','jawTopRight'],
                                                'rebuild':True},
                                'jawTemplate2':{'keys':['cheekLineLeftMid','cheekLeft','jawLineLeftMid',
                                                        'jawUnder',
                                                        'jawLineRightMid','cheekRight','cheekLineRightMid'],
                                                'rebuild':True},
                                'jawTemplate3':{'keys':['cheekBoneLeft','smileLeft','chinLeft','chin',
                                                        'chinRight','smileRight','cheekBoneRight'],
                                                'rebuild':True},
                                }
    
            d_curveCreation.update(_d_curveCreation)
            """            
            
    
    
        md_res = self.UTILS.create_defineHandles(self, l_order, d_creation, _size / 10,
                                                 mTemplateNull)
        ml_subHandles.extend(md_res['ml_handles'])
        md_handles.update(md_res['md_handles'])
    
            
        md_res = self.UTILS.create_defineCurve(self, d_curveCreation, md_handles, mNoTransformNull)
        md_resCurves = md_res['md_curves']
        
        for k,l in md_loftCreation.iteritems():
            ml_curves = [md_resCurves[k2] for k2 in l]
            for mObj in ml_curves:
                mObj.v=False
            
            self.UTILS.create_simpleTemplateLoftMesh(self,
                                                     [mObj.mNode for mObj in ml_curves],
                                                     mTemplateNull,
                                                     polyType = 'bezier',
                                                     baseName = k)            
        
        
        
        
        #Mirror indexing -------------------------------------
        log.debug("|{0}| >> Mirror Indexing...".format(_str_func)+'-'*40) 
        
        idx_ctr = 0
        idx_side = 0
        d = {}
        
        for tag,mHandle in md_handles.iteritems():
            if mHandle in ml_defineHandles:
                continue
            
            mHandle._verifyMirrorable()
            _center = True
            for p1,p2 in d_pairs.iteritems():
                if p1 == tag or p2 == tag:
                    _center = False
                    break
            if _center:
                log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
                mHandle.mirrorSide = 0
                mHandle.mirrorIndex = idx_ctr
                idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"
    
        #Self mirror wiring -------------------------------------------------------
        for k,m in d_pairs.iteritems():
            try:
                md_handles[k].mirrorSide = 1
                md_handles[m].mirrorSide = 2
                md_handles[k].mirrorIndex = idx_side
                md_handles[m].mirrorIndex = idx_side
                md_handles[k].doStore('mirrorHandle',md_handles[m].mNode)
                md_handles[m].doStore('mirrorHandle',md_handles[k].mNode)
                idx_side +=1        
            except Exception,err:
                log.error('Mirror error: {0}'.format(err))
        
        
        
        self.msgList_connect('templateHandles',ml_subHandles)#Connect
        self.msgList_connect('templateCurves',md_res['ml_curves'])#Connect        
        return
        
        
        
            
        #Build our brow loft --------------------------------------------------------------------------
        log.debug("|{0}| >> Loft...".format(_str_func)+'-'*40) 
        self.UTILS.create_simpleTemplateLoftMesh(self,
                                                 [md_loftCurves['browLine'].mNode,
                                                  md_loftCurves['browUpr'].mNode],
                                                 mTemplateNull,
                                                 polyType = 'bezier',
                                                 baseName = 'brow')
        
        #Build our brow loft --------------------------------------------------------------------------
        log.debug("|{0}| >> Visualize brow...".format(_str_func)+'-'*40)
        md_directCurves = {}
        for tag in ['browLeft','browRight']:
            mCrv = md_loftCurves[tag]
            ml_temp = []
            for k in ['start','mid','end']:
                mLoc = cgmMeta.asMeta(self.doCreateAt())
                mJointLabel = mHandleFactory.addJointLabel(mLoc,k)
                
                self.connectChildNode(mLoc, tag+k.capitalize()+'templateHelper','block')
                
                mLoc.rename("{0}_{1}_templateHelper".format(tag,k))
                
                mPointOnCurve = cgmMeta.asMeta(CURVES.create_pointOnInfoNode(mCrv.mNode,
                                                                             turnOnPercentage=True))
                
                mPointOnCurve.doConnectIn('parameter',"{0}.{1}".format(self.mNode,"param{0}".format(k.capitalize())))
            
            
                mPointOnCurve.doConnectOut('position',"{0}.translate".format(mLoc.mNode))
            
                mLoc.p_parent = mNoTransformNull
                ml_temp.append(mLoc)
                #mLoc.v=False
                #mc.pointConstraint(mTrackLoc.mNode,mTrackGroup.mNode)
                
            #Joint curves......
            _crv = mc.curve(d=1,p=[mObj.p_position for mObj in ml_temp])
            
            #CORERIG.create_at(create='curve',l_pos = l_pos)
            mCrv = cgmMeta.validateObjArg(_crv,'cgmObject',setClass=True)
            mCrv.p_parent = mNoTransformNull
            mHandleFactory.color(mCrv.mNode)
            mCrv.rename('{0}_jointCurve'.format(tag))            
            mCrv.v=False
            md_loftCurves[tag] = mCrv
        
            self.connectChildNode(mCrv, tag+'JointCurve','block')
        
            l_clusters = []
            for i,cv in enumerate(mCrv.getComponents('cv')):
                _res = mc.cluster(cv, n = 'test_{0}_{1}_pre_cluster'.format(ml_temp[i].p_nameBase,i))
                TRANS.parent_set( _res[1], ml_temp[i].mNode)
                l_clusters.append(_res)
                ATTR.set(_res[1],'visibility',False)
                
            mc.rebuildCurve(mCrv.mNode, d=3, keepControlPoints=False,ch=1,s=8,
                            n="reparamRebuild")

    except Exception,err:
        cgmGEN.cgmException(Exception,err)

#=============================================================================================================
#>> Prerig
#=============================================================================================================
def prerigDelete(self):
    self.noTransTemplateNull.v=True
    
    for mObj in self.msgList_get('defineSubHandles') + self.msgList_get('templateHandles'):
        mLabel = mObj.getMessageAsMeta('jointLabel')
        if mLabel:
            mLabel.v=1
    
def create_handle(self,tag,pos,mJointTrack=None,
                  trackAttr=None,visualConnection=True,
                  nameEnd = 'BrowHandle'):
    mHandle = cgmMeta.validateObjArg( CURVES.create_fromName('circle', size = _size_sub), 
                                      'cgmObject',setClass=1)
    mHandle.doSnapTo(self)

    mHandle.p_position = pos

    mHandle.p_parent = mStateNull
    mHandle.doStore('cgmName',tag)
    mHandle.doStore('cgmType','templateHandle')
    mHandle.doName()

    mHandleFactory.color(mHandle.mNode,controlType='sub')

    self.connectChildNode(mHandle.mNode,'{0}nameEnd'.format(tag),'block')

    return mHandle

    #joinHandle ------------------------------------------------
    mJointHandle = cgmMeta.validateObjArg( CURVES.create_fromName('jack',
                                                                  size = _size_sub*.75),
                                           'cgmObject',
                                           setClass=1)

    mJointHandle.doStore('cgmName',tag)    
    mJointHandle.doStore('cgmType','jointHelper')
    mJointHandle.doName()                

    mJointHandle.p_position = pos
    mJointHandle.p_parent = mStateNull


    mHandleFactory.color(mJointHandle.mNode,controlType='sub')
    mHandleFactory.addJointLabel(mJointHandle,tag)
    mHandle.connectChildNode(mJointHandle.mNode,'jointHelper','handle')

    mTrackGroup = mJointHandle.doGroup(True,True,
                                       asMeta=True,
                                       typeModifier = 'track',
                                       setClass='cgmObject')

    if trackAttr and mJointTrack:
        mPointOnCurve = cgmMeta.asMeta(CURVES.create_pointOnInfoNode(mJointTrack.mNode,turnOnPercentage=True))

        mPointOnCurve.doConnectIn('parameter',"{0}.{1}".format(self.mNode,trackAttr))

        mTrackLoc = mJointHandle.doLoc()

        mPointOnCurve.doConnectOut('position',"{0}.translate".format(mTrackLoc.mNode))

        mTrackLoc.p_parent = mNoTransformNull
        mTrackLoc.v=False
        mc.pointConstraint(mTrackLoc.mNode,mTrackGroup.mNode)                    


    elif mJointTrack:
        mLoc = mHandle.doLoc()
        mLoc.v=False
        mLoc.p_parent = mNoTransformNull
        mc.pointConstraint(mHandle.mNode,mLoc.mNode)

        res = DIST.create_closest_point_node(mLoc.mNode,mJointTrack.mNode,True)
        #mLoc = cgmMeta.asMeta(res[0])
        mTrackLoc = cgmMeta.asMeta(res[0])
        mTrackLoc.p_parent = mNoTransformNull
        mTrackLoc.v=False
        mc.pointConstraint(mTrackLoc.mNode,mTrackGroup.mNode)


    mAimGroup = mJointHandle.doGroup(True,True,
                                     asMeta=True,
                                     typeModifier = 'aim',
                                     setClass='cgmObject')
    mc.aimConstraint(mLidRoot.mNode,
                     mAimGroup.mNode,
                     maintainOffset = False, weight = 1,
                     aimVector = [0,0,-1],
                     upVector = [0,1,0],
                     worldUpVector = [0,1,0],
                     worldUpObject = self.mNode,
                     worldUpType = 'objectRotation' )                          


    if visualConnection:
        log.debug("|{0}| >> visualConnection ".format(_str_func, tag))
        trackcrv,clusters = CORERIG.create_at([mLidRoot.mNode,
                                               mJointHandle.mNode],#ml_handleJoints[1]],
                                              'linearTrack',
                                              baseName = '{0}_midTrack'.format(tag))

        mTrackCrv = cgmMeta.asMeta(trackcrv)
        mTrackCrv.p_parent = mNoTransformNull
        mHandleFactory.color(mTrackCrv.mNode, controlType = 'sub')

        for s in mTrackCrv.getShapes(asMeta=True):
            s.overrideEnabled = 1
            s.overrideDisplayType = 2

    return mHandle

def prerig(self):
    def create_handle(mHelper, mSurface, tag, k, side, controlType = 'main', controlShape = 'squareRounded',
                      aimGroup = 1,nameDict = None,surfaceOffset =1,mode='track',size = 1.0):
        mHandle = cgmMeta.validateObjArg( CURVES.create_fromName(controlShape, size = size), 
                                          'cgmControl',setClass=1)
        mHandle._verifyMirrorable()
    
        mHandle.doSnapTo(self)
        mHandle.p_parent = mStateNull
    
        if nameDict:
            RIGGEN.store_and_name(mHandle,nameDict)
        else:
            mHandle.doStore('cgmName',tag)
            mHandle.doStore('cgmType','prerigHandle')
            mHandle.doName()
    
    
        _key = tag
        if k:
            _key = _key+k.capitalize()
        mMasterGroup = mHandle.doGroup(True,True,
                                       asMeta=True,
                                       typeModifier = 'master',
                                       setClass='cgmObject')
    
        if mode == 'track':
            if mHelper:
                mc.pointConstraint(mHelper.mNode,mMasterGroup.mNode,maintainOffset=False)
        else:
            d_res = DIST.get_closest_point_data(mSurface.mNode,mHelper.mNode)
            mMasterGroup.p_position = d_res['position']    
    
        mHandleFactory.color(mHandle.mNode,side = side, controlType=controlType)
        mStateNull.connectChildNode(mHandle, _key+'prerigHelper','block')
    
        _const = mc.normalConstraint(mSurface.mNode, mMasterGroup.mNode,
                                     aimVector = [0,0,1], upVector = [0,1,0],
                                     worldUpObject = self.mNode,
                                     worldUpType = 'objectrotation', 
                                     worldUpVector = [0,1,0])
        mc.delete(_const)
        
    
        if aimGroup:
            mHandle.doGroup(True,True,
                            asMeta=True,
                            typeModifier = 'aim',
                            setClass='cgmObject')
    
    
        mHandle.tz = surfaceOffset
    
        return mHandle
    
    def create_jointHelper(mPos, mSurface, tag, k, side, nameDict=None, aimGroup = 1,size = 1.0, sizeMult=1.0, mode = 'track',surfaceOffset = 1):

        mHandle = cgmMeta.validateObjArg( CURVES.create_fromName('axis3d', size = (size)*sizeMult), 
                                          'cgmControl',setClass=1)
        mHandle._verifyMirrorable()

        mHandle.doSnapTo(self)
        mHandle.p_parent = mStateNull
        if nameDict:
            RIGGEN.store_and_name(mHandle,nameDict)
            _dCopy = copy.copy(nameDict)
            _dCopy.pop('cgmType')
            mJointLabel = mHandleFactory.addJointLabel(mHandle,NAMETOOLS.returnCombinedNameFromDict(_dCopy))

        else:
            mHandle.doStore('cgmName',tag)
            mHandle.doStore('cgmType','jointHelper')
            mHandle.doName()

        _key = tag
        if k:
            _key = "{0}_{1}".format(tag,k)



        mMasterGroup = mHandle.doGroup(True,True,
                                       asMeta=True,
                                       typeModifier = 'master',
                                       setClass='cgmObject')
        
        if mode == 'track':
            if mPos:
                mc.pointConstraint(mPos.mNode,mMasterGroup.mNode,maintainOffset=False)
        else:
            d_res = DIST.get_closest_point_data(mSurface.mNode,mPos.mNode)
            mMasterGroup.p_position = d_res['position']

        #mHandleFactory.color(mHandle.mNode,side = side, controlType='sub')
        mStateNull.connectChildNode(mHandle, _key+'prerigHelper','block')

        if mSurface:
            _const = mc.normalConstraint(mSurface.mNode, mMasterGroup.mNode,
                                         aimVector = [0,0,1], upVector = [0,1,0],
                                         worldUpObject = self.mNode,
                                         worldUpType = 'objectrotation', 
                                         worldUpVector = [0,1,0])
            mc.delete(_const)
            mHandle.tz = -surfaceOffset
            

        if aimGroup:
            mHandle.doGroup(True,True,
                            asMeta=True,
                            typeModifier = 'aim',
                            setClass='cgmObject')


        return mHandle            
    try:
        _str_func = 'prerig'
        log.debug("|{0}| >>  {1}".format(_str_func,self)+ '-'*80)
        self.blockState = 'prerig'
        _side = self.UTILS.get_side(self)
        
        self.atUtils('module_verify')
        mStateNull = self.UTILS.stateNull_verify(self,'prerig')
        mNoTransformNull = self.atUtils('noTransformNull_verify','prerig')
        self.noTransTemplateNull.v=False
        
        _offset = self.atUtils('get_shapeOffset')/4.0
        _size = MATH.average(self.baseSize[1:])
        _size_base = _size * .25
        _size_sub = _size_base * .5
        
        #mRoot = self.getMessageAsMeta('rootHelper')
        mHandleFactory = self.asHandleFactory()
        
        #---------------------------------------------------------------
        log.debug("|{0}| >> Gather define/template handles/curves in a useful format...".format(_str_func)) 
        d_pairs = {}
        ml_handles = []
        md_handles = {}
        md_dHandles = {}
        md_dCurves = {}
        md_jointHandles = {}
        ml_jointHandles = []
        ml_defineHandles = []
        for mObj in self.msgList_get('defineSubHandles') + self.msgList_get('templateHandles'):
            md_dHandles[mObj.handleTag] = mObj
            mLabel = mObj.getMessageAsMeta('jointLabel')
            if mLabel:
                mLabel.v=0
            ml_defineHandles.append(mObj)

        for mObj in self.msgList_get('defineCurves') + self.msgList_get('templateCurves') :
            md_dCurves[mObj.handleTag] = mObj
            mObj.template=1        
        
        #Main setup -----------------------------------------------------
        if self.noseSetup:
            log.debug("|{0}| >>  noseSetup".format(_str_func)+ '-'*40)
            str_noseSetup = self.getEnumValueString('noseSetup')
        
            if str_noseSetup == 'simple':
                log.debug("|{0}| >>  noseSetup: {1}".format(_str_func,str_noseSetup))
        
                mSurf =  self.noseTemplateLoft
        
                _d_name = {'cgmName':'nose',
                           'cgmType':'handleHelper'}
                
                
                #NoseBase ----------------------------------------------------------------------
                log.debug("|{0}| >>  {1}...".format(_str_func,'noseTip'))
                _tag = 'noseBase'
                mDefHandle = md_dHandles['noseTip']
                _dTmp = copy.copy(_d_name)
                _dTmp['cgmName'] = 'noseBase'
                #_dTmp['cgmDirection'] = side
                mHandle = create_handle(mDefHandle,mSurf,_tag,None,None,controlShape = 'loftWideDown',
                                        size= _size_sub*2.0,
                                        controlType = 'main',
                                        nameDict = _d_name,
                                        surfaceOffset=-_offset/2.0, mode = 'closestPoint')
                ml_handles.append(mHandle)
            
                mStateNull.doStore(_tag+'ShapeHelper',mHandle.mNode)
                md_handles[_tag] = mHandle
               
            
                #Joint handle
                _dTmp['cgmType'] = 'jointHandle'
                mJointHelper = create_jointHelper(mHandle,mSurf,_tag,None,None,nameDict=_dTmp,mode='closestPoint',surfaceOffset=0)
                mStateNull.doStore(_tag+'JointHelper',mJointHelper.mNode)
                
                mJointHelper.masterGroup.p_position = DIST.get_average_position([md_dHandles['nostrilBaseLeft'].p_position,
                                                                            md_dHandles['nostrilBaseRight'].p_position])                
                mHandle.masterGroup.p_position = DIST.get_average_position([md_dHandles['bulbBaseLeft'].p_position,
                                                                                 md_dHandles['bulbBaseRight'].p_position])                 
                md_handles[_tag+'Joint'] = mJointHelper
                ml_jointHandles.append(mJointHelper)
                
                #NoseTip ----------------------------------------------------------------------
                if self.numJointsNoseTip:
                    log.debug("|{0}| >>  {1}...".format(_str_func,'noseTip'))
                    _tag = 'noseTip'
                    mDefHandle = md_dHandles['noseTip']
                    _dTmp = copy.copy(_d_name)
                    _dTmp['cgmName'] = 'noseTip'
                    #_dTmp['cgmDirection'] = side
                    mHandle = create_handle(mDefHandle,mSurf,_tag,None,None,controlShape = 'semiSphere',
                                            size= _size_sub,
                                            controlType = 'sub',
                                            nameDict = _d_name,
                                            surfaceOffset=_offset/2.0, mode = 'closestPoint')
                    ml_handles.append(mHandle)
                
                    mStateNull.doStore(_tag+'ShapeHelper',mHandle.mNode)
                
                    #Joint handle
                    _dTmp['cgmType'] = 'jointHandle'
                    mJointHelper = create_jointHelper(mHandle,mSurf,_tag,None,None,nameDict=_dTmp,mode='closestPoint',surfaceOffset=_offset*2.0)
                    mStateNull.doStore(_tag+'JointHelper',mJointHelper.mNode)
                    
                    md_handles[_tag] = mHandle
                    md_handles[_tag+'Joint'] = mJointHelper
                    ml_jointHandles.append(mJointHelper)
                    
                
                
                #Nostrils -------------------------------------------------------------------
                if self.numJointsNostril:
                    d_pairs['nostrilLeft'] = 'nostrilRight'
                    d_pairs['nostrilLeftJoint'] = 'nostrilRightJoint'
                    for side in ['left','right']:
                        #Get our position
                        _tag = 'nostril'+side.capitalize()
                        log.debug("|{0}| >>  {1}...".format(_str_func,_tag))
            
                        mDefHandle = md_dHandles['nostrilFront'+side.capitalize()]
                        _dTmp = copy.copy(_d_name)
                        _dTmp['cgmName'] = 'nostril'
                        _dTmp['cgmDirection'] = side
                        mHandle = create_handle(mDefHandle,mSurf,_tag,None,side,controlShape = 'semiSphere',
                                                size= _size_sub/2.0,
                                                controlType = 'sub',
                                                nameDict = _d_name,
                                                surfaceOffset=_offset/2.0, mode = 'closestPoint')
                        ml_handles.append(mHandle)
            
                        mStateNull.doStore(_tag+'ShapeHelper',mHandle.mNode)
            
                        #Joint handle
                        _dTmp['cgmType'] = 'jointHandle'
                        mJointHelper = create_jointHelper(mHandle,mSurf,_tag,None,side,nameDict=_dTmp,mode='closestPoint',surfaceOffset=_offset)
                        mStateNull.doStore(_tag+'JointHelper',mJointHelper.mNode)
                        ml_jointHandles.append(mJointHelper)
                        
                        md_handles[_tag] = mHandle
                        md_handles[_tag+'Joint'] = mJointHelper                        
            else:
                raise ValueError,"Invalid noseSetup: {0}".format(str_noseSetup)
        
        if self.cheekSetup:
            log.debug("|{0}| >>  Cheeksetup".format(_str_func)+ '-'*40)
            str_cheekSetup = self.getEnumValueString('cheekSetup')
            
            if str_cheekSetup == 'single':
                log.debug("|{0}| >>  cheekSetup: {1}".format(_str_func,str_cheekSetup))
                
                mSurf =  self.jawTemplateLoft
                
                _d_name = {'cgmName':'cheek',
                           'cgmType':'handleHelper'}
                
                d_pairs['cheekLeft'] = 'cheekRight'
                d_pairs['cheekLeftJoint'] = 'cheekRightJoint'                
                
                for side in ['left','right']:
                    #Get our position
                    _tag = 'cheek'+side.capitalize()
                    log.debug("|{0}| >>  {1}...".format(_str_func,_tag))
                    
                    mDefHandle = md_dHandles[_tag]
                    _dTmp = copy.copy(_d_name)
                    _dTmp['cgmDirection'] = side
                    mHandle = create_handle(mDefHandle,mSurf,_tag,None,side,controlShape = 'semiSphere',
                                            size= _size_sub,
                                            controlType = 'sub',nameDict = _d_name,surfaceOffset=_offset, mode = 'closestPoint')
                    ml_handles.append(mHandle)
                    
                    mStateNull.doStore(_tag+'ShapeHelper',mHandle.mNode)
                    
                    #Joint handle
                    _dTmp['cgmType'] = 'jointHandle'
                    mJointHelper = create_jointHelper(mHandle,mSurf,_tag,None,
                                                      side,
                                                      size= _size_sub,
                                                      nameDict=_dTmp,mode='closestPoint',surfaceOffset=_offset)
                    mStateNull.doStore(_tag+'JointHelper',mJointHelper.mNode)
                    md_handles[_tag] = mHandle
                    md_handles[_tag+'Joint'] = mJointHelper
                    ml_jointHandles.append(mJointHelper)
                    
            else:
                raise ValueError,"Invalid cheekSetup: {0}".format(str_cheekSetup)
        
        if self.jawSetup:
            log.debug("|{0}| >>  Jaw setup...".format(_str_func)+ '-'*40)
            
            _d_name = {'cgmName':'jaw',
                       'cgmType':'jointHelper'}            
            md_jointHandles['jawLower'] = create_jointHelper(None,None,'jawLower',None,
                                                             'center',nameDict=_d_name,
                                                             size= _size_sub,
                                                             sizeMult = 2.0,aimGroup=0)
            md_jointHandles['jawLower'].p_position = DIST.get_average_position([md_dHandles['jawEdgeRightMid'].p_position,
                                                                                md_dHandles['jawEdgeLeftMid'].p_position])
            
            
            l_jaw = ['jawEdgeRightMid', 'jawRight','jawLineRightMid','chinRight','chin',
                     'chinLeft','jawLineLeftMid', 'jawLeft', 'jawEdgeLeftMid']
            _crv = CORERIG.create_at(create='curveLinear',l_pos=[md_dHandles[k].p_position for k in l_jaw])
            #md_dCurves['jawLine'].mNode
            _shape = mc.offsetCurve(_crv,rn=0,cb=1,st=1,cl=1,cr=0,ch=0,
                                    d=1,tol=.0001,sd=1,ugn=0,
                                    distance =-_offset)
            mc.delete(_crv)
            
            mShape = cgmMeta.validateObjArg(_shape[0],'cgmControl',setClass=1)
            mShape.p_parent = mStateNull
            
            _d_name['cgmType'] = 'shapeHelper'
            RIGGEN.store_and_name(mShape,_d_name)
            mHandleFactory.color(mShape.mNode,side = _side, controlType='main')
            md_jointHandles['jawLower'].doStore('shapeHelper',mShape.mNode)
            mShape.doStore('dagHelper', md_jointHandles['jawLower'].mNode)
            
            mStateNull.connectChildNode(md_jointHandles['jawLower'], 'jaw'+'JointHelper','block')
            mStateNull.connectChildNode(mShape, 'jaw'+'ShapeHelper','block')
            ml_jointHandles.append(md_jointHandles['jawLower'])            
            ml_handles.append(mShape)
            
            md_handles['jaw'] = mShape
            md_handles['jawJoint'] = md_jointHandles['jawLower']            
            
        if self.muzzleSetup:
            log.debug("|{0}| >>  Muzzle setup...".format(_str_func)+ '-'*40)
            
            _d_name = {'cgmName':'muzzle',
                       'cgmType':'jointHelper'}
            md_jointHandles['muzzle'] = create_jointHelper(None,None,'muzzle',None,
                                                           'center',
                                                           size= _size_sub,
                                                           nameDict=_d_name,sizeMult = 2.0,aimGroup=0)
            md_jointHandles['muzzle'].p_position = self.getPositionByAxisDistance('z-',_offset * 2)
            mStateNull.connectChildNode(md_jointHandles['muzzle'], 'muzzle'+'JointHelper','block')
            
            mShape = mHandleFactory.buildBaseShape('pyramid',baseSize = _offset, shapeDirection = 'z+')
            TRANS.scale_to_boundingBox(mShape.mNode, [_offset,_offset,_offset/2.0])
            mShape.p_parent = mStateNull
            mShape.p_position = self.getPositionByAxisDistance('z+',_offset * 2)
            
            _d_name['cgmType'] = 'shapeHelper'
            RIGGEN.store_and_name(mShape,_d_name)
            mHandleFactory.color(mShape.mNode,side = _side, controlType='main')
            md_jointHandles['muzzle'].doStore('shapeHelper',mShape.mNode)
            mShape.doStore('dagHelper',md_jointHandles['muzzle'].mNode)            
            
            ml_handles.append(mShape)
            
            md_handles['muzzle'] = mShape
            md_handles['muzzleJoint'] = md_jointHandles['muzzle']              
            ml_jointHandles.append(md_jointHandles['muzzle'])            
            
            pass

            
        
        #Mirror indexing -------------------------------------
        log.debug("|{0}| >> Mirror Indexing...".format(_str_func)+'-'*40) 
    
        idx_ctr = 0
        idx_side = 0
        d = {}
    
        for tag,mHandle in md_handles.iteritems():
            if mHandle in ml_defineHandles:
                continue
            try:mHandle._verifyMirrorable()
            except:
                mHandle = cgmMeta.validateObjArg(mHandle,'cgmControl',setClass=1)
                mHandle._verifyMirrorable()
            _center = True
            for p1,p2 in d_pairs.iteritems():
                if p1 == tag or p2 == tag:
                    _center = False
                    break
            if _center:
                log.debug("|{0}| >>  Center: {1}".format(_str_func,tag))    
                mHandle.mirrorSide = 0
                mHandle.mirrorIndex = idx_ctr
                idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"
    
        #Self mirror wiring -------------------------------------------------------
        for k,m in d_pairs.iteritems():
            try:
                md_handles[k].mirrorSide = 1
                md_handles[m].mirrorSide = 2
                md_handles[k].mirrorIndex = idx_side
                md_handles[m].mirrorIndex = idx_side
                md_handles[k].doStore('mirrorHandle',md_handles[m].mNode)
                md_handles[m].doStore('mirrorHandle',md_handles[k].mNode)
                idx_side +=1        
            except Exception,err:
                log.error('Mirror error: {0}'.format(err))        
        
        
        
        
        
        self.msgList_connect('prerigHandles', ml_handles)
        self.msgList_connect('jointHandles', ml_jointHandles)
        
        pprint.pprint(vars())
        return
        
        ml_handles = []
        md_handles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}
        md_jointHandles = {'brow':{'center':[],
                              'left':[],
                              'right':[]}}

        
        #Get base dat =============================================================================    
        mBBHelper = self.bbHelper
        mBrowLoft = self.getMessageAsMeta('browTemplateLoft')
        
        _size = MATH.average(self.baseSize[1:])
        _size_base = _size * .25
        _size_sub = _size_base * .5
        
        idx_ctr = 0
        idx_side = 0
        
        
        
        #Handles =====================================================================================
        log.debug("|{0}| >> Brow Handles..".format(_str_func)+'-'*40)
        
        _d = {'cgmName':'browCenter',
              'cgmType':'handleHelper'}
        
        mBrowCenterDefine = self.defineBrowcenterHelper
        md_handles['browCenter'] = [create_handle(mBrowCenterDefine,mBrowLoft,
                                                  'browCenter',None,'center',nameDict = _d)]
        md_handles['brow']['center'].append(md_handles['browCenter'])
        md_handles['browCenter'][0].mirrorIndex = idx_ctr
        idx_ctr +=1
        mStateNull.msgList_connect('browCenterPrerigHandles',md_handles['browCenter'])
        
        _d_nameHandleSwap = {'start':'inner',
                             'end':'outer'}
        for tag in ['browLeft','browRight']:
            _d['cgmName'] = tag
        
            for k in ['start','mid','end']:
                _d['cgmNameModifier'] = _d_nameHandleSwap.get(k,k)
                
                if 'Left' in tag:
                    _side = 'left'
                elif 'Right' in tag:
                    _side = 'right'
                else:
                    _side = 'center'
                
                if _side in ['left','right']:
                    _d['cgmDirection'] = _side
                    
                if k == 'mid':
                    _control = 'sub'
                else:
                    _control = 'main'
                    
                mTemplateHelper = self.getMessageAsMeta(tag+k.capitalize()+'templateHelper')
                
                mHandle = create_handle(mTemplateHelper,mBrowLoft,tag,k,_side,controlType = _control,nameDict = _d)
                md_handles['brow'][_side].append(mHandle)
                ml_handles.append(mHandle)                
            mStateNull.msgList_connect('{0}PrerigHandles'.format(tag),md_handles['brow'][_side])


        #Joint helpers ------------------------
        log.debug("|{0}| >> Joint helpers..".format(_str_func)+'-'*40)
        _d = {'cgmName':'brow',
              'cgmDirection':'center',
              'cgmType':'jointHelper'}        
        
        mFullCurve = self.getMessageAsMeta('browLineloftCurve')
        md_jointHandles['browCenter'] = [create_jointHelper(mBrowCenterDefine,mBrowLoft,'center',None,
                                                            'center',nameDict=_d)]
        md_jointHandles['brow']['center'].append(md_jointHandles['browCenter'])
        md_jointHandles['browCenter'][0].mirrorIndex = idx_ctr
        idx_ctr +=1
        mStateNull.msgList_connect('browCenterJointHandles',md_jointHandles['browCenter'])
        

        for tag in ['browLeft','browRight']:
            mCrv = self.getMessageAsMeta("{0}JointCurve".format(tag))
            if 'Left' in tag:
                _side = 'left'
            elif 'Right' in tag:
                _side = 'right'
            else:
                _side = 'center'            
            
            if _side in ['left','right']:
                _d['cgmDirection'] = _side
                
            _factor = 100/(self.numJointsBrow-1)
            
            for i in range(self.numJointsBrow):
                log.debug("|{0}| >>  Joint Handle: {1}|{2}...".format(_str_func,tag,i))            
                _d['cgmIterator'] = i
                
                mLoc = cgmMeta.asMeta(self.doCreateAt())
                mLoc.rename("{0}_{1}_jointTrackHelper".format(tag,i))
            
                #self.connectChildNode(mLoc, tag+k.capitalize()+'templateHelper','block')
                mPointOnCurve = cgmMeta.asMeta(CURVES.create_pointOnInfoNode(mCrv.mNode,
                                                                             turnOnPercentage=True))
            
                mPointOnCurve.parameter = (_factor * i)/100.0
                mPointOnCurve.doConnectOut('position',"{0}.translate".format(mLoc.mNode))
            
                mLoc.p_parent = mNoTransformNull
                
            
                res = DIST.create_closest_point_node(mLoc.mNode,mFullCurve.mNode,True)
                #mLoc = cgmMeta.asMeta(res[0])
                mTrackLoc = cgmMeta.asMeta(res[0])
                mTrackLoc.p_parent = mNoTransformNull
                mTrackLoc.v=False
                
                mHandle = create_jointHelper(mTrackLoc,mBrowLoft,tag,i,_side,nameDict=_d)
                md_jointHandles['brow'][_side].append(mHandle)
                ml_handles.append(mHandle)
                
            
        
        #Aim pass ------------------------------------------------------------------------
        for side in ['left','right']:
            #Handles -------
            ml = md_handles['brow'][side]
            for i,mObj in enumerate(ml):
                mObj.mirrorIndex = idx_side + i
                mObj.mirrorAxis = "translateX,rotateY,rotateZ"
                
                if side == 'left':
                    _aim = [-1,0,0]
                    mObj.mirrorSide = 1                    
                else:
                    _aim = [1,0,0]
                    mObj.mirrorSide = 2
                    
                _up = [0,0,1]
                _worldUp = [0,0,1]
                
                if i == 0:
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(md_handles['browCenter'][0].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )                                
                else:

                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i-1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )
                    
            mStateNull.msgList_connect('brow{0}PrerigHandles'.format(side.capitalize()), ml)
            
        idx_side = idx_side + i + 1
        log.info(idx_side)
        
        for side in ['left','right']:
            #Joint Helpers ----------------
            ml = md_jointHandles['brow'][side]
            for i,mObj in enumerate(ml):
                if side == 'left':
                    _aim = [1,0,0]
                    mObj.mirrorSide = 1
                else:
                    _aim = [-1,0,0]
                    mObj.mirrorSide = 2
                    
                mObj.mirrorIndex = idx_side + i
                mObj.mirrorAxis = "translateX,rotateY,rotateZ"
                _up = [0,0,1]
                _worldUp = [0,0,1]
                if mObj == ml[-1]:
                    _vAim = [_aim[0]*-1,_aim[1],_aim[2]]
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i-1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _vAim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )                    
                else:
                    mAimGroup = mObj.aimGroup
                    mc.aimConstraint(ml[i+1].masterGroup.mNode,
                                     mAimGroup.mNode,
                                     maintainOffset = False, weight = 1,
                                     aimVector = _aim,
                                     upVector = _up,
                                     worldUpVector = _worldUp,
                                     worldUpObject = mObj.masterGroup.mNode,
                                     worldUpType = 'objectRotation' )
                    
            mStateNull.msgList_connect('brow{0}JointHandles'.format(side.capitalize()), ml)
        
        #Mirror setup --------------------------------
        """
        for mHandle in ml_handles:
            mHandle._verifyMirrorable()
            _str_handle = mHandle.p_nameBase
            if 'Center' in _str_handle:
                mHandle.mirrorSide = 0
                mHandle.mirrorIndex = idx_ctr
                idx_ctr +=1
            mHandle.mirrorAxis = "translateX,rotateY,rotateZ"
    
        #Self mirror wiring -------------------------------------------------------
        for k,m in _d_pairs.iteritems():
            md_handles[k].mirrorSide = 1
            md_handles[m].mirrorSide = 2
            md_handles[k].mirrorIndex = idx_side
            md_handles[m].mirrorIndex = idx_side
            md_handles[k].doStore('mirrorHandle',md_handles[m].mNode)
            md_handles[m].doStore('mirrorHandle',md_handles[k].mNode)
            idx_side +=1        """
        
        #Close out ======================================================================================
        self.msgList_connect('prerigHandles', ml_handles)
        
        self.blockState = 'prerig'
        return
    
    
    except Exception,err:
        cgmGEN.cgmException(Exception,err)
        
#=============================================================================================================
#>> Skeleton
#=============================================================================================================
def skeleton_check(self):
    return True

def skeleton_build(self, forceNew = True):
    _short = self.mNode
    _str_func = '[{0}] > skeleton_build'.format(_short)
    log.debug("|{0}| >> ...".format(_str_func)) 
    
    _radius = self.atUtils('get_shapeOffset') * .25# or 1
    ml_joints = []
    
    mModule = self.atUtils('module_verify')
    
    mRigNull = mModule.rigNull
    if not mRigNull:
        raise ValueError,"No rigNull connected"
    
    mPrerigNull = self.prerigNull
    if not mPrerigNull:
        raise ValueError,"No prerig null"
    
    mRoot = self.UTILS.skeleton_getAttachJoint(self)
    
    #>> If skeletons there, delete -------------------------------------------------------------------------- 
    _bfr = mRigNull.msgList_get('moduleJoints',asMeta=True)
    if _bfr:
        log.debug("|{0}| >> Joints detected...".format(_str_func))            
        if forceNew:
            log.debug("|{0}| >> force new...".format(_str_func))                            
            mc.delete([mObj.mNode for mObj in _bfr])
        else:
            return _bfr
        
    _baseNameAttrs = ATTR.datList_getAttrs(self.mNode,'nameList')
    _l_baseNames = ATTR.datList_get(self.mNode, 'nameList')
    
    def create_jointFromHandle(mHandle=None,mParent = False):
        mJnt = mHandle.doCreateAt('joint')
        mJnt.doCopyNameTagsFromObject(mHandle.mNode,ignore = ['cgmType'])
        mJnt.doStore('cgmType','skinJoint')
        mJnt.doName()
        JOINT.freezeOrientation(mJnt.mNode)

        mJnt.p_parent = mParent
        ml_joints.append(mJnt)
        return mJnt

    if self.jawSetup:
        #'jaw'+'JointHelper'
        mObj = mPrerigNull.getMessageAsMeta('jaw'+'JointHelper')
        mJaw = create_jointFromHandle(mObj,mRoot)
        mPrerigNull.doStore('jawJoint',mJaw.mNode)
        
    
    if self.noseSetup:
        log.debug("|{0}| >>  noseSetup".format(_str_func)+ '-'*40)
        str_noseSetup = self.getEnumValueString('noseSetup')
    
        if str_noseSetup == 'simple':
            log.debug("|{0}| >>  noseSetup: {1}".format(_str_func,str_noseSetup))
            
            _tag = 'noseBase'
            mNoseBase = create_jointFromHandle(mPrerigNull.getMessageAsMeta('{0}JointHelper'.format(_tag)),
                                               mRoot)
            mPrerigNull.doStore('{0}Joint'.format(_tag),mNoseBase.mNode)
            
            #NoseTip ----------------------------------------------------------------------
            if self.numJointsNoseTip:
                log.debug("|{0}| >>  {1}...".format(_str_func,'noseTip'))
                _tag = 'noseTip'
                mNoseTip = create_jointFromHandle(mPrerigNull.getMessageAsMeta('{0}JointHelper'.format(_tag)),
                                                  mNoseBase)
                mPrerigNull.doStore('{0}Joint'.format(_tag),mNoseTip.mNode)

            #Nostrils -------------------------------------------------------------------
            if self.numJointsNostril:
                for side in ['left','right']:
                    _tag = 'nostril'+side.capitalize()
                    log.debug("|{0}| >>  {1}...".format(_str_func,_tag))
                    mJnt = create_jointFromHandle(mPrerigNull.getMessageAsMeta('{0}JointHelper'.format(_tag)),
                                                  mNoseBase)
                    mPrerigNull.doStore('{0}Joint'.format(_tag),mJnt.mNode)
                    
        else:
            raise ValueError,"Invalid noseSetup: {0}".format(str_noseSetup)
        
    if self.cheekSetup:
        log.debug("|{0}| >>  Cheeksetup".format(_str_func)+ '-'*40)
        str_cheekSetup = self.getEnumValueString('cheekSetup')
        if str_cheekSetup == 'single':
            log.debug("|{0}| >>  cheekSetup: {1}".format(_str_func,str_cheekSetup))
            
            for side in ['left','right']:
                _tag = 'cheek'+side.capitalize()
                log.debug("|{0}| >>  {1}...".format(_str_func,_tag))
                mJnt = create_jointFromHandle(mPrerigNull.getMessageAsMeta('{0}JointHelper'.format(_tag)),
                                              mJaw)
                mPrerigNull.doStore('{0}Joint'.format(_tag),mJnt.mNode)               
        else:
            raise ValueError,"Invalid cheekSetup: {0}".format(str_cheekSetup)
                
    #>> ===========================================================================
    mRigNull.msgList_connect('moduleJoints', ml_joints)
    self.msgList_connect('moduleJoints', ml_joints)
    
    pprint.pprint(ml_joints)

    for mJnt in ml_joints:
        mJnt.displayLocalAxis = 1
        mJnt.radius = _radius
        
    return ml_joints    
    
   
    

    
    
    
    #>> Head ===================================================================================
    log.debug("|{0}| >> Head...".format(_str_func))
    p = POS.get( ml_prerigHandles[-1].jointHelper.mNode )
    mHeadHelper = ml_templateHandles[0].orientHelper
    
    #...create ---------------------------------------------------------------------------
    mHead_jnt = cgmMeta.cgmObject(mc.joint (p=(p[0],p[1],p[2])))
    mHead_jnt.parent = False
    #self.copyAttrTo(_baseNameAttrs[-1],mHead_jnt.mNode,'cgmName',driven='target')
    
    #...orient ----------------------------------------------------------------------------
    #cgmMeta.cgmObject().getAxisVector
    CORERIG.match_orientation(mHead_jnt.mNode, mHeadHelper.mNode)
    JOINT.freezeOrientation(mHead_jnt.mNode)
    
    #...name ----------------------------------------------------------------------------
    #mHead_jnt.doName()
    #mHead_jnt.rename(_l_namesToUse[-1])
    for k,v in _l_namesToUse[-1].iteritems():
        mHead_jnt.doStore(k,v)
    mHead_jnt.doName()
    
    if self.neckBuild:#...Neck =====================================================================
        log.debug("|{0}| >> neckBuild...".format(_str_func))
        if len(ml_prerigHandles) == 2 and self.neckJoints == 1:
            log.debug("|{0}| >> Single neck joint...".format(_str_func))
            p = POS.get( ml_prerigHandles[0].jointHelper.mNode )
            
            mBaseHelper = ml_prerigHandles[0].orientHelper
            
            #...create ---------------------------------------------------------------------------
            mNeck_jnt = cgmMeta.cgmObject(mc.joint (p=(p[0],p[1],p[2])))
            
            #self.copyAttrTo(_baseNameAttrs[0],mNeck_jnt.mNode,'cgmName',driven='target')
            
            #...orient ----------------------------------------------------------------------------
            #cgmMeta.cgmObject().getAxisVector
            TRANS.aim_atPoint(mNeck_jnt.mNode,
                              mHead_jnt.p_position,
                              'z+', 'y+', 'vector',
                              vectorUp=mHeadHelper.getAxisVector('z-'))
            JOINT.freezeOrientation(mNeck_jnt.mNode)
            
            #mNeck_jnt.doName()
            
            mHead_jnt.p_parent = mNeck_jnt
            ml_joints.append(mNeck_jnt)
            
            #mNeck_jnt.rename(_l_namesToUse[0])
            for k,v in _l_namesToUse[0].iteritems():
                mNeck_jnt.doStore(k,v)
            mNeck_jnt.doName()
        else:
            log.debug("|{0}| >> Multiple neck joint...".format(_str_func))
            
            _d = self.atBlockUtils('skeleton_getCreateDict', self.neckJoints +1)
            
            mOrientHelper = ml_prerigHandles[0].orientHelper
            
            ml_joints = JOINT.build_chain(_d['positions'][:-1], parent=True, worldUpAxis= mOrientHelper.getAxisVector('z-'))
            
            for i,mJnt in enumerate(ml_joints):
                #mJnt.rename(_l_namesToUse[i])
                for k,v in _l_namesToUse[i].iteritems():
                    mJnt.doStore(k,v)
                mJnt.doName()                
            
            #self.copyAttrTo(_baseNameAttrs[0],ml_joints[0].mNode,'cgmName',driven='target')
            
        mHead_jnt.p_parent = ml_joints[-1]
        ml_joints[0].parent = False
    else:
        mHead_jnt.parent = False
        #mHead_jnt.rename(_l_namesToUse[-1])
        
    ml_joints.append(mHead_jnt)
    
    for mJnt in ml_joints:
        mJnt.displayLocalAxis = 1
        mJnt.radius = _radius
    if len(ml_joints) > 1:
        mHead_jnt.radius = ml_joints[-1].radius * 5

    mRigNull.msgList_connect('moduleJoints', ml_joints)
    self.msgList_connect('moduleJoints', ml_joints)
    self.atBlockUtils('skeleton_connectToParent')
    
    return ml_joints


#=============================================================================================================
#>> rig
#=============================================================================================================
#NOTE - self here is a rig Factory....

d_preferredAngles = {}#In terms of aim up out for orientation relative values, stored left, if right, it will invert
d_rotateOrders = {}

#Rig build stuff goes through the rig build factory ------------------------------------------------------
@cgmGEN.Timer
def rig_prechecks(self):
    _short = self.d_block['shortName']
    _str_func = 'rig_prechecks'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    
    str_faceType = mBlock.getEnumValueString('faceType')
    if str_faceType not in ['default']:
        self.l_precheckErrors.append("faceType setup not completed: {0}".format(str_faceType))

    str_jawSetup = mBlock.getEnumValueString('jawSetup')
    if str_jawSetup not in ['none','simple']:
        self.l_precheckErrors.append("Jaw setup not completed: {0}".format(str_jawSetup))
    
    str_muzzleSetup = mBlock.getEnumValueString('muzzleSetup')
    if str_muzzleSetup not in ['none','simple']:
        self.l_precheckErrors.append("Muzzle setup not completed: {0}".format(str_muzzleSetup))
        
    str_noseSetup = mBlock.getEnumValueString('noseSetup')
    if str_noseSetup not in ['none','simple']:
        self.l_precheckErrors.append("Nose setup not completed: {0}".format(str_noseSetup))
        
    str_nostrilSetup = mBlock.getEnumValueString('nostrilSetup')
    if str_nostrilSetup not in ['none','default']:
        self.l_precheckErrors.append("Nostril setup not completed: {0}".format(str_nostrilSetup))
        
    str_cheekSetup = mBlock.getEnumValueString('cheekSetup')
    if str_cheekSetup not in ['none','single']:
        self.l_precheckErrors.append("Cheek setup not completed: {0}".format(str_cheekSetup))    
                
    if mBlock.scaleSetup:
        self.l_precheckErrors.append("Scale setup not complete")

@cgmGEN.Timer
def rig_dataBuffer(self):
    _short = self.d_block['shortName']
    _str_func = 'rig_dataBuffer'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mModule = self.mModule
    mRigNull = self.mRigNull
    mPrerigNull = mBlock.prerigNull
    self.mPrerigNull = mPrerigNull
    ml_handleJoints = mPrerigNull.msgList_get('handleJoints')
    mMasterNull = self.d_module['mMasterNull']

    
    self.b_scaleSetup = mBlock.scaleSetup
    
    
    for k in ['jaw','muzzle','nose','nostril','cheek','bridge','chin',
              'lip','lipSeal','teeth','tongue','uprJaw']:
        _tag = "{0}Setup".format(k)
        self.__dict__['str_{0}'.format(_tag)] = False
        _v = mBlock.getEnumValueString(_tag)
        if _v != 'none':
            self.__dict__['str_{0}'.format(_tag)] = _v
        log.debug("|{0}| >> self.str_{1} = {2}".format(_str_func,_tag,self.__dict__['str_{0}'.format(_tag)]))    
    
    #Offset ============================================================================ 
    self.v_offset = self.mPuppet.atUtils('get_shapeOffset')
    log.debug("|{0}| >> self.v_offset: {1}".format(_str_func,self.v_offset))    
    log.debug(cgmGEN._str_subLine)
    
    #Size =======================================================================================
    self.v_baseSize = [mBlock.blockScale * v for v in mBlock.baseSize]
    self.f_sizeAvg = MATH.average(self.v_baseSize)
    
    log.debug("|{0}| >> size | self.v_baseSize: {1} | self.f_sizeAvg: {2}".format(_str_func,
                                                                                  self.v_baseSize,
                                                                                  self.f_sizeAvg ))
    
    #Settings =============================================================================
    mModuleParent =  self.d_module['mModuleParent']
    if mModuleParent:
        mSettings = mModuleParent.rigNull.settings
    else:
        log.debug("|{0}| >>  using puppet...".format(_str_func))
        mSettings = self.d_module['mMasterControl'].controlVis

    log.debug("|{0}| >> mSettings | self.mSettings: {1}".format(_str_func,mSettings))
    self.mSettings = mSettings
    
    #rotateOrder =============================================================================
    _str_orientation = self.d_orientation['str']
    _l_orient = [_str_orientation[0],_str_orientation[1],_str_orientation[2]]
    self.ro_base = "{0}{1}{2}".format(_str_orientation[1],_str_orientation[2],_str_orientation[0])
    """
    self.ro_head = "{2}{0}{1}".format(_str_orientation[0],_str_orientation[1],_str_orientation[2])
    self.ro_headLookAt = "{0}{2}{1}".format(_str_orientation[0],_str_orientation[1],_str_orientation[2])
    log.debug("|{0}| >> rotateOrder | self.ro_base: {1}".format(_str_func,self.ro_base))
    log.debug("|{0}| >> rotateOrder | self.ro_head: {1}".format(_str_func,self.ro_head))
    log.debug("|{0}| >> rotateOrder | self.ro_headLookAt: {1}".format(_str_func,self.ro_headLookAt))"""
    log.debug(cgmGEN._str_subLine)

    return True


@cgmGEN.Timer
def rig_skeleton(self):
    _short = self.d_block['shortName']
    
    _str_func = 'rig_skeleton'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
        
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mPrerigNull = self.mPrerigNull
    
    ml_jointsToConnect = []
    ml_jointsToHide = []
    ml_joints = mRigNull.msgList_get('moduleJoints')
    self.d_joints['ml_moduleJoints'] = ml_joints
    
    #---------------------------------------------

    
    
    
    BLOCKUTILS.skeleton_pushSettings(ml_joints, self.d_orientation['str'],
                                     self.d_module['mirrorDirection'])
                                     #d_rotateOrders, d_preferredAngles)
    
    
    #Rig Joints =================================================================================
    ml_rigJoints = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,
                                                           ml_joints,
                                                           'rig',
                                                           self.mRigNull,
                                                           'rigJoints',
                                                           'rig',
                                                           cgmType = False,
                                                           blockNames=False)
    ml_driverJoints = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,
                                                              ml_joints,
                                                              None,
                                                              self.mRigNull,
                                                              'driverJoints',
                                                              'driver',
                                                              cgmType = False,
                                                              blockNames=False)    
    
    for i,mJnt in enumerate(ml_rigJoints):
        mJnt.p_parent = ml_driverJoints[i]
    """
    ml_segmentJoints = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,ml_joints, None,
                                                               mRigNull,'segmentJoints','seg',
                                                               cgmType = 'segJnt')
    ml_jointsToHide.extend(ml_segmentJoints)        """
    
    
    
    
    #Processing  joints ================================================================================
    log.debug("|{0}| >> Processing Joints...".format(_str_func)+ '-'*40)
    
    #Need to sort our joint lists:
    md_skinJoints = {}
    md_rigJoints = {}
    md_segJoints = {}
    md_driverJoints = {}
    md_handles = {}
    md_handleShapes = {}
    
    def doSingleJoint(tag,mParent = None):
        log.debug("|{0}| >> gathering {1}...".format(_str_func,tag))            
        mJntSkin = mPrerigNull.getMessageAsMeta('{0}Joint'.format(tag))
    
        mJntRig = mJntSkin.getMessageAsMeta('rigJoint')
        mJntDriver = mJntSkin.getMessageAsMeta('driverJoint')
    
        if mParent is not None:
            mJntDriver.p_parent = mParent
    
        md_skinJoints[t] = mJntSkin
        md_rigJoints[t] = mJntRig
        md_driverJoints[t] = mJntDriver
        md_handleShapes[t] = mPrerigNull.getMessageAsMeta('{0}ShapeHelper'.format(t))
        
    #Jaw ---------------------------------------------------------------
    if self.str_jawSetup:
        log.debug("|{0}| >> jaw...".format(_str_func))
        mJntSkin = mPrerigNull.getMessageAsMeta('jawJoint')
        mJntRig = mJntSkin.getMessageAsMeta('rigJoint')
        mJntDriver = mJntSkin.getMessageAsMeta('driverJoint')
        
        md_skinJoints['jaw'] = mJntSkin
        md_rigJoints['jaw'] = mJntRig
        md_driverJoints['jaw'] = mJntDriver

        #mJntFK = BLOCKUTILS.skeleton_buildDuplicateChain(mBlock,[mJntSkin],
        #                                                'fk', mRigNull,
        #                                                'fkJaw',
        #                                                cgmType = False,
        #                                                 singleMode = True)[0]
        #md_driverJoints['jaw'] = mJntFK
        #mJntRig.p_parent = mJntFK
        
    
    if self.str_noseSetup:
        log.debug("|{0}| >> nose...".format(_str_func)+'-'*40)
        
        for t in ['noseBase','noseTip','nostrilLeft','nostrilRight']:
            mParent = None
            if t == 'noseBase':
                mParent = False
            doSingleJoint(t,mParent)
            
            """
            log.debug("|{0}| >> gathering {1}...".format(_str_func,t))            
            mJntSkin = mPrerigNull.getMessageAsMeta('{0}Joint'.format(t))

            mJntRig = mJntSkin.getMessageAsMeta('rigJoint')
            mJntDriver = mJntSkin.getMessageAsMeta('driverJoint')
            
            if t in ['noseBase']:
                mJntDriver.p_parent = False
                
            md_skinJoints[t] = mJntSkin
            md_rigJoints[t] = mJntRig
            md_driverJoints[t] = mJntDriver
                
            md_handleShapes[t] = mPrerigNull.getMessageAsMeta('{0}ShapeHelper'.format(t))"""
    
    if self.str_cheekSetup:
        log.debug("|{0}| >> cheek...".format(_str_func))
        for t in ['cheekLeft','cheekRight']:
            doSingleJoint(t,False)
            

    
    #Processing  Handles ================================================================================
    log.debug("|{0}| >> Processing Handles...".format(_str_func)+ '-'*40)

    """
    for k in ['center','left','right']:
        log.debug("|{0}| >> {1}...".format(_str_func,k))        
        ml_skin = self.mPrerigNull.msgList_get('brow{0}Joints'.format(k.capitalize()))
        md_skinJoints['brow'][k] = ml_skin
        ml_rig = []
        ml_seg = []
        
        for mJnt in ml_skin:
            mRigJoint = mJnt.getMessageAsMeta('rigJoint')
            ml_rig.append(mRigJoint)
            
            mSegJoint = mJnt.getMessageAsMeta('segJoint')
            ml_seg.append(mSegJoint)
            mSegJoint.p_parent = False
            
            mRigJoint.p_parent = mSegJoint
            
        md_rigJoints['brow'][k] = ml_rig
        md_segJoints['brow'][k] = ml_seg
        
    log.debug(cgmGEN._str_subLine)
    
    #Brow joints ================================================================================
    log.debug("|{0}| >> Brow Handles...".format(_str_func)+ '-'*40)    
    mBrowCurve = mBlock.getMessageAsMeta('browLineloftCurve')
    _BrowCurve = mBrowCurve.getShapes()[0]
    md_handles = {'brow':{}}
    md_handleShapes = {'brow':{}}
    
    for k in ['center','left','right']:
        log.debug("|{0}| >> {1}...".format(_str_func,k))        
        ml_helpers = self.mPrerigNull.msgList_get('brow{0}PrerigHandles'.format(k.capitalize()))    
        ml_new = []
        for mHandle in ml_helpers:
            mJnt = mHandle.doCreateAt('joint')
            mJnt.doCopyNameTagsFromObject(mHandle.mNode,ignore = ['cgmType'])
            #mJnt.doStore('cgmType','dag')
            mJnt.doName()
            ml_new.append(mJnt)
            ml_joints.append(mJnt)
            JOINT.freezeOrientation(mJnt.mNode)
            mJnt.p_parent = False
            mJnt.p_position = mHandle.masterGroup.p_position
            #DIST.get_closest_point(mHandle.mNode,_BrowCurve,True)[0]

        md_handles['brow'][k] = ml_new
        md_handleShapes['brow'][k] = ml_helpers
        ml_jointsToHide.extend(ml_new)
    log.debug(cgmGEN._str_subLine)
    """
    self.md_rigJoints = md_rigJoints
    self.md_skinJoints = md_skinJoints
    self.md_segJoints = md_segJoints
    self.md_handles = md_handles
    self.md_handleShapes = md_handleShapes
    self.md_driverJoints = md_driverJoints
    
    #...joint hide -----------------------------------------------------------------------------------
    for mJnt in ml_jointsToHide:
        try:mJnt.drawStyle =2
        except:mJnt.radius = .00001
    
    pprint.pprint(vars())
    #...connect... 
    self.fnc_connect_toRigGutsVis( ml_jointsToConnect )        
    return

@cgmGEN.Timer
def rig_shapes(self):
    try:
        _short = self.d_block['shortName']
        _str_func = 'rig_shapes'
        log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
        log.debug("{0}".format(self))
        
    
        mBlock = self.mBlock
        #_baseNameAttrs = ATTR.datList_getAttrs(mBlock.mNode,'nameList')    
        mHandleFactory = mBlock.asHandleFactory()
        mRigNull = self.mRigNull
        mPrerigNull = self.mPrerigNull
        
        ml_rigJoints = mRigNull.msgList_get('rigJoints')
        
        
        if self.md_rigJoints.get('jaw'):
            log.debug("|{0}| >> Jaw setup...".format(_str_func)+ '-'*40)
            mJaw_fk = self.md_driverJoints.get('jaw')
            CORERIG.shapeParent_in_place(mJaw_fk.mNode, mPrerigNull.getMessageAsMeta('jawShapeHelper').mNode)
            
            mRigNull.doStore('controlJaw',mJaw_fk.mNode)
            
        if self.str_muzzleSetup:
            log.debug("|{0}| >> Muzzle setup...".format(_str_func)+ '-'*40)
            mMuzzleDagHelper = mPrerigNull.getMessageAsMeta('muzzleJointHelper')
            mMuzzleDag = mMuzzleDagHelper.doCreateAt()
            mMuzzleDag.doCopyNameTagsFromObject(mMuzzleDagHelper.mNode,'cgmType')
            mMuzzleDag.doName()
            
            CORERIG.shapeParent_in_place(mMuzzleDag.mNode,
                                         mMuzzleDagHelper.getMessageAsMeta('shapeHelper').mNode)
            
            mRigNull.doStore('controlMuzzle',mMuzzleDag.mNode)
            
        
        if self.str_cheekSetup:
            log.debug("|{0}| >> cheek setup...".format(_str_func)+ '-'*40)
            for k in ['cheekLeft','cheekRight']:
                mDriver = self.md_driverJoints.get(k)
                CORERIG.shapeParent_in_place(mDriver.mNode, self.md_handleShapes[k].mNode)
                
        
        if self.str_noseSetup:
            log.debug("|{0}| >> nose setup...".format(_str_func)+ '-'*40)
            
            for k in ['noseBase','noseTip','nostrilLeft','nostrilRight']:
                mDriver = self.md_driverJoints.get(k)
                if mDriver:
                    log.debug("|{0}| >> found: {1}".format(_str_func,k))
                    CORERIG.shapeParent_in_place(mDriver.mNode, self.md_handleShapes[k].mNode)
                    
                    
            
            
        
        """
        #Brow center ================================================================================
        mBrowCenter = self.md_handles['brow']['center'][0].doCreateAt()
        mBrowCenterShape = self.md_handleShapes['brow']['center'][0].doDuplicate(po=False)
        mBrowCenterShape.scale = [1.5,1.5,1.5]
        
        mBrowCenter.doStore('cgmName','browMain')
        mBrowCenter.doName()
        
        CORERIG.shapeParent_in_place(mBrowCenter.mNode,
                                     mBrowCenterShape.mNode,False)
        
        mRigNull.connectChildNode(mBrowCenter,'browMain','rigNull')#Connect
        
        
        #Handles ================================================================================
        log.debug("|{0}| >> Handles...".format(_str_func)+ '-'*80)
        for k,d in self.md_handles.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    CORERIG.shapeParent_in_place(mHandle.mNode,
                                                 self.md_handleShapes[k][side][i].mNode)
                    
                    if side == 'center':
                        mHandleFactory.color(mHandle.mNode,side='center',controlType='sub')"""
                        
        #Direct ================================================================================
        log.debug("|{0}| >> Direct...".format(_str_func)+ '-'*80)
        for k,d in self.md_rigJoints.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            
            if VALID.isListArg(d):
                for i,mHandle in enumerate(d):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    side = mHandle.getMayaAttr('cgmDirection') or False
                    crv = CURVES.create_fromName(name='cube',
                                                 direction = 'z+',
                                                 size = mHandle.radius*2)
                    SNAP.go(crv,mHandle.mNode)
                    mHandleFactory.color(crv,side=side,controlType='sub')
                    CORERIG.shapeParent_in_place(mHandle.mNode,
                                                 crv,keepSource=False)                
            elif issubclass(type(d),dict):
                for side,ml in d.iteritems():
                    log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                    for i,mHandle in enumerate(ml):
                        log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                        crv = CURVES.create_fromName(name='cube',
                                                     direction = 'z+',
                                                     size = mHandle.radius*2)
                        SNAP.go(crv,mHandle.mNode)
                        mHandleFactory.color(crv,side=side,controlType='sub')
                        CORERIG.shapeParent_in_place(mHandle.mNode,
                                                     crv,keepSource=False)
            else:
                log.debug("|{0}| >> {1}...".format(_str_func,d))
                side = d.getMayaAttr('cgmDirection') or 'center'                
                crv = CURVES.create_fromName(name='cube',
                                             direction = 'z+',
                                             size = d.radius*2)
                SNAP.go(crv,d.mNode)
                mHandleFactory.color(crv,side=side,controlType='sub')
                CORERIG.shapeParent_in_place(d.mNode,
                                             crv,keepSource=False)                
                    
                    
        for mJnt in ml_rigJoints:
            try:
                mJnt.drawStyle =2
            except:
                mJnt.radius = .00001                
        return
    except Exception,error:
        cgmGEN.cgmException(Exception,error,msg=vars())


@cgmGEN.Timer
def rig_controls(self):
    try:
        _short = self.d_block['shortName']
        _str_func = 'rig_controls'
        log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
        log.debug("{0}".format(self))
      
        mRigNull = self.mRigNull
        mBlock = self.mBlock
        ml_controlsAll = []#we'll append to this list and connect them all at the end
        mRootParent = self.mDeformNull
        ml_segmentHandles = []
        ml_rigJoints = mRigNull.msgList_get('rigJoints')
        
        #mPlug_visSub = self.atBuilderUtils('build_visSub')
        mPlug_visDirect = cgmMeta.cgmAttr(self.mSettings,'visDirect_{0}'.format(self.d_module['partName']),
                                          value = True,
                                          attrType='bool',
                                          defaultValue = False,
                                          keyable = False,hidden = False)
        
        
        
        def simpleRegister(mObj):
            _d = MODULECONTROL.register(mObj,
                                        mirrorSide= self.d_module['mirrorDirection'],
                                        mirrorAxis="translateX,rotateY,rotateZ",
                                        makeAimable = False)
            ml_controlsAll.append(_d['mObj'])            
            return _d['mObj']
        
        for link in ['controlJaw','controlMuzzle']:
            mLink = mRigNull.getMessageAsMeta(link)
            if mLink:
                log.debug("|{0}| >> {1}...".format(_str_func,link))
                
                _d = MODULECONTROL.register(mLink,
                                            mirrorSide= self.d_module['mirrorDirection'],
                                            mirrorAxis="translateX,rotateY,rotateZ",
                                            makeAimable = False)
                
                ml_controlsAll.append(_d['mObj'])        
                #ml_segmentHandles.append(_d['mObj'])
                
        if self.str_cheekSetup:
            log.debug("|{0}| >> cheek setup...".format(_str_func)+ '-'*40)
            for k in ['cheekLeft','cheekRight']:
                log.debug("|{0}| >> {1}...".format(_str_func,k))
                simpleRegister(self.md_driverJoints.get(k))


        if self.str_noseSetup:
            log.debug("|{0}| >> nose setup...".format(_str_func)+ '-'*40)
            
            for k in ['noseBase','noseTip','nostrilLeft','nostrilRight']:
                log.debug("|{0}| >> {1}...".format(_str_func,k))
                simpleRegister(self.md_driverJoints.get(k))

        """
        #Handles ================================================================================
        log.debug("|{0}| >> Handles...".format(_str_func)+ '-'*80)
        for k,d in self.md_handles.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    _d = MODULECONTROL.register(mHandle,
                                                mirrorSide= side,
                                                mirrorAxis="translateX,rotateY,rotateZ",
                                                makeAimable = True)
                    
                    ml_controlsAll.append(_d['mObj'])
                    ml_segmentHandles.append(_d['mObj'])"""
                    
        #Direct ================================================================================
        log.debug("|{0}| >> Direct...".format(_str_func)+ '-'*80)
        for mHandle in ml_rigJoints:
            log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
            side = mHandle.getMayaAttr('cgmDirection') or 'center'
            
            _d = MODULECONTROL.register(mHandle,
                                        typeModifier='direct',
                                        mirrorSide= side,
                                        mirrorAxis="translateX,rotateY,rotateZ",
                                        makeAimable = False)
        
            mObj = _d['mObj']
        
            ml_controlsAll.append(_d['mObj'])
        
            if mObj.hasAttr('cgmIterator'):
                ATTR.set_hidden(mObj.mNode,'cgmIterator',True)        
        
            for mShape in mObj.getShapes(asMeta=True):
                ATTR.connect(mPlug_visDirect.p_combinedShortName, "{0}.overrideVisibility".format(mShape.mNode))            
            
        
        """
        for k,d in self.md_rigJoints.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
            for side,ml in d.iteritems():
                log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
                for i,mHandle in enumerate(ml):
                    log.debug("|{0}| >> {1}...".format(_str_func,mHandle))
                    _d = MODULECONTROL.register(mHandle,
                                                typeModifier='direct',
                                                mirrorSide= side,
                                                mirrorAxis="translateX,rotateY,rotateZ",
                                                makeAimable = False)
                    
                    mObj = _d['mObj']
                    
                    ml_controlsAll.append(_d['mObj'])
                    
                    ATTR.set_hidden(mObj.mNode,'radius',True)        
                    if mObj.hasAttr('cgmIterator'):
                        ATTR.set_hidden(mObj.mNode,'cgmIterator',True)        
                
                    for mShape in mObj.getShapes(asMeta=True):
                        ATTR.connect(mPlug_visDirect.p_combinedShortName, "{0}.overrideVisibility".format(mShape.mNode))"""                    


        #Close out...
        mHandleFactory = mBlock.asHandleFactory()
        for mCtrl in ml_controlsAll:
            ATTR.set(mCtrl.mNode,'rotateOrder',self.ro_base)
            
            if mCtrl.hasAttr('radius'):
                ATTR.set(mCtrl.mNode,'radius',0)        
                ATTR.set_hidden(mCtrl.mNode,'radius',True)        
            
            ml_pivots = mCtrl.msgList_get('spacePivots')
            if ml_pivots:
                log.debug("|{0}| >> Coloring spacePivots for: {1}".format(_str_func,mCtrl))
                for mPivot in ml_pivots:
                    mHandleFactory.color(mPivot.mNode, controlType = 'sub')            
        """
        if mHeadIK:
            ATTR.set(mHeadIK.mNode,'rotateOrder',self.ro_head)
        if mHeadLookAt:
            ATTR.set(mHeadLookAt.mNode,'rotateOrder',self.ro_headLookAt)
            """
        
        mRigNull.msgList_connect('handleJoints',ml_segmentHandles,'rigNull')        
        mRigNull.msgList_connect('controlsAll',ml_controlsAll)
        mRigNull.moduleSet.extend(ml_controlsAll)
        
    except Exception,error:
        cgmGEN.cgmException(Exception,error,msg=vars())


@cgmGEN.Timer
def rig_frame(self):
    _short = self.d_block['shortName']
    _str_func = ' rig_rigFrame'
    
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))    

    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mRootParent = self.mDeformNull
    mModule = self.mModule
    mDeformNull = self.mDeformNull
    mFollowParent = self.mDeformNull
    mFollowBase = self.mDeformNull
    
    mdD = self.md_driverJoints
    #Process our main controls ==============================================================
    mMuzzle = mRigNull.getMessageAsMeta('controlMuzzle')
    mJaw = mRigNull.getMessageAsMeta('controlJaw')
    
    if mMuzzle:
        log.debug("|{0}| >> Muzzle setup...".format(_str_func))
        mFollowParent = mMuzzle
        mFollowBase = mMuzzle.doCreateAt('null',setClass=True)
        mFollowBase.rename('{0}_followBase'.format(self.d_module['partName']))
        mFollowBase.p_parent = self.mDeformNull
        
    if mJaw:
        log.debug("|{0}| >> Jaw setup...".format(_str_func))
        mJaw.masterGroup.p_parent = mFollowParent
        if not mMuzzle:
            mFollowParent = mJaw
        
        
    if self.str_cheekSetup:
        log.debug("|{0}| >> cheek setup...".format(_str_func)+ '-'*40)
        for k in ['cheekLeft','cheekRight']:
            log.debug("|{0}| >> {1}...".format(_str_func,k))
            mdD[k].masterGroup.p_parent = self.mDeformNull
            mc.parentConstraint([mFollowBase.mNode, mJaw.mNode],
                                mdD[k].masterGroup.mNode,maintainOffset=True)
            
    
    
    if self.str_noseSetup:
        log.debug("|{0}| >> nose setup...".format(_str_func)+ '-'*40)
        mdD['noseBase'].masterGroup.p_parent = mDeformNull
        
        mTrack = mdD['noseBase'].masterGroup.doLoc()
        mTrack.p_parent = mFollowParent
        mc.pointConstraint([mFollowBase.mNode, mTrack.mNode],
                            mdD['noseBase'].masterGroup.mNode,maintainOffset=True)
        
        mc.aimConstraint(mFollowBase.mNode, mdD['noseBase'].masterGroup.mNode, maintainOffset = True,
                         aimVector = [0,1,0], upVector = [0,0,1], 
                         worldUpObject = mFollowBase.mNode,
                         worldUpType = 'objectrotation', 
                         worldUpVector = [0,0,1])

        for k in ['noseBase','noseTip','nostrilLeft','nostrilRight']:
            pass
    
    
    
    """
    mBrowMain = mRigNull.browMain
    mBrowMain.masterGroup.p_parent = self.mDeformNull
    
    #Parenting ============================================================================
    log.debug("|{0}| >>Parenting...".format(_str_func)+ '-'*80)
    
    for k,d in self.md_handles.iteritems():
        log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
        for side,ml in d.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
            for i,mHandle in enumerate(ml):
                mHandle.masterGroup.p_parent = self.mDeformNull
                
    for k,d in self.md_segJoints.iteritems():
        log.debug("|{0}| >> {1}...".format(_str_func,k)+ '-'*40)
        for side,ml in d.iteritems():
            log.debug("|{0}| >> {1}...".format(_str_func,side)+ '-'*10)
            for i,mHandle in enumerate(ml):
                mHandle.p_parent = self.mDeformNull
        
    
    #Brow Ribbon ============================================================================
    log.debug("|{0}| >> Brow ribbon...".format(_str_func)+ '-'*80)
    
    md_seg = self.md_segJoints
    md_brow = md_seg['brow']
    ml_right = copy.copy(md_brow['right'])
    ml_center = md_brow['center']
    ml_left = md_brow['left']
    ml_right.reverse()
    
    ml_ribbonJoints = ml_right + ml_center + ml_left
    
    md_handles = self.md_handles
    md_brow = md_handles['brow']
    ml_rightHandles = copy.copy(md_brow['right'])
    ml_centerHandles = md_brow['center']
    ml_leftHandles = md_brow['left']
    ml_rightHandles.reverse()    
    
    
    ml_skinDrivers = ml_rightHandles + ml_centerHandles + ml_leftHandles
    
    d_ik = {'jointList':[mObj.mNode for mObj in ml_ribbonJoints],
            'baseName' : self.d_module['partName'] + '_ikRibbon',
            'orientation':'xyz',
            'loftAxis' : 'z',
            'tightenWeights':False,
            'driverSetup':'stableBlend',
            'squashStretch':None,
            'connectBy':'constraint',
            'squashStretchMain':'arcLength',
            'paramaterization':'fixed',#mBlock.getEnumValueString('ribbonParam'),
            #masterScalePlug:mPlug_masterScale,
            #'settingsControl': mSettings.mNode,
            'extraSquashControl':True,
            'influences':ml_skinDrivers,
            'moduleInstance' : self.mModule}    
    
    
    res_ribbon = IK.ribbon(**d_ik)
    
    #Setup some constraints============================================================================
    md_brow['center'][0].masterGroup.p_parent = mBrowMain
    
    mc.pointConstraint([md_brow['left'][0].mNode, md_brow['right'][0].mNode],
                       md_brow['center'][0].masterGroup.mNode,
                       maintainOffset=True)
    
    
    for side in ['left','right']:
        ml = md_brow[side]
        ml[0].masterGroup.p_parent = mBrowMain
        mc.pointConstraint([ml[0].mNode, ml[-1].mNode],
                           ml[1].masterGroup.mNode,
                           maintainOffset=True)
        """
        
        
    pprint.pprint(vars())

    return


@cgmGEN.Timer
def rig_cleanUp(self):
    _short = self.d_block['shortName']
    _str_func = 'rig_cleanUp'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    
    mMasterControl= self.d_module['mMasterControl']
    mMasterDeformGroup= self.d_module['mMasterDeformGroup']    
    mMasterNull = self.d_module['mMasterNull']
    mModuleParent = self.d_module['mModuleParent']
    mPlug_globalScale = self.d_module['mPlug_globalScale']
    

    #Settings =================================================================================
    #log.debug("|{0}| >> Settings...".format(_str_func))
    #mSettings.visDirect = 0
    
    #mPlug_FKIK = cgmMeta.cgmAttr(mSettings,'FKIK')
    #mPlug_FKIK.p_defaultValue = 1
    #mPlug_FKIK.value = 1
        
    #Lock and hide =================================================================================
    ml_controls = mRigNull.msgList_get('controlsAll')
    
    for mCtrl in ml_controls:
        if mCtrl.hasAttr('radius'):
            ATTR.set_hidden(mCtrl.mNode,'radius',True)
        
        for link in 'masterGroup','dynParentGroup','aimGroup','contraintGroup':
            if mCtrl.getMessage(link):
                mCtrl.getMessageAsMeta(link).dagLock(True)
    
    if not mBlock.scaleSetup:
        log.debug("|{0}| >> No scale".format(_str_func))
        ml_controlsToLock = copy.copy(ml_controls)
        for mCtrl in ml_controlsToLock:
            ATTR.set_standardFlags(mCtrl.mNode, ['scale'])
    else:
        log.debug("|{0}| >>  scale setup...".format(_str_func))
        
        
    self.mDeformNull.dagLock(True)

    #Close out ===============================================================================================
    mRigNull.version = self.d_block['buildVersion']
    mBlock.blockState = 'rig'
    mBlock.UTILS.set_blockNullTemplateState(mBlock)
    self.UTILS.rigNodes_store(self)


def create_simpleMesh(self,  deleteHistory = True, cap=True):
    _str_func = 'create_simpleMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    #>> Head ===================================================================================
    log.debug("|{0}| >> Head...".format(_str_func))
    
    mGroup = self.msgList_get('headMeshProxy')[0].getParent(asMeta=True)
    l_headGeo = mGroup.getChildren(asMeta=False)
    ml_headStuff = []
    for i,o in enumerate(l_headGeo):
        log.debug("|{0}| >> geo: {1}...".format(_str_func,o))                    
        if ATTR.get(o,'v'):
            log.debug("|{0}| >> visible head: {1}...".format(_str_func,o))            
            mObj = cgmMeta.validateObjArg(mc.duplicate(o, po=False, ic = False)[0])
            ml_headStuff.append(  mObj )
            mObj.p_parent = False
        

    if self.neckBuild:#...Neck =====================================================================
        log.debug("|{0}| >> neckBuild...".format(_str_func))    
        ml_neckMesh = self.UTILS.create_simpleLoftMesh(self,deleteHistory,cap)
        ml_headStuff.extend(ml_neckMesh)
        
    _mesh = mc.polyUnite([mObj.mNode for mObj in ml_headStuff],ch=False)
    _mesh = mc.rename(_mesh,'{0}_0_geo'.format(self.p_nameBase))
    
    return cgmMeta.validateObjListArg(_mesh)

def asdfasdfasdf(self, forceNew = True, skin = False):
    """
    Build our proxyMesh
    """
    _short = self.d_block['shortName']
    _str_func = 'build_proxyMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    mHeadIK = mRigNull.headIK
    mSettings = mRigNull.settings
    mPuppetSettings = self.d_module['mMasterControl'].controlSettings
    
    ml_rigJoints = mRigNull.msgList_get('rigJoints',asMeta = True)
    if not ml_rigJoints:
        raise ValueError,"No rigJoints connected"

    #>> If proxyMesh there, delete --------------------------------------------------------------------------- 
    _bfr = mRigNull.msgList_get('proxyMesh',asMeta=True)
    if _bfr:
        log.debug("|{0}| >> proxyMesh detected...".format(_str_func))            
        if forceNew:
            log.debug("|{0}| >> force new...".format(_str_func))                            
            mc.delete([mObj.mNode for mObj in _bfr])
        else:
            return _bfr
        
    #>> Head ===================================================================================
    log.debug("|{0}| >> Head...".format(_str_func))
    if directProxy:
        log.debug("|{0}| >> directProxy... ".format(_str_func))
        _settings = self.mRigNull.settings.mNode
        
    
    mGroup = mBlock.msgList_get('headMeshProxy')[0].getParent(asMeta=True)
    l_headGeo = mGroup.getChildren(asMeta=False)
    l_vis = mc.ls(l_headGeo, visible = True)
    ml_headStuff = []
    
    for i,o in enumerate(l_vis):
        log.debug("|{0}| >> visible head: {1}...".format(_str_func,o))
        
        mObj = cgmMeta.validateObjArg(mc.duplicate(o, po=False, ic = False)[0])
        ml_headStuff.append(  mObj )
        mObj.parent = ml_rigJoints[-1]
        
        ATTR.copy_to(ml_rigJoints[-1].mNode,'cgmName',mObj.mNode,driven = 'target')
        mObj.addAttr('cgmIterator',i)
        mObj.addAttr('cgmType','proxyGeo')
        mObj.doName()
        
        if directProxy:
            CORERIG.shapeParent_in_place(ml_rigJoints[-1].mNode,mObj.mNode,True,False)
            CORERIG.colorControl(ml_rigJoints[-1].mNode,_side,'main',directProxy=True)        
        
    if mBlock.neckBuild:#...Neck =====================================================================
        log.debug("|{0}| >> neckBuild...".format(_str_func))


def build_proxyMesh(self, forceNew = True, puppetMeshMode = False):
    """
    Build our proxyMesh
    """
    _short = self.d_block['shortName']
    _str_func = 'build_proxyMesh'
    log.debug("|{0}| >>  ".format(_str_func)+ '-'*80)
    log.debug("{0}".format(self))
    
     
    mBlock = self.mBlock
    mRigNull = self.mRigNull
    m#Settings = mRigNull.settings
    mPuppetSettings = self.d_module['mMasterControl'].controlSettings
    mPrerigNull = mBlock.prerigNull
    #directProxy = mBlock.proxyDirect
    
    _side = BLOCKUTILS.get_side(self.mBlock)
    
    ml_rigJoints = mRigNull.msgList_get('rigJoints',asMeta = True)
    if not ml_rigJoints:
        raise ValueError,"No rigJoints connected"
    self.v_baseSize = [mBlock.blockScale * v for v in mBlock.baseSize]
    
    #>> If proxyMesh there, delete --------------------------------------------------------------------------- 
    if puppetMeshMode:
        _bfr = mRigNull.msgList_get('puppetProxyMesh',asMeta=True)
        if _bfr:
            log.debug("|{0}| >> puppetProxyMesh detected...".format(_str_func))            
            if forceNew:
                log.debug("|{0}| >> force new...".format(_str_func))                            
                mc.delete([mObj.mNode for mObj in _bfr])
            else:
                return _bfr        
    else:
        _bfr = mRigNull.msgList_get('proxyMesh',asMeta=True)
        if _bfr:
            log.debug("|{0}| >> proxyMesh detected...".format(_str_func))            
            if forceNew:
                log.debug("|{0}| >> force new...".format(_str_func))                            
                mc.delete([mObj.mNode for mObj in _bfr])
            else:
                return _bfr
        
    ml_proxy = []
    ml_curves = []
    
    
    #Jaw -------------
    mJaw = mRigNull.getMessageAsMeta('controlJaw')
    if mJaw:
        log.debug("|{0}| >> jaw...".format(_str_func))
        mLoftSurface =  mBlock.jawTemplateLoft.doDuplicate(po=False,ic=False)
        #nurbsToPoly -mnd 1  -ch 1 -f 1 -pt 1 -pc 200 -chr 0.9 -ft 0.01 -mel 0.001 -d 0.1 -ut 1 -un 3 -vt 1 -vn 3 -uch 0 -ucr 0 -cht 0.01 -es 0 -ntr 0 -mrt 0 -uss 1 "jaw_fk_anim_Transform";
        _surf = mc.nurbsToPoly(mLoftSurface.mNode, mnd=1, f=1, pt = 1,ch=0, pc=200, chr = .9, ft=.01, mel = .001, d = .1, ut=1, un = 3, vt=1, vn=3, uch = 0, cht = .01, ntr = 0, mrt = 0, uss = 1 )
        mDag = mJaw.doCreateAt()
        CORERIG.shapeParent_in_place(mDag.mNode,_surf,False) 
        ml_proxy.append(mDag)
        #mLoftSurface.p_parent = False
        mDag.p_parent = mJaw
        
    
    ml_drivers = mRigNull.msgList_get('driverJoints')
    for mObj in ml_drivers:
        if mObj.getMayaAttr('cgmName')=='noseBase':
            log.debug("|{0}| >> noseBase...".format(_str_func))
            mLoftSurface =  mBlock.noseTemplateLoft.doDuplicate(po=False,ic=False)
            _surf = mc.nurbsToPoly(mLoftSurface.mNode, mnd=1, f=1, pt = 1,ch=0, pc=200, chr = .9, ft=.01, mel = .001, d = .1, ut=1, un = 3, vt=1, vn=3, uch = 0, cht = .01, ntr = 0, mrt = 0, uss = 1 )
            mDag = mObj.doCreateAt()
            CORERIG.shapeParent_in_place(mDag.mNode,_surf,False) 
            ml_proxy.append(mDag)
            #mLoftSurface.p_parent = False
            mDag.p_parent = mObj            
        



    for mProxy in ml_proxy:
        CORERIG.colorControl(mProxy.mNode,_side,'main',transparent=False,proxy=True)
        mc.makeIdentity(mProxy.mNode, apply = True, t=1, r=1,s=1,n=0,pn=1)

        #Vis connect -----------------------------------------------------------------------
        mProxy.overrideEnabled = 1
        ATTR.connect("{0}.proxyVis".format(mPuppetSettings.mNode),"{0}.visibility".format(mProxy.mNode) )
        ATTR.connect("{0}.proxyLock".format(mPuppetSettings.mNode),"{0}.overrideDisplayType".format(mProxy.mNode) )
        for mShape in mProxy.getShapes(asMeta=1):
            str_shape = mShape.mNode
            mShape.overrideEnabled = 0
            #ATTR.connect("{0}.proxyVis".format(mPuppetSettings.mNode),"{0}.visibility".format(str_shape) )
            ATTR.connect("{0}.proxyLock".format(mPuppetSettings.mNode),"{0}.overrideDisplayTypes".format(str_shape) )
            
    #if directProxy:
    #    for mObj in ml_rigJoints:
    #        for mShape in mObj.getShapes(asMeta=True):
                #mShape.overrideEnabled = 0
    #            mShape.overrideDisplayType = 0
    #            ATTR.connect("{0}.visDirect".format(_settings), "{0}.overrideVisibility".format(mShape.mNode))
        
        

    
    mRigNull.msgList_connect('proxyMesh', ml_proxy + ml_curves)




















