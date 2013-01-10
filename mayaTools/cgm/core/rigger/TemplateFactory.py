import copy
import re

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
from Red9.core import Red9_General as r9General

# From cgm ==============================================================
from cgm.lib import (modules,curves,distance,attributes)
reload(attributes)
from cgm.lib.classes import NameFactory
from cgm.core.classes import DraggerContextFactory as dragFactory
reload(dragFactory)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
class go(object):
    @r9General.Timer
    def __init__(self,module): 
        #>>> Get our base info
        #>>> module null data 
        assert module.mClass in ['cgmModule','cgmLimb'],"Not a module"
        self.m = module# Link for shortness
        
        self.moduleNullData = attributes.returnUserAttrsToDict(self.m.mNode)
        self.templateNull = self.m.templateNull.mNode or False
        self.rigNull = self.m.rigNull.mNode or false
    
        #>>> part name 
        self.partName = NameFactory.returnUniqueGeneratedName(self.m.mNode, ignore = 'cgmType')
        self.partType = self.m.moduleType or False
        
        self.direction = False
        if self.m.hasAttr('cgmDirection'):
            direction = self.m.cgmDirection or False
        
        #>>> template null 
        self.templateNullData = attributes.returnUserAttrsToDict(self.templateNull)
        self.curveDegree = self.m.templateNull.curveDegree
        self.stiffIndex = self.m.templateNull.stiffIndex
        
        log.info("Module: %s"%self.m.getShortName())
        log.info("moduleNullData: %s"%self.moduleNullData)
        log.info("partType: %s"%self.partType)
        log.info("direction: %s"%self.direction) 
        
        if self.m.mClass == 'cgmLimb':
            log.info("mode: cgmLimb Template")
        else:
            raise NotImplementedError,"haven't implemented %s templatizing yet"%self.m.mClass
        
        
@r9General.Timer
def doTemplate(self):
    #Meat of the template process
    #==============	
    #>>> Get our base info
    """ module null data """
    moduleNullData = attributes.returnUserAttrsToDict(self.mNode)
    templateNull = self.templateNull.mNode or False
    rigNull = self.rigNull.mNode or false

    """ part name """
    partName = NameFactory.returnUniqueGeneratedName(self.mNode, ignore = 'cgmType')
    partType = self.moduleType or False
    
    direction = False
    if self.hasAttr('cgmDirection'):
        direction = self.cgmDirection or False
    
    """ template null """
    templateNullData = attributes.returnUserAttrsToDict(templateNull)
    curveDegree = self.templateNull.curveDegree
    stiffIndex = self.templateNull.stiffIndex
    
    log.info("Module: %s"%self.getShortName())
    log.info("moduleNullData: %s"%moduleNullData)
    log.info("partType: %s"%partType)
    log.info("direction: %s"%direction)
    
    
    """ template object nulls """
    #templatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleNull,'templatePosObjects')
    #templateControlObjectsNull = modules.returnInfoTypeNull(moduleNull,'templateControlObjects')
        
    
    """ Start objects stuff """
    #templateStarterDataInfoNull = modules.returnInfoTypeNull(moduleNull,'templateStarterData')
    #initialObjectsTemplateDataBuffer = attributes.returnUserAttrsToList(templateStarterDataInfoNull)
    #initialObjectsPosData = lists.removeMatchedIndexEntries(initialObjectsTemplateDataBuffer,'cgm')
    """
    corePositionList = []
    coreRotationList = []
    coreScaleList = []
    for set in initialObjectsPosData:
        if re.match('pos',set[0]):
            corePositionList.append(set[1])
        elif re.match('rot',set[0]):
            coreRotationList.append(set[1])
        elif re.match('scale',set[0]):
            coreScaleList.append(set[1])
    log.info(corePositionList)
    log.info( coreRotationList )
    log.info( coreScaleList )
    """
    #template control objects stuff
    #==============	    
    """
    templateControlObjectsDataNull = modules.returnInfoTypeNull(moduleNull,'templateControlObjectsData')
    templateControlObjectsDataNullBuffer = attributes.returnUserAttrsToList(templateControlObjectsDataNull)
    templateControlObjectsData = lists.removeMatchedIndexEntries(templateControlObjectsDataNullBuffer,'cgm')
    controlPositionList = []
    controlRotationList = []
    controlScaleList = []
    print templateControlObjectsData
    for set in templateControlObjectsData:
        if re.match('pos',set[0]):
            controlPositionList.append(set[1])
        elif re.match('rot',set[0]):
            controlRotationList.append(set[1])
        elif re.match('scale',set[0]):
            controlScaleList.append(set[1])
    print controlPositionList
    print controlRotationList
    print controlScaleList
    """
    # Names Info
    #==============	       
    """
    coreNamesInfoNull = modules.returnInfoTypeNull(moduleNull,'coreNames')
    coreNamesBuffer = attributes.returnUserAttrsToList(coreNamesInfoNull)
    coreNames = lists.removeMatchedIndexEntries(coreNamesBuffer,'cgm')
    coreNamesAttrs = []
    for set in coreNames:
        coreNamesAttrs.append(coreNamesInfoNull+'.'+set[0])
    divider = NameFactory.returnCGMDivider()
    
    print ('%s%s'% (moduleNull,' data aquired...'))
    """
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> make template objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    return
    """makes template objects"""
    templateObjects = makeLimbTemplate(moduleNull)
    print 'Template Limb made....'
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Parent objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    for obj in templateObjects[0]:    
        obj =  rigging.doParentReturnName(obj,templateNull) 

    print 'Template objects parented'
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Transform groups and Handles...handling
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    root = modules.returnInfoNullObjects(moduleNull,'templatePosObjects',types='templateRoot')
    
    handles = templateObjects[1]
    #>>> Break up the handles into the sets we need 
    if stiffIndex == 0:
        splitHandles = False
        handlesToSplit = handles
        handlesRemaining = [handles[0],handles[-1]]
    elif stiffIndex < 0:
        splitHandles = True
        handlesToSplit = handles[:stiffIndex]
        handlesRemaining = handles[stiffIndex:]
        handlesRemaining.append(handles[0])
    elif stiffIndex > 0:
        splitHandles = True
        handlesToSplit = handles[stiffIndex:]
        handlesRemaining = handles[:stiffIndex]
        handlesRemaining.append(handles[-1])
    
    """ makes our mid transform groups"""
    if len(handlesToSplit)>2:
        constraintGroups = constraints.doLimbSegmentListParentConstraint(handlesToSplit)
        print 'Constraint groups created...'
        
        for group in constraintGroups:
            mc.parent(group,root[0])
        
    """ zero out the first and last"""
    for handle in [handles[0],handles[-1]]:
        groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
        mc.parent(groupBuffer,root[0])
        
    #>>> Break up the handles into the sets we need 
    if stiffIndex < 0:
        for handle in handles[(stiffIndex+-1):-1]:
            groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
            mc.parent(groupBuffer,handles[-1])
    elif stiffIndex > 0:
        for handle in handles[1:(stiffIndex+1)]:
            groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
            mc.parent(groupBuffer,handles[0])
            
    print 'Constraint groups parented...'
    
    rootName = NameFactory.doNameObject(root[0])
    
    for obj in handles:
        attributes.doSetLockHideKeyableAttr(obj,True,False,False,['sx','sy','sz','v'])
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Parenting constrainging parts
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
    if moduleParent != masterNull:
        if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
            moduleParent = attributes.returnMessageObject(moduleParent,'moduleParent')
        parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
        parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
        parentTemplateObjects = []
        for key in parentTemplatePosObjectsInfoData.keys():
            if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                    parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
        closestParentObject = distance.returnClosestObject(rootName,parentTemplateObjects)
        if (search.returnTagInfo(moduleNull,'cgmModuleType')) != 'foot':
            constraintGroup = rigging.groupMeObject(rootName,maintainParent=True)
            constraintGroup = NameFactory.doNameObject(constraintGroup)
            mc.pointConstraint(closestParentObject,constraintGroup, maintainOffset=True)
            mc.scaleConstraint(closestParentObject,constraintGroup, maintainOffset=True)
        else:
            constraintGroup = rigging.groupMeObject(closestParentObject,maintainParent=True)
            constraintGroup = NameFactory.doNameObject(constraintGroup)
            mc.parentConstraint(rootName,constraintGroup, maintainOffset=True)
            
    """ grab the last clavicle piece if the arm has one and connect it to the arm  """
    moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
    if moduleParent != masterNull:
        if (search.returnTagInfo(moduleNull,'cgmModuleType')) == 'arm':
            if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
                print '>>>>>>>>>>>>>>>>>>>>> YOU FOUND ME'
                parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
                parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
                parentTemplateObjects = []
                for key in parentTemplatePosObjectsInfoData.keys():
                    if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                        if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                            parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
                closestParentObject = distance.returnClosestObject(rootName,parentTemplateObjects)
                endConstraintGroup = rigging.groupMeObject(closestParentObject,maintainParent=True)
                endConstraintGroup = NameFactory.doNameObject(endConstraintGroup)
                mc.pointConstraint(handles[0],endConstraintGroup, maintainOffset=True)
                mc.scaleConstraint(handles[0],endConstraintGroup, maintainOffset=True)
        
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Final stuff
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    
    
    #>>> Set our new module rig process state
    mc.setAttr ((moduleNull+'.templateState'), 1)
    mc.setAttr ((moduleNull+'.skeletonState'), 0)
    print ('%s%s'% (moduleNull,' done'))
    
    #>>> Tag our objects for easy deletion
    children = mc.listRelatives (templateNull, allDescendents = True,type='transform')
    for obj in children:
        attributes.storeInfo(obj,'cgmOwnedBy',templateNull)
        
    #>>> Visibility Connection
    masterControl = attributes.returnMessageObject(masterNull,'controlMaster')
    visControl = attributes.returnMessageObject(masterControl,'childControlVisibility')
    attributes.doConnectAttr((visControl+'.orientHelpers'),(templateNull+'.visOrientHelpers'))
    attributes.doConnectAttr((visControl+'.controlHelpers'),(templateNull+'.visControlHelpers'))
    #>>> Run a rename on the module to make sure everything is named properly
    #NameFactory.doRenameHeir(moduleNull)
    


def makeLimbTemplate (moduleNull):  
    #>>>Curve degree finder
    if curveDegree == 0:
        doCurveDegree = 1
    else:
        if len(corePositionList) <= 3:
            doCurveDegree = 1
        else:
            doCurveDegree = len(corePositionList) - 1
    
    returnList = []
    templObjNameList = []
    templHandleList = []
    
    moduleColors = modules.returnModuleColors(moduleNull)
    
    #>>>Scale stuff
    moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
    if moduleParent == masterNull:
        length = (distance.returnDistanceBetweenPoints (corePositionList[0],corePositionList[-1]))
        size = length / len(coreNamesAttrs)
    else:
        parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
        parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
        parentTemplateObjects = []
        for key in parentTemplatePosObjectsInfoData.keys():
            if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                    parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
        createBuffer = curves.createControlCurve('sphere',1)
        pos = corePositionList[0]
        mc.move (pos[0], pos[1], pos[2], createBuffer, a=True)
        closestParentObject = distance.returnClosestObject(createBuffer,parentTemplateObjects)
        boundingBoxSize = distance.returnBoundingBoxSize (closestParentObject)
        maxSize = max(boundingBoxSize)
        size = maxSize *.25
        mc.delete(createBuffer)
        if partType == 'clavicle':
            size = size * .5
        elif partType == 'head':
            size = size * .75
        if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
            size = size * 2
        
    cnt = 0
    lastCountSizeMatch = len(corePositionList) -1
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Making the template objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    for pos in corePositionList:
        if cnt == 0:
            sizeMultiplier = 1
        elif cnt == lastCountSizeMatch:
            sizeMultiplier = .8
        else:
            sizeMultiplier = .5
        """make a sphere and move it"""
        createBuffer = curves.createControlCurve('sphere',(size * sizeMultiplier))
        curves.setCurveColorByName(createBuffer,moduleColors[0])
        attributes.storeInfo(createBuffer,'cgmName',coreNamesAttrs[cnt])
        if direction != None:
            attributes.storeInfo(createBuffer,'cgmDirection',direction)
        attributes.storeInfo(createBuffer,'cgmType','templateObject')
        tmpObjName = NameFactory.doNameObject(createBuffer)
        mc.move (pos[0], pos[1], pos[2], [tmpObjName], a=True)
                    
        """adds it to the list"""
        templObjNameList.append (tmpObjName)
        templHandleList.append (tmpObjName)  
        """ replaces the message node locator objects with the new template ones """  
        attributes.storeObjectToMessage (tmpObjName, templatePosObjectsInfoNull, NameFactory.returnUniqueGeneratedName(tmpObjName,ignore='cgmType'))  
        
        cnt +=1

    """Makes our curve"""    
    crvName = mc.curve (d=doCurveDegree, p = corePositionList , os=True, n=('%s%s%s' %(partName,'_',(typesDictionary.get('templateCurve')))))            
    if direction != None:
            attributes.storeInfo(crvName,'cgmDirection',direction)
    attributes.storeInfo(crvName,'cgmType','templateCurve')
    curves.setCurveColorByName(crvName,moduleColors[1])
    curveLocs = []
    
    cnt = 0
    for obj in templObjNameList:
        pointLoc = locators.locMeObject (obj)
        attributes.storeInfo(pointLoc,'cgmName',templObjNameList[cnt])
        if direction != None:
            attributes.storeInfo(pointLoc,'cgmDirection',direction)
        mc.setAttr ((pointLoc+'.visibility'),0)
        mc.parentConstraint ([obj],[pointLoc],mo=False)
        mc.connectAttr ( (pointLoc+'.translate') , ('%s%s%i%s' % (crvName, '.controlPoints[', cnt, ']')), f=True )
        curveLocs.append (pointLoc)
        cnt+=1
    
    #>>> Direction and size Stuff
    
    """ Directional data derived from joints """
    generalDirection = locators.returnHorizontalOrVertical(templObjNameList)
    if generalDirection == 'vertical' and 'leg' not in partType:
        worldUpVector = [0,0,-1]
    elif generalDirection == 'vertical' and 'leg' in partType:
        worldUpVector = [0,0,1]
    else:
        worldUpVector = [0,1,0]
    
    """ Create root control"""
    moduleNullData = attributes.returnUserAttrsToDict(moduleNull)
    templateNull = moduleNullData.get('templateNull')
    
    rootSize = (distance.returnBoundingBoxSizeToAverage(templObjNameList[0])*1.5)
    createBuffer = curves.createControlCurve('cube',rootSize)
    curves.setCurveColorByName(createBuffer,moduleColors[0])
    
    if partType == 'clavicle' or partType == 'clavicle':
        position.movePointSnap(createBuffer,templObjNameList[0])
    else:
        position.movePointSnap(createBuffer,templObjNameList[0])
    constBuffer = mc.aimConstraint(templObjNameList[-1],createBuffer,maintainOffset = False, weight = 1, aimVector = [1,0,0], upVector = [0,1,0], worldUpVector = worldUpVector, worldUpType = 'vector' )
    mc.delete (constBuffer[0])
    attributes.storeInfo(createBuffer,'cgmType','templateRoot')
    if direction != None:
        attributes.storeInfo(createBuffer,'cgmDirection',direction)
    rootCtrl = NameFactory.doNameObject(createBuffer)
    
    rootGroup = rigging.groupMeObject(rootCtrl)
    rootGroup = rigging.doParentReturnName(rootGroup,templateNull)
    
    templObjNameList.append (crvName)
    templObjNameList += curveLocs
    
    """ replaces the message node locator objects with the new template ones """                          
    attributes.storeObjectToMessage (crvName, templatePosObjectsInfoNull, 'curve')
    attributes.storeObjectToMessage (rootCtrl, templatePosObjectsInfoNull, 'root')  
    
    """Get our modules group, parents our part null there and connects it to the info null"""
    modulesGroup = attributes.returnMessageObject(masterNull,'modulesGroup')
    modulesInfoNull = modules.returnInfoTypeNull(masterNull,'modules')
    
    attributes.storeObjectToMessage (moduleNull, modulesInfoNull, (NameFactory.returnUniqueGeneratedName(moduleNull,ignore='cgmType')))
    
    """ parenting of the modules group if necessary"""
    moduleNullBuffer = rigging.doParentReturnName(moduleNull,modulesGroup)
    if moduleNullBuffer == False:
        moduleNull = moduleNull
    else:
        moduleNull = moduleNullBuffer

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Orientation helpers
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    """ Make our Orientation Helpers """
    orientHelpersReturn = addOrientationHelpers(templHandleList,rootCtrl,moduleNull,partType,(templateNull+'.visOrientHelpers'))
    masterOrient = orientHelpersReturn[0]
    orientObjects = orientHelpersReturn[1]
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Control helpers
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    print orientObjects
    print moduleNull
    print (templateNull+'.visControlHelpers')
    controlHelpersReturn = addControlHelpers(orientObjects,moduleNull,(templateNull+'.visControlHelpers'))

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Input the saved values if there are any
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    """ Orientation Helpers """
    rotBuffer = coreRotationList[-1]
    #actualName = mc.spaceLocator (n= wantedName)
    rotCheck = sum(rotBuffer)
    if rotCheck != 0:
        mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],masterOrient,os=True)
    
    cnt = 0
    for obj in orientObjects:
        rotBuffer = coreRotationList[cnt]
        rotCheck = sum(rotBuffer)
        if rotCheck != 0:
            mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],obj,os=True)
        cnt +=1 
            
    """ Control Helpers """
    controlHelpers = controlHelpersReturn[0]
    cnt = 0
    for obj in controlHelpers:
        posBuffer = controlPositionList[cnt]
        posCheck = sum(posBuffer)
        if posCheck != 0:
            mc.xform(obj,t=[posBuffer[0],posBuffer[1],posBuffer[2]],ws=True)
        
        rotBuffer = controlRotationList[cnt]
        rotCheck = sum(rotBuffer)
        if rotCheck != 0:
            mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],obj,ws=True)
        
        scaleBuffer = controlScaleList[cnt]
        scaleCheck = sum(scaleBuffer)
        if scaleCheck != 0:
            mc.scale(scaleBuffer[0],scaleBuffer[1],scaleBuffer[2],obj,absolute=True)
        cnt +=1 
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Final stuff
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    returnList.append(templObjNameList)
    returnList.append(templHandleList)
    returnList.append(rootCtrl)
    return returnList

def doTemplate2(masterNull, moduleNull):
    def makeLimbTemplate (moduleNull):  
        #>>>Curve degree finder
        if curveDegree == 0:
            doCurveDegree = 1
        else:
            if len(corePositionList) <= 3:
                doCurveDegree = 1
            else:
                doCurveDegree = len(corePositionList) - 1
        
        returnList = []
        templObjNameList = []
        templHandleList = []
        
        moduleColors = modules.returnModuleColors(moduleNull)
        
        #>>>Scale stuff
        moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
        if moduleParent == masterNull:
            length = (distance.returnDistanceBetweenPoints (corePositionList[0],corePositionList[-1]))
            size = length / len(coreNamesAttrs)
        else:
            parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
            parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
            parentTemplateObjects = []
            for key in parentTemplatePosObjectsInfoData.keys():
                if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                    if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                        parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
            createBuffer = curves.createControlCurve('sphere',1)
            pos = corePositionList[0]
            mc.move (pos[0], pos[1], pos[2], createBuffer, a=True)
            closestParentObject = distance.returnClosestObject(createBuffer,parentTemplateObjects)
            boundingBoxSize = distance.returnBoundingBoxSize (closestParentObject)
            maxSize = max(boundingBoxSize)
            size = maxSize *.25
            mc.delete(createBuffer)
            if partType == 'clavicle':
                size = size * .5
            elif partType == 'head':
                size = size * .75
            if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
                size = size * 2
            
        cnt = 0
        lastCountSizeMatch = len(corePositionList) -1
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Making the template objects
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        for pos in corePositionList:
            if cnt == 0:
                sizeMultiplier = 1
            elif cnt == lastCountSizeMatch:
                sizeMultiplier = .8
            else:
                sizeMultiplier = .5
            """make a sphere and move it"""
            createBuffer = curves.createControlCurve('sphere',(size * sizeMultiplier))
            curves.setCurveColorByName(createBuffer,moduleColors[0])
            attributes.storeInfo(createBuffer,'cgmName',coreNamesAttrs[cnt])
            if direction != None:
                attributes.storeInfo(createBuffer,'cgmDirection',direction)
            attributes.storeInfo(createBuffer,'cgmType','templateObject')
            tmpObjName = NameFactory.doNameObject(createBuffer)
            mc.move (pos[0], pos[1], pos[2], [tmpObjName], a=True)
                        
            """adds it to the list"""
            templObjNameList.append (tmpObjName)
            templHandleList.append (tmpObjName)  
            """ replaces the message node locator objects with the new template ones """  
            attributes.storeObjectToMessage (tmpObjName, templatePosObjectsInfoNull, NameFactory.returnUniqueGeneratedName(tmpObjName,ignore='cgmType'))  
            
            cnt +=1

        """Makes our curve"""    
        crvName = mc.curve (d=doCurveDegree, p = corePositionList , os=True, n=('%s%s%s' %(partName,'_',(typesDictionary.get('templateCurve')))))            
        if direction != None:
                attributes.storeInfo(crvName,'cgmDirection',direction)
        attributes.storeInfo(crvName,'cgmType','templateCurve')
        curves.setCurveColorByName(crvName,moduleColors[1])
        curveLocs = []
        
        cnt = 0
        for obj in templObjNameList:
            pointLoc = locators.locMeObject (obj)
            attributes.storeInfo(pointLoc,'cgmName',templObjNameList[cnt])
            if direction != None:
                attributes.storeInfo(pointLoc,'cgmDirection',direction)
            mc.setAttr ((pointLoc+'.visibility'),0)
            mc.parentConstraint ([obj],[pointLoc],mo=False)
            mc.connectAttr ( (pointLoc+'.translate') , ('%s%s%i%s' % (crvName, '.controlPoints[', cnt, ']')), f=True )
            curveLocs.append (pointLoc)
            cnt+=1
        
        #>>> Direction and size Stuff
        
        """ Directional data derived from joints """
        generalDirection = locators.returnHorizontalOrVertical(templObjNameList)
        if generalDirection == 'vertical' and 'leg' not in partType:
            worldUpVector = [0,0,-1]
        elif generalDirection == 'vertical' and 'leg' in partType:
            worldUpVector = [0,0,1]
        else:
            worldUpVector = [0,1,0]
        
        """ Create root control"""
        moduleNullData = attributes.returnUserAttrsToDict(moduleNull)
        templateNull = moduleNullData.get('templateNull')
        
        rootSize = (distance.returnBoundingBoxSizeToAverage(templObjNameList[0])*1.5)
        createBuffer = curves.createControlCurve('cube',rootSize)
        curves.setCurveColorByName(createBuffer,moduleColors[0])
        
        if partType == 'clavicle' or partType == 'clavicle':
            position.movePointSnap(createBuffer,templObjNameList[0])
        else:
            position.movePointSnap(createBuffer,templObjNameList[0])
        constBuffer = mc.aimConstraint(templObjNameList[-1],createBuffer,maintainOffset = False, weight = 1, aimVector = [1,0,0], upVector = [0,1,0], worldUpVector = worldUpVector, worldUpType = 'vector' )
        mc.delete (constBuffer[0])
        attributes.storeInfo(createBuffer,'cgmType','templateRoot')
        if direction != None:
            attributes.storeInfo(createBuffer,'cgmDirection',direction)
        rootCtrl = NameFactory.doNameObject(createBuffer)
        
        rootGroup = rigging.groupMeObject(rootCtrl)
        rootGroup = rigging.doParentReturnName(rootGroup,templateNull)
        
        templObjNameList.append (crvName)
        templObjNameList += curveLocs
        
        """ replaces the message node locator objects with the new template ones """                          
        attributes.storeObjectToMessage (crvName, templatePosObjectsInfoNull, 'curve')
        attributes.storeObjectToMessage (rootCtrl, templatePosObjectsInfoNull, 'root')  
        
        """Get our modules group, parents our part null there and connects it to the info null"""
        modulesGroup = attributes.returnMessageObject(masterNull,'modulesGroup')
        modulesInfoNull = modules.returnInfoTypeNull(masterNull,'modules')
        
        attributes.storeObjectToMessage (moduleNull, modulesInfoNull, (NameFactory.returnUniqueGeneratedName(moduleNull,ignore='cgmType')))
        
        """ parenting of the modules group if necessary"""
        moduleNullBuffer = rigging.doParentReturnName(moduleNull,modulesGroup)
        if moduleNullBuffer == False:
            moduleNull = moduleNull
        else:
            moduleNull = moduleNullBuffer

        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        #>> Orientation helpers
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        """ Make our Orientation Helpers """
        orientHelpersReturn = addOrientationHelpers(templHandleList,rootCtrl,moduleNull,partType,(templateNull+'.visOrientHelpers'))
        masterOrient = orientHelpersReturn[0]
        orientObjects = orientHelpersReturn[1]
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        #>> Control helpers
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        print orientObjects
        print moduleNull
        print (templateNull+'.visControlHelpers')
        controlHelpersReturn = addControlHelpers(orientObjects,moduleNull,(templateNull+'.visControlHelpers'))

        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        #>> Input the saved values if there are any
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        """ Orientation Helpers """
        rotBuffer = coreRotationList[-1]
        #actualName = mc.spaceLocator (n= wantedName)
        rotCheck = sum(rotBuffer)
        if rotCheck != 0:
            mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],masterOrient,os=True)
        
        cnt = 0
        for obj in orientObjects:
            rotBuffer = coreRotationList[cnt]
            rotCheck = sum(rotBuffer)
            if rotCheck != 0:
                mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],obj,os=True)
            cnt +=1 
                
        """ Control Helpers """
        controlHelpers = controlHelpersReturn[0]
        cnt = 0
        for obj in controlHelpers:
            posBuffer = controlPositionList[cnt]
            posCheck = sum(posBuffer)
            if posCheck != 0:
                mc.xform(obj,t=[posBuffer[0],posBuffer[1],posBuffer[2]],ws=True)
            
            rotBuffer = controlRotationList[cnt]
            rotCheck = sum(rotBuffer)
            if rotCheck != 0:
                mc.rotate(rotBuffer[0],rotBuffer[1],rotBuffer[2],obj,ws=True)
            
            scaleBuffer = controlScaleList[cnt]
            scaleCheck = sum(scaleBuffer)
            if scaleCheck != 0:
                mc.scale(scaleBuffer[0],scaleBuffer[1],scaleBuffer[2],obj,absolute=True)
            cnt +=1 
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        #>> Final stuff
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        returnList.append(templObjNameList)
        returnList.append(templHandleList)
        returnList.append(rootCtrl)
        return returnList	
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # The actual meat of the limb template process
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>>> get colors

    #>>> Get our base info
    """ module null data """
    moduleNullData = attributes.returnUserAttrsToDict(moduleNull)

    """ part name """
    partName = NameFactory.returnUniqueGeneratedName(moduleNull, ignore = 'cgmType')
    partType = moduleNullData.get('cgmModuleType')
    direction = moduleNullData.get('cgmDirection')
    
    
    """ template null """
    templateNull = moduleNullData.get('templateNull')
    templateNullData = attributes.returnUserAttrsToDict(templateNull)
    curveDegree = templateNullData.get('curveDegree')
    stiffIndex = templateNullData.get('stiffIndex')
    
    """ template object nulls """
    templatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleNull,'templatePosObjects')
    templateControlObjectsNull = modules.returnInfoTypeNull(moduleNull,'templateControlObjects')
    
    """ rig null """
    rigNull = moduleNullData.get('rigNull')
    
    
    """ Start objects stuff """
    templateStarterDataInfoNull = modules.returnInfoTypeNull(moduleNull,'templateStarterData')
    initialObjectsTemplateDataBuffer = attributes.returnUserAttrsToList(templateStarterDataInfoNull)
    initialObjectsPosData = lists.removeMatchedIndexEntries(initialObjectsTemplateDataBuffer,'cgm')
    corePositionList = []
    coreRotationList = []
    coreScaleList = []
    for set in initialObjectsPosData:
        if re.match('pos',set[0]):
            corePositionList.append(set[1])
        elif re.match('rot',set[0]):
            coreRotationList.append(set[1])
        elif re.match('scale',set[0]):
            coreScaleList.append(set[1])
    print corePositionList
    print coreRotationList
    print coreScaleList
    
    """ template control objects stuff """
    templateControlObjectsDataNull = modules.returnInfoTypeNull(moduleNull,'templateControlObjectsData')
    templateControlObjectsDataNullBuffer = attributes.returnUserAttrsToList(templateControlObjectsDataNull)
    templateControlObjectsData = lists.removeMatchedIndexEntries(templateControlObjectsDataNullBuffer,'cgm')
    controlPositionList = []
    controlRotationList = []
    controlScaleList = []
    print templateControlObjectsData
    for set in templateControlObjectsData:
        if re.match('pos',set[0]):
            controlPositionList.append(set[1])
        elif re.match('rot',set[0]):
            controlRotationList.append(set[1])
        elif re.match('scale',set[0]):
            controlScaleList.append(set[1])
    print controlPositionList
    print controlRotationList
    print controlScaleList

    
    """ Names Info """
    coreNamesInfoNull = modules.returnInfoTypeNull(moduleNull,'coreNames')
    coreNamesBuffer = attributes.returnUserAttrsToList(coreNamesInfoNull)
    coreNames = lists.removeMatchedIndexEntries(coreNamesBuffer,'cgm')
    coreNamesAttrs = []
    for set in coreNames:
        coreNamesAttrs.append(coreNamesInfoNull+'.'+set[0])
        
    
    divider = NameFactory.returnCGMDivider()
    
    print ('%s%s'% (moduleNull,' data aquired...'))
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> make template objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    """makes template objects"""
    templateObjects = makeLimbTemplate(moduleNull)
    print 'Template Limb made....'
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Parent objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    for obj in templateObjects[0]:    
        obj =  rigging.doParentReturnName(obj,templateNull) 

    print 'Template objects parented'
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Transform groups and Handles...handling
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    root = modules.returnInfoNullObjects(moduleNull,'templatePosObjects',types='templateRoot')
    
    handles = templateObjects[1]
    #>>> Break up the handles into the sets we need 
    if stiffIndex == 0:
        splitHandles = False
        handlesToSplit = handles
        handlesRemaining = [handles[0],handles[-1]]
    elif stiffIndex < 0:
        splitHandles = True
        handlesToSplit = handles[:stiffIndex]
        handlesRemaining = handles[stiffIndex:]
        handlesRemaining.append(handles[0])
    elif stiffIndex > 0:
        splitHandles = True
        handlesToSplit = handles[stiffIndex:]
        handlesRemaining = handles[:stiffIndex]
        handlesRemaining.append(handles[-1])
    
    """ makes our mid transform groups"""
    if len(handlesToSplit)>2:
        constraintGroups = constraints.doLimbSegmentListParentConstraint(handlesToSplit)
        print 'Constraint groups created...'
        
        for group in constraintGroups:
            mc.parent(group,root[0])
        
    """ zero out the first and last"""
    for handle in [handles[0],handles[-1]]:
        groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
        mc.parent(groupBuffer,root[0])
        
    #>>> Break up the handles into the sets we need 
    if stiffIndex < 0:
        for handle in handles[(stiffIndex+-1):-1]:
            groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
            mc.parent(groupBuffer,handles[-1])
    elif stiffIndex > 0:
        for handle in handles[1:(stiffIndex+1)]:
            groupBuffer = (rigging.groupMeObject(handle,maintainParent=True))
            mc.parent(groupBuffer,handles[0])
            
    print 'Constraint groups parented...'
    
    rootName = NameFactory.doNameObject(root[0])
    
    for obj in handles:
        attributes.doSetLockHideKeyableAttr(obj,True,False,False,['sx','sy','sz','v'])
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Parenting constrainging parts
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
    if moduleParent != masterNull:
        if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
            moduleParent = attributes.returnMessageObject(moduleParent,'moduleParent')
        parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
        parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
        parentTemplateObjects = []
        for key in parentTemplatePosObjectsInfoData.keys():
            if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                    parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
        closestParentObject = distance.returnClosestObject(rootName,parentTemplateObjects)
        if (search.returnTagInfo(moduleNull,'cgmModuleType')) != 'foot':
            constraintGroup = rigging.groupMeObject(rootName,maintainParent=True)
            constraintGroup = NameFactory.doNameObject(constraintGroup)
            mc.pointConstraint(closestParentObject,constraintGroup, maintainOffset=True)
            mc.scaleConstraint(closestParentObject,constraintGroup, maintainOffset=True)
        else:
            constraintGroup = rigging.groupMeObject(closestParentObject,maintainParent=True)
            constraintGroup = NameFactory.doNameObject(constraintGroup)
            mc.parentConstraint(rootName,constraintGroup, maintainOffset=True)
            
    """ grab the last clavicle piece if the arm has one and connect it to the arm  """
    moduleParent = attributes.returnMessageObject(moduleNull,'moduleParent')
    if moduleParent != masterNull:
        if (search.returnTagInfo(moduleNull,'cgmModuleType')) == 'arm':
            if (search.returnTagInfo(moduleParent,'cgmModuleType')) == 'clavicle':
                print '>>>>>>>>>>>>>>>>>>>>> YOU FOUND ME'
                parentTemplatePosObjectsInfoNull = modules.returnInfoTypeNull(moduleParent,'templatePosObjects')
                parentTemplatePosObjectsInfoData = attributes.returnUserAttrsToDict (parentTemplatePosObjectsInfoNull)
                parentTemplateObjects = []
                for key in parentTemplatePosObjectsInfoData.keys():
                    if (mc.attributeQuery (key,node=parentTemplatePosObjectsInfoNull,msg=True)) == True:
                        if search.returnTagInfo((parentTemplatePosObjectsInfoData[key]),'cgmType') != 'templateCurve':
                            parentTemplateObjects.append (parentTemplatePosObjectsInfoData[key])
                closestParentObject = distance.returnClosestObject(rootName,parentTemplateObjects)
                endConstraintGroup = rigging.groupMeObject(closestParentObject,maintainParent=True)
                endConstraintGroup = NameFactory.doNameObject(endConstraintGroup)
                mc.pointConstraint(handles[0],endConstraintGroup, maintainOffset=True)
                mc.scaleConstraint(handles[0],endConstraintGroup, maintainOffset=True)
        
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #>> Final stuff
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    
    
    #>>> Set our new module rig process state
    mc.setAttr ((moduleNull+'.templateState'), 1)
    mc.setAttr ((moduleNull+'.skeletonState'), 0)
    print ('%s%s'% (moduleNull,' done'))
    
    #>>> Tag our objects for easy deletion
    children = mc.listRelatives (templateNull, allDescendents = True,type='transform')
    for obj in children:
        attributes.storeInfo(obj,'cgmOwnedBy',templateNull)
        
    #>>> Visibility Connection
    masterControl = attributes.returnMessageObject(masterNull,'controlMaster')
    visControl = attributes.returnMessageObject(masterControl,'childControlVisibility')
    attributes.doConnectAttr((visControl+'.orientHelpers'),(templateNull+'.visOrientHelpers'))
    attributes.doConnectAttr((visControl+'.controlHelpers'),(templateNull+'.visControlHelpers'))
    #>>> Run a rename on the module to make sure everything is named properly
    #NameFactory.doRenameHeir(moduleNull)




