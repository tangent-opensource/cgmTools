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

##>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
@r9General.Timer   
def isSized(self):
    """
    Return if a moudle is sized or not
    """
    handles = self.rigNull.handles
    if self.templateNull.templateStarterData:
        if len(self.templateNull.templateStarterData) == handles:
            for i in range(handles):
                if not self.templateNull.templateStarterData[i][1]:
                    log.warning("%s has no data"%(self.templateNull.templateStarterData[i]))                    
                    return False
            return True
        else:
            log.warning("%i is not == %i handles necessary"%(len(self.templateNull.templateStarterData),handles))
            return False
    else:
        log.warning("No template starter data found for '%s'"%self.getShortName())        
    return False
    
    
    
def doSize(self,sizeMode='normal',geo = []):
    """
    Size a module
    1) Determine what points we need to gather
    2) Initiate draggerContextFactory
    3) Prompt user per point
    4) at the end of the day have a pos list the length of the handle list
    
    @ sizeMode
    'all' - pick every handle position
    'normal' - first/last, if child, will use last position of parent as first
    
    TODO:
    Add option for other modes
    Add geo argument that can be passed for speed
    Add clamp on value
    """
    clickMode = {"heel":"surface"}    
    
    #Gather info
    #==============      
    handles = self.rigNull.handles
    names = getGeneratedCoreNames(self)
    if not geo:
        geo = self.modulePuppet.getGeo()
    log.debug("Handles: %s"%handles)
    log.debug("Names: %s"%names)
    log.debug("Puppet: %s"%self.getMessage('modulePuppet'))
    log.debug("Geo: %s"%geo)
    i_module = self #Bridge holder for our module class to go into our sizer class
    
    #Variables
    #==============      
    if sizeMode == 'normal':
        if names > 1:
            namesToCreate = names[0],names[-1]
        else:
            namesToCreate = names
        log.info("Names: %s"%names)
    else:
        namesToCreate = names        
        sizeMode = 'all'
       
    class moduleSizer(dragFactory.clickMesh):
        """Sublass to get the functs we need in there"""
        def __init__(self,i_module = i_module,**kws):
            super(moduleSizer, self).__init__(**kws)
            self.i_module = i_module
            log.info("Please place '%s'"%self.toCreate[0])
            
        def release(self):
            if len(self.returnList)< len(self.toCreate)-1:#If we have a prompt left
                log.info("Please place '%s'"%self.toCreate[len(self.returnList)+1])            
            dragFactory.clickMesh.release(self)

            
        def finalize(self):
            log.debug("returnList: %s"% self.returnList)
            log.debug("createdList: %s"% self.createdList)   
            buffer = self.i_module.templateNull.templateStarterData
            log.debug("starting data: %s"% buffer)
            
            #Make sure we have enough points
            #==============  
            handles = self.i_module.rigNull.handles
            if len(self.returnList) < handles:
                log.warning("Creating curve to get enough points")                
                curve = curves.curveFromPosList(self.returnList)
                mc.rebuildCurve (curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0,s=(handles-1), d=1, tol=0.001)
                self.returnList = curves.returnCVsPosList('curve1')#Get the pos of the cv's
                mc.delete(curve)

            #Store info
            #==============                  
            for i,p in enumerate(self.returnList):
                buffer[i][1] = p#need to ensure it's storing properly
                log.info('[%s,%s]'%(buffer[i],p))
                
            #Store locs
            #==============  
            log.debug("finish data: %s"% buffer)
            self.i_module.templateNull.templateStarterData = buffer#store it
            log.info("'%s' sized!"%self.i_module.getShortName())
            dragFactory.clickMesh.finalize(self)
        
    #Start up our sizer    
    return moduleSizer(mode = 'midPoint',
                       mesh = geo,
                       create = 'locator',
                       toCreate = namesToCreate)
    

@r9General.Timer   
def doSetParentModule(self,moduleParent,force = False):
    """
    Set a module parent of a module

    module(string)
    """
    #See if parent exists and is a module, if so...
    #>>>buffer children
    #>>>see if already connected
    #>>Check existance
        #==============	
    #Get our instance
    try:
        moduleParent.mNode#See if we have an instance

    except:
        if mc.objExists(moduleParent):
            moduleParent = r9Meta.MetaClass(moduleParent)#initialize
        else:
            log.warning("'%s' doesn't exist"%moduleParent)#if it doesn't initialize, nothing is there		
            return False	

    #Logic checks
    #==============
    if not moduleParent.hasAttr('mClass'):
        log.warning("'%s' lacks an mClass attr"%module.mNode)	    
        return False

    if moduleParent.mClass not in ['cgmModule']:
        log.warning("'%s' is not a recognized module type"%moduleParent.mClass)
        return False

    if not moduleParent.hasAttr('moduleChildren'):#Quick check
        log.warning("'%s'doesn't have 'moduleChildren' attr"%moduleParent.getShortName())#if it doesn't initialize, nothing is there		
        return False	

    buffer = copy.copy(moduleParent.moduleChildren) or []#Buffer till we have have append functionality	

    if self.mNode in buffer:
        log.warning("'%s' already connnected to '%s'"%(module,moduleParent.getShortName()))
        return False

        #Connect
        #==============	
    else:
        log.info("Current children: %s"%buffer)
        log.info("Adding '%s'!"%self.getShortName())    

        buffer.append(self.mNode) #Revist when children has proper add/remove handling
        del moduleParent.moduleChildren #Revist when children has proper add/remove handling
        moduleParent.connectChildren(buffer,'moduleChildren','moduleParent',force=force)#Connect
        if moduleParent.modulePuppet.mNode:
            self.__setMessageAttr__('modulePuppet',moduleParent.modulePuppet.mNode)#Connect puppet to 

    self.parent = moduleParent.parent
    return True


@r9General.Timer   
def getGeneratedCoreNames(self):
    """ 
    Generate core names for a module and return them

    self MUST be cgmModule

    RETURNS:
    generatedNames(list)
    
    TODO:
    Where to store names?
    """
    log.info("Generating core names via ModuleFactory - '%s'"%self.getShortName())

    ### check the settings first ###
    partType = self.moduleType
    log.debug("%s partType is %s"%(self.getShortName(),partType))
    settingsCoreNames = modules.returncgmTemplateCoreNames(partType)
    handles = self.rigNull.handles
    partName = NameFactory.returnRawGeneratedName(self.mNode,ignore=['cgmType','cgmTypeModifier'])

    ### if there are no names settings, genearate them from name of the limb module###
    generatedNames = []
    if settingsCoreNames == False:   
        cnt = 1
        for handle in range(handles):
            generatedNames.append('%s%s%i' % (partName,'_',cnt))
            cnt+=1

    elif int(self.rigNull.handles) > (len(settingsCoreNames)):
        log.info(" We need to make sure that there are enough core names for handles")       
        cntNeeded = self.rigNull.handles  - len(settingsCoreNames) +1
        nonSplitEnd = settingsCoreNames[len(settingsCoreNames)-2:]
        toIterate = settingsCoreNames[1]
        iterated = []
        for i in range(cntNeeded):
            iterated.append('%s%s%i' % (toIterate,'_',(i+1)))
        generatedNames.append(settingsCoreNames[0])
        for name in iterated:
            generatedNames.append(name)
        for name in nonSplitEnd:
            generatedNames.append(name) 

    else:
        generatedNames = settingsCoreNames[:self.rigNull.handles]

    #figure out what to do with the names
    if not self.templateNull.templateStarterData:
        buffer = []
        for n in generatedNames:
            buffer.append([str(n),[]])
        self.templateNull.templateStarterData = buffer
    else:
        for i,pair in enumerate(self.templateNull.templateStarterData):
            pair[0] = generatedNames[i]      
        
    return generatedNames


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
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




