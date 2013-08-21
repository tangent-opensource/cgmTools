# From Python =============================================================
import copy
import re

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
#from Red9.core import Red9_General as r9General

# From cgm ==============================================================
from cgm.core import cgm_General as cgmGeneral
from cgm.core import cgm_Meta as cgmMeta
from cgm.core.rigger.lib import joint_Utils as jntUtils
from cgm.core.classes import GuiFactory as gui

from cgm.lib import (cgmMath,
                     joints,
                     rigging,
                     attributes,
                     locators,
                     distance,
                     autoname,
                     search,
                     curves,
                     dictionary,
                     lists,
                     settings,
                     modules)
reload(joints)
reload(cgmMath)
from cgm.core.lib import nameTools

#>>> Register rig functions
#=====================================================================
from cgm.core.rigger.lib.Limb import (spine,neckHead,leg,clavicle,arm,finger,thumb)
d_moduleTypeToBuildModule = {'torso':spine,
                             'neckhead':neckHead,
                             'leg':leg,
                             'arm':arm,
                             'clavicle':clavicle,
                             'thumb':thumb,
                             'finger':finger,
                            } 
for module in d_moduleTypeToBuildModule.keys():
    reload(d_moduleTypeToBuildModule[module])

typesDictionary = dictionary.initializeDictionary(settings.getTypesDictionaryFile())
namesDictionary = dictionary.initializeDictionary( settings.getNamesDictionaryFile())
settingsDictionary = dictionary.initializeDictionary( settings.getSettingsDictionaryFile())
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
class go(object):
    @cgmGeneral.Timer
    def __init__(self,moduleInstance,forceNew = True,saveTemplatePose = True,**kws): 
        """
        To do:
        Add rotation order settting
        Add module parent check to make sure parent is templated to be able to move forward, or to constrain
        Add any other piece meal data necessary
        Add a cleaner to force a rebuild
        """
        # Get our base info
        #==============	        
        #>>> module null data 
        assert moduleInstance.mClass in ['cgmModule','cgmLimb'],"Not a module"
        assert moduleInstance.isTemplated(),"Module is not templated"
        #assert object is templated
        #assert ...
        log.debug(">>> JointFactory.go.__init__")
        self.cls = "JointFactory.go"
	self._cgmClass = "JointFactory.go"
        self._i_module = moduleInstance# Link for shortness
        
        if moduleInstance.isSkeletonized():
            if forceNew:
                deleteSkeleton(moduleInstance)
            else:
                log.warning("'%s' has already been skeletonized"%moduleInstance.getShortName())
                return        
        
        #>>> store template settings
        if saveTemplatePose:
            log.debug("Saving template pose in JointFactory.go")
            self._i_module.storeTemplatePose()
        
        self.rigNull = self._i_module.getMessage('rigNull')[0] or False
        self._i_rigNull = self._i_module.rigNull
        self.moduleColors = self._i_module.getModuleColors()
        self.l_coreNames = self._i_module.coreNames.value
        self.foundDirections = False #Placeholder to see if we have it
                
        #>>> part name 
        self._partName = self._i_module.getPartNameBase()
        self._partType = self._i_module.moduleType.lower() or False
        self._strShortName = self._i_module.getShortName() or False
	
        self.direction = None
        if self._i_module.hasAttr('cgmDirection'):
            self.direction = self._i_module.cgmDirection or None
        
        #>>> template null 
        self.i_templateNull = self._i_module.templateNull
        self.curveDegree = self.i_templateNull.curveDegree
	
        #>>> Gather info
        #=========================================================	
        self._l_coreNames = self._i_module.coreNames.value        
        #>>> Instances and joint stuff
        self.jointOrientation = modules.returnSettingsData('jointOrientation')
        self.i_root = self.i_templateNull.root
        self.i_orientRootHelper = self.i_templateNull.orientRootHelper
        self.i_curve = self.i_templateNull.curve
        self._ml_controlObjects = self.i_templateNull.msgList_get('controlObjects')
        self._d_handleToHandleJoints = {}
	
        log.debug("Module: %s"%self._i_module.getShortName())
        log.debug("partType: %s"%self._partType)
        log.debug("direction: %s"%self.direction) 
        log.debug("colors: %s"%self.moduleColors)
        log.debug("coreNames: %s"%self.l_coreNames)
        log.debug("root: %s"%self.i_root.getShortName())
        log.debug("curve: %s"%self.i_curve.getShortName())
        log.debug("orientRootHelper: %s"%self.i_orientRootHelper.getShortName())
        log.debug("rollJoints: %s"%self.i_templateNull.rollJoints)
        log.debug("jointOrientation: %s"%self.jointOrientation)
        log.debug("hasJointSetup: %s"%hasJointSetup(self))
	if not hasJointSetup(self):
	    raise StandardError, "Need to add to build dict"
	
	#Skeletonize
	self.str_progressBar = gui.doStartMayaProgressBar(4)
	try:
	    if self._i_module.mClass == 'cgmLimb':
		log.debug("mode: cgmLimb Skeletonize")
		mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Skeletonize'), progress=0)    		
		doSkeletonize(self)
		
		mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Special Joints'), progress=4)    				
		self.build(self)
		#Only going to tag our handleJoints at the very end because of message connection duplication
		for i_obj in self._ml_controlObjects:
		    i_obj.connectChildNode(self._d_handleToHandleJoints[i_obj],'handleJoint')	    
	    else:
		raise NotImplementedError,"haven't implemented '%s' templatizing yet"%self._i_module.mClass
	except StandardError,error:
	    raise StandardError,"%s.go >> build failed! | %s"%(self._strShortName,error)
	gui.doEndMayaProgressBar(self.str_progressBar)#Close out this progress bar        
	
def hasJointSetup(self):
    if not issubclass(type(self),go):
	log.error("Not a JointFactory.go instance: '%s'"%self)
	raise StandardError
    self = self#Link
    log.debug(">>> %s.hasJointSetup >> "%(self._strShortName) + "="*75)      
    
    if self._partType not in d_moduleTypeToBuildModule.keys():
	log.debug("%s.isBuildable>>> '%s' Not in d_moduleTypeToBuildModule"%(self._strShortName,self._partType))	
	return False
    
    try:#Version
	self._buildVersion = d_moduleTypeToBuildModule[self._partType].__version__    
    except:
	log.error("%s.isBuildable>>> Missing version"%(self._strShortName))	
	return False
    
    try:#Joints list
	self.build = d_moduleTypeToBuildModule[self._partType].__bindSkeletonSetup__
	self.buildModule = d_moduleTypeToBuildModule[self._partType]
    except:
	log.error("%s.isBuildable>>> Missing Joint Setup Function"%(self._strShortName))	
	return False	
    
    return True    
	
#@r9General.Timer
def doSkeletonize(self):
    """ 
    DESCRIPTION:
    Basic limb skeletonizer
    
    ARGUMENTS:
    stiffIndex(int) - the index of the template objects you want to not have roll joints
                      For example, a value of -1 will let the chest portion of a spine 
                      segment be solid instead of having a roll segment. Default is the modules setting
    RETURNS:
    l_limbJoints(list)
    """
    # Get our base info
    #==================	        
    assert self.cls == 'JointFactory.go',"Not a JointFactory.go instance!"
    assert mc.objExists(self._i_module.mNode),"module no longer exists"
    curve = self.i_curve.mNode
    partName = self._partName
    l_limbJoints = []
    
    log.debug(">>> %s.doSkeletonize >> "%self._strShortName + "="*75)            
    
    #>>> Check roll joint args
    rollJoints = self.i_templateNull.rollJoints
    d_rollJointOverride = self.i_templateNull.rollOverride
    if type(d_rollJointOverride) is not dict:
        d_rollJointOverride = False
    
    #>>> See if we have have a suitable parent joint to use
    # We'll know it is if the first template position shares an equivalent position with it's parentModule
    #======================================================
    i_parentJointToUse = False
    
    pos = distance.returnWorldSpacePosition( self._ml_controlObjects[0].mNode )
    log.debug("pos: %s"%pos)
    #Get parent position, if we have one
    if self._i_module.getMessage('moduleParent'):
        log.debug("Found moduleParent, checking joints...")
        i_parentRigNull = self._i_module.moduleParent.rigNull
        parentJoints = i_parentRigNull.msgList_getMessage('moduleJoints')
        log.debug(parentJoints)
        if parentJoints:
            parent_pos = distance.returnWorldSpacePosition( parentJoints[-1] )
            log.debug("parentPos: %s"%parent_pos)  
            
        log.debug("Equivalent: %s"%cgmMath.isVectorEquivalent(pos,parent_pos))
        if cgmMath.isVectorEquivalent(pos,parent_pos):#if they're equivalent
            i_parentJointToUse = cgmMeta.cgmObject(parentJoints[-1])
            
    #>>> Make if our segment only has one handle
    #==========================================	
    mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Parent Check...'), progress=1)    				    
    self.b_parentStole = False
    if len(self._ml_controlObjects) == 1:
        if i_parentJointToUse:
            log.debug("Single joint: moduleParent mode")
            #Need to grab the last joint for this module
            l_limbJoints = [parentJoints[-1]]
            i_parentRigNull.msgList_connect(parentJoints[:-1],'moduleJoints','rigNull')
	    self.b_parentStole = True	    
        else:
            log.debug("Single joint: no parent mode")
            l_limbJoints.append ( mc.joint (p=(pos[0],pos[1],pos[2]))) 
    else:
        if i_parentJointToUse:
            #We're going to reconnect all but the last joint back to the parent module and delete the last parent joint which we're replacing
            i_parentRigNull.msgList_connect(parentJoints[:-1],'moduleJoints','rigNull')
            mc.delete(i_parentJointToUse.mNode)
	    self.b_parentStole = True
            
        #>>> Make the limb segment
        #==========================	
	mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Making segment joints...'), progress=1)    				    	
        l_spanUPositions = []
        #>>> Divide stuff
        for i_obj in self._ml_controlObjects:#These are our base span u positions on the curve
            l_spanUPositions.append(distance.returnNearestPointOnCurveInfo(i_obj.mNode,curve)['parameter'])
        l_spanSegmentUPositions = lists.parseListToPairs(l_spanUPositions)
        #>>>Get div per span
        l_spanDivs = self._i_module.get_rollJointCountList() or []
	"""
        for segment in l_spanSegmentUPositions:
            l_spanDivs.append(rollJoints)
            
        if d_rollJointOverride:
            for k in d_rollJointOverride.keys():
                try:
                    l_spanDivs[int(k)]#If the arg passes
                    l_spanDivs[int(k)] = d_rollJointOverride.get(k)#Override the roll value
                except:log.warning("%s:%s rollOverride arg failed"%(k,d_rollJointOverride.get(k)))
        """
        log.debug("l_spanSegmentUPositions: %s"%l_spanSegmentUPositions)
        log.debug("l_spanDivs: %s"%l_spanDivs)
        
        #>>>Get div per span 
        l_jointUPositions = []
        for i,segment in enumerate(l_spanSegmentUPositions):#Split stuff up
            #Get our span u value distance
            length = segment[1]-segment[0]
            div = length / (l_spanDivs[i] +1)
            tally = segment[0]
            l_jointUPositions.append(tally)
            for i in range(l_spanDivs[i] +1)[1:]:
                tally = segment[0]+(i*div)
                l_jointUPositions.append(tally)
        l_jointUPositions.append(l_spanUPositions[-1])
                
        l_jointPositions = []
        for u in l_jointUPositions:
            l_jointPositions.append(mc.pointPosition("%s.u[%f]"%(curve,u)))
            
        #>>> Remove the duplicate positions"""
        l_jointPositions = lists.returnPosListNoDuplicates(l_jointPositions)
        #>>> Actually making the joints
        for pos in l_jointPositions:
            l_limbJoints.append ( mc.joint (p=(pos[0],pos[1],pos[2]))) 
               
    #>>> Naming
    #=========== 
    """ 
    Copy naming information from template objects to the joints closest to them
    copy over a cgmNameModifier tag from the module first
    """
    #attributes.copyUserAttrs(moduleNull,l_limbJoints[0],attrsToCopy=['cgmNameModifier'])
    mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Naming...'), progress=2)    				    
    
    #>>>First we need to find our matches
    log.debug("Finding matches from module controlObjects")
    for i_obj in self._ml_controlObjects:
        closestJoint = distance.returnClosestObject(i_obj.mNode,l_limbJoints)
        #transferObj = attributes.returnMessageObject(obj,'cgmName')
        """Then we copy it"""
        attributes.copyUserAttrs(i_obj.mNode,closestJoint,attrsToCopy=['cgmPosition','cgmNameModifier','cgmDirection','cgmName'])
	self._d_handleToHandleJoints[i_obj] = cgmMeta.cgmNode(closestJoint)
	i_obj.connectChildNode(closestJoint,'handleJoint')
	
    #>>>If we stole our parents anchor joint, we need to to reconnect it
    log.debug("STOLEN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> %s"%self.b_parentStole)
    if self.b_parentStole:
	i_parentControl = self._i_module.moduleParent.templateNull.msgList_get('controlObjects')[-1]
	log.debug("parentControl: %s"%i_parentControl.getShortName())
        closestJoint = distance.returnClosestObject(i_parentControl.mNode,l_limbJoints)	
	i_parentControl.connectChildNode(closestJoint,'handleJoint')
    
    #>>>Store it
    #self._i_rigNull.connectChildren(l_limbJoints,'moduleJoints','module')
    self._i_rigNull.msgList_connect(l_limbJoints,'moduleJoints','rigNull')
    #self._i_rigNull.msgList_connect(l_limbJoints,'baseJoints','module')
  

    #>>>Store these joints and rename the heirarchy
    log.debug("Metaclassing our objects") 
    for i,o in enumerate(l_limbJoints):
        i_o = cgmMeta.cgmObject(o)
        i_o.addAttr('mClass','cgmObject',lock=True) 
        i_o.addAttr('d_jointFlags', '{}',attrType = 'string', lock=True, hidden=True) 
	
    ml_moduleJoints = self._i_rigNull.msgList_get('moduleJoints',asMeta = True)    
    ml_moduleJoints[0].doName(nameChildren=True,fastIterate=False)#name
    l_moduleJoints = [i_j.p_nameShort for i_j in ml_moduleJoints]#store
    
    #>>> Orientation    
    #=============== 
    mc.progressBar(self.str_progressBar, edit=True, status = "%s >>Skeletonize>> step:'%s' "%(self._strShortName,'Orienting...'), progress=3)    				        
    try:
	if not doOrientSegment(self):
	    raise StandardError, "Orient failed"
    except StandardError,error:
        raise StandardError,"Segment orientation failed: %s"%error    
    
    #>>> Set its radius and toggle axis visbility on
    jointSize = (distance.returnDistanceBetweenObjects (l_moduleJoints[0],l_moduleJoints[-1])/6)
    reload(attributes)
    #jointSize*.2
    attributes.doMultiSetAttr(l_moduleJoints,'radi',3)
    
    #>>> Flag our handle joints
    #===========================
    ml_handles = []
    ml_handleJoints = []
    for i_obj in self._ml_controlObjects:
	if i_obj.hasAttr('handleJoint'):
	    #d_buffer = i_obj.handleJoint.d_jointFlags
	    #d_buffer['isHandle'] = True
	    #i_obj.handleJoint.d_jointFlags = d_buffer
	    ml_handleJoints.append(i_obj.handleJoint)
    
    self._i_rigNull.msgList_connect(ml_handleJoints,'handleJoints','rigNull')
	    
    return True 

#@r9General.Timer
def doOrientSegment(self):
    """ 
    Segement orienter. Must have a JointFactory Instance
    """ 
    # Get our base info
    #==================	        
    assert self.cls == 'JointFactory.go',"Not a JointFactory.go instance!"
    assert mc.objExists(self._i_module.mNode),"module no longer exists"
    
    ml_moduleJoints = self._i_rigNull.msgList_get('moduleJoints',asMeta = True)
    l_moduleJoints = [i_j.p_nameShort for i_j in ml_moduleJoints]    
    
    #self._i_rigNull = self._i_module.rigNull#refresh
    log.debug(">>> %s.doOrientSegment >> "%self._strShortName + "="*75)            
        
    #>>> orientation vectors
    #=======================    
    orientationVectors = search.returnAimUpOutVectorsFromOrientation(self.jointOrientation)
    wantedAimVector = orientationVectors[0]
    wantedUpVector = orientationVectors[1]  
    log.debug("wantedAimVector: %s"%wantedAimVector)
    log.debug("wantedUpVector: %s"%wantedUpVector)
    
    #>>> Put objects in order of closeness to root
    #l_limbJoints = distance.returnDistanceSortedList(l_limbJoints[0],l_limbJoints)
    
    #>>> Segment our joint list by cgmName, prolly a better way to optimize this
    l_cull = copy.copy(l_moduleJoints)
    if len(l_cull)==1:
        log.debug('Single joint orient mode')
        helper = self.i_templateNull.orientRootHelper.mNode
        if helper:
            log.debug("helper: %s"%helper)
            constBuffer = mc.orientConstraint( helper,l_cull[0],maintainOffset = False)
            mc.delete (constBuffer[0])  
	    #Push rotate to jointOrient
	    i_jnt = cgmMeta.cgmObject(l_cull[0])
	    ##i_jnt.jointOrient = i_jnt.rotate
	    ##i_jnt.rotate = [0,0,0]
	    
    else:#Normal mode
        log.debug('Normal orient mode')        
        self.l_jointSegmentIndexSets= []
        while l_cull:
            matchTerm = search.findRawTagInfo(l_cull[0],'cgmName')
            buffer = []
            objSet = search.returnMatchedTagsFromObjectList(l_cull,'cgmName',matchTerm)
            for o in objSet:
                buffer.append(l_moduleJoints.index(o))
            self.l_jointSegmentIndexSets.append(buffer)
            for obj in objSet:
                l_cull.remove(obj)
            
        #>>> un parenting the chain
        for i,i_jnt in enumerate(ml_moduleJoints):
	    if i != 0:
		i_jnt.parent = False
            i_jnt.displayLocalAxis = 1#tmp
	    #Reset the jointRotate before orientating
	    ##i_jnt.jointOrient = [0,0,0]	    
	    #Set rotateOrder
            try:
		#i_jnt.rotateOrder = 2
                i_jnt.rotateOrder = self.jointOrientation
	    except StandardError,error:
		log.error("doOrientSegment>>rotate order set fail: %s"%i_jnt.getShortName())
    
        #>>>per segment stuff
        assert len(self.l_jointSegmentIndexSets) == len(self._i_module.coreNames.value)#quick check to make sure we've got the stuff we need
        cnt = 0
	log.debug("Segment Index sets: %s"%self.l_jointSegmentIndexSets)
        for cnt,segment in enumerate(self.l_jointSegmentIndexSets):#for each segment
	    log.debug("On segment: %s"%segment)	    
	    lastCnt = len(self.l_jointSegmentIndexSets)-1
            segmentHelper = self._ml_controlObjects[cnt].getMessage('helper')[0]
            helperObjectCurvesShapes =  mc.listRelatives(segmentHelper,shapes=True)
            upLoc = locators.locMeCvFromCvIndex(helperObjectCurvesShapes[0],30)        
            if not mc.objExists(segmentHelper) and search.returnObjectType(segmentHelper) != 'nurbsCurve':
                raise StandardError,"doOrientSegment>>> No helper found"
	    
            if cnt != lastCnt:
		log.debug(cnt)
                #>>> Create our up object from from the helper object 
                #>>> make a pair list
                #pairList = lists.parseListToPairs(segment)
                """for pair in pairList:
                    constraintBuffer = mc.aimConstraint(ml_moduleJoints[pair[1]].mNode,ml_moduleJoints[pair[0]].mNode,maintainOffset = False, weight = 1, aimVector = wantedAimVector, upVector = wantedUpVector, worldUpVector = [0,1,0], worldUpObject = upLoc, worldUpType = 'object' )
                    mc.delete(constraintBuffer[0])"""
		for index in segment:
		    if index != 0:
			ml_moduleJoints[index].parent = ml_moduleJoints[index-1].mNode
		    ml_moduleJoints[index].rotate  = [0,0,0]			
		    ml_moduleJoints[index].jointOrient  = [0,0,0]	
		    
		    log.debug("%s aim to %s"%(ml_moduleJoints[index].mNode,ml_moduleJoints[index+1].mNode))
		    constraintBuffer = mc.aimConstraint(ml_moduleJoints[index+1].mNode,ml_moduleJoints[index].mNode,maintainOffset = False, weight = 1, aimVector = wantedAimVector, upVector = wantedUpVector, worldUpVector = [0,1,0], worldUpObject = upLoc, worldUpType = 'object' )
		    mc.delete(constraintBuffer[0])
		    
		    #Push rotate to jointOrient
		    #ml_moduleJoints[index].jointOrient = ml_moduleJoints[index].rotate
		    #ml_moduleJoints[index].rotate = [0,0,0]
		    
		mc.delete(upLoc)
                """for index in segment[-1:]:
		    log.debug("%s orient to %s"%(ml_moduleJoints[index].mNode,ml_moduleJoints[index-1].mNode))		    
                    constraintBuffer = mc.orientConstraint(ml_moduleJoints[index-1].mNode,ml_moduleJoints[index].mNode,maintainOffset = False, weight = 1)
                    mc.delete(constraintBuffer[0])"""
                #>>>  Increment and delete the up loc """
            else:
		log.debug(">>> Last count")
                #>>> Make an aim object and move it """
		i_jnt = ml_moduleJoints[segment[-1]]
		log.debug(i_jnt.getShortName())
		i_jnt.parent = ml_moduleJoints[segment[-1]-1].mNode
		i_jnt.jointOrient  = [0,0,0]
		#ml_moduleJoints[index].rotate  = [0,0,0]					

                aimLoc = locators.locMeObject(segmentHelper)
                aimLocGroup = rigging.groupMeObject(aimLoc)
                mc.move (0,0,10, aimLoc, localSpace=True)
                constraintBuffer = mc.aimConstraint(aimLoc,i_jnt.mNode,maintainOffset = False, weight = 1, aimVector = wantedAimVector, upVector = wantedUpVector, worldUpVector = [0,1,0], worldUpObject = upLoc, worldUpType = 'object' )
                mc.delete(constraintBuffer[0])
                mc.delete(aimLocGroup)
                mc.delete(upLoc)
		#>>>Push the first joints orient to 		
		#i_jnt.jointOrient = i_jnt.rotate
		#i_jnt.rotate = [0,0,0]	
        #>>>Reconnect the joints
        for cnt,i_jnt in enumerate(ml_moduleJoints[1:]):#parent each to the one before it
            i_jnt.parent = ml_moduleJoints[cnt].mNode
	    i_p = cgmMeta.cgmObject(i_jnt.parent)
	    #Verify inverse scale connection
	    cgmMeta.cgmAttr(i_jnt,"inverseScale").doConnectIn("%s.scale"%i_p.mNode)

    if self._i_module.moduleType in ['foot']:
        log.debug("Special case orient")
        if len(l_moduleJoints) > 1:
            helper = self.i_templateNull.orientRootHelper.mNode
            if helper:
                log.debug("Root joint fix...")                
                rootJoint = l_moduleJoints[0]
                ml_moduleJoints[1].parent = False #unparent the first child
                constBuffer = mc.orientConstraint( helper,rootJoint,maintainOffset = False)
                mc.delete (constBuffer[0])   
                ml_moduleJoints[1].parent = rootJoint
		ml_moduleJoints[1].jointOrient = ml_moduleJoints[1].rotate
		ml_moduleJoints[1].rotate = [0,0,0]        
    
    #Copy 
    #""" Freeze the rotations """
    jntUtils.metaFreezeJointOrientation(ml_moduleJoints)   
    
    #Connect to parent
    try:
	if self._i_module.getMessage('moduleParent'):#If we have a moduleParent, constrain it
	    connectToParentModule(self._i_module)    
    except:
	raise StandardError, "Failed to connect to module parent"
	
    try:
	for i,i_jnt in enumerate(ml_moduleJoints):
	    log.debug(i_jnt.getAttr('cgmName'))
	    if i_jnt.getAttr('cgmName') in ['ankle']:
		log.debug("Copy orient from parent mode: %s"%i_jnt.getShortName())
		joints.doCopyJointOrient(i_jnt.parent,i_jnt.mNode)
    except:
	raise StandardError, "Failed to Copy parent joint orient"    
    return True




#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Module tools
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
#@r9General.Timer
def deleteSkeleton(self,*args,**kws):  
    #MUST BE A MODULE
    if not self.isSkeletonized():
        log.warning("Not skeletonized. Cannot delete skeleton: '%s'"%self.getShortName())
        return False
    log.debug(">>> %s.deleteSkeleton >> "%self.p_nameShort + "="*75)            
    
    ml_skinJoints = self.rig_getSkinJoints(asMeta = True)
    l_skinJoints = [i_j.p_nameLong for i_j in ml_skinJoints if i_j ]  
    
    #We need to see if any of or moduleJoints have children
    l_strayChildren = []
    for i_jnt in ml_skinJoints:
        buffer = i_jnt.getChildren(True)
        for c in buffer:
            if c not in l_skinJoints:
                try:
                    i_c = cgmMeta.cgmObject(c)
                    i_c.parent = False
                    l_strayChildren.append(i_c.mNode)
                except StandardError,error:
                    log.warning(error)     
		    
    log.debug("l_strayChildren: %s"%l_strayChildren)    
    self.msgList_purge('skinJoints')
    self.msgList_purge('moduleJoints')
    self.msgList_purge('handleJoints')
    
    if l_skinJoints:
	mc.delete(l_skinJoints)
    else:return False
	

    
    return True

#@r9General.Timer
def connectToParentModule(self):
    """
    Pass a module class. Constrains template root to parent's closest template object
    """
    log.debug(">>> %s.connectToParentModule >> "%self.p_nameShort + "="*75)            
    if not self.isSkeletonized():
        log.error("Must be skeletonized to contrainToParentModule: '%s' "%self.getShortName())
        return False
    
    ml_moduleJoints = self.rigNull.msgList_get('moduleJoints',asMeta = True)
    l_moduleJoints = [i_o.p_nameShort for i_o in ml_moduleJoints]
    if not self.getMessage('moduleParent'):
        return False
    else:
        #>>> Get some info
        i_rigNull = self.rigNull #Link
        i_parent = self.moduleParent #Link
        parentState = i_parent.getState() 
        if i_parent.isSkeletonized():#>> If we have a module parent
            #>> If we have another anchor
            l_parentSkinJoints = i_parent.rigNull.msgList_getMessage('moduleJoints')
            closestObj = distance.returnClosestObject(l_moduleJoints[0],l_parentSkinJoints)
            ml_moduleJoints[0].parent = closestObj
            
        else:
            log.error("Parent has not been skeletonized...")           
            return False  
    return True


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Module tools
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  

def skeletonizeCharacter(masterNull):
    """ 
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DESCRIPTION:
    Skeletonizes a character
    
    ARGUMENTS:
    masterNull(string)
    
    RETURNS:
    nothin
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    modules = modules.returnModules(masterNull)
    orderedModules = modules.returnOrderedModules(modules)
    #>>> Do the spine first
    stateCheck = modules.moduleStateCheck(orderedModules[0],['template'])
    if stateCheck == 1:
        spineJoints = skeletonize(orderedModules[0])
    else:
        print ('%s%s' % (module,' has already been skeletonized. Moving on...'))
    
    #>>> Do the rest
    for module in orderedModules[1:]:
        stateCheck = modules.moduleStateCheck(module,['template'])
        if stateCheck == 1:
            templateNull = modules.returnTemplateNull(module)
            root =  modules.returnInfoNullObjects(module,'templatePosObjects',types='templateRoot')
            
            #>>> See if our item has a non default anchor
            anchored = storeTemplateRootParent(module) 
            if anchored == True:
                anchor =  attributes.returnMessageObject(root[0],'skeletonParent')
                closestJoint = distance.returnClosestObject(anchor,spineJoints)
            else:
                closestJoint = distance.returnClosestObject(root[0],spineJoints) 
        
            l_limbJoints = skeletonize(module)
            rootName = rigging.doParentReturnName(l_limbJoints[0],closestJoint)
            print rootName
        else:
            print ('%s%s' % (module,' has already been skeletonized. Moving on...'))

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def skeletonStoreCharacter(masterNull):
    """ 
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DESCRIPTION:
    stores a skeleton of a character
    
    ARGUMENTS:
    masterNull(string)
    
    RETURNS:
    nothin
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    modules = modules.returnModules(masterNull)
    orderedModules = modules.returnOrderedModules(modules)
    #>>> Do the spine first
    stateCheck = modules.moduleStateCheck(orderedModules[0],['template'])
    if stateCheck == 1:
        spineJoints = modules.saveTemplateToModule(orderedModules[0])
    else:
        print ('%s%s' % (module,' has already been skeletonized. Moving on...'))
    
    #>>> Do the rest
    for module in orderedModules[1:]:
        stateCheck = modules.moduleStateCheck(module,['template'])
        if stateCheck == 1:
            templateNull = modules.returnTemplateNull(module)        
            modules.saveTemplateToModule(module)
        else:
            print ('%s%s' % (module,' has already been skeletonized. Moving on...'))

       
         
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>            

def storeTemplateRootParent(moduleNull):
    """ 
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DESCRIPTION:
    Stores the template root parent to the root control if there is a new one
    
    ARGUMENTS:
    moduleNull(string)
    
    RETURNS:
    success(bool)
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    templateNull = modules.returnTemplateNull(moduleNull)
    root =   modules.returnInfoNullObjects(moduleNull,'templatePosObjects',types='templateRoot')
    parent = search.returnParentObject(root, False)
    if parent != templateNull:
        if parent != False:
            attributes.storeObjectToMessage(parent,root,'skeletonParent')
            return True
    return False



#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>    
#>>> Tools    
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
