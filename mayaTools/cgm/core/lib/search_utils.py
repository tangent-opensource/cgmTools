"""
------------------------------------------
search_utils: cgm.core.lib.search_utils
Author: Josh Burton
email: jjburton@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------

"""
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
import maya.mel as mel
# From Red9 =============================================================

# From cgm ==============================================================
from cgm.core import cgm_General as cgmGen
from cgm.core.cgmPy import validateArgs as VALID
reload(VALID)
from cgm.core.lib import shared_data as coreShared
from cgm.core.lib import name_utils as NAME
from cgm.core.lib import attribute_utils as ATTR
from cgm.lib import attributes

from cgm.lib import lists
#>>> Utilities
#===================================================================   
is_shape = VALID.is_shape
is_transform = VALID.is_transform    
get_mayaType = VALID.get_mayaType
get_transform = VALID.get_transform 

def get_tag(node = None, tag = None):
    """
    Get the info on a given node with a provided tag
    
    :parameters:
        node(str): Object to check

    :returns
        status(bool)
    """   
    _str_func = 'get_tag'
    _node = VALID.stringArg(node,False,_str_func) 
    
    if (mc.objExists('%s.%s' %(_node,tag))) == True:
        messageQuery = (mc.attributeQuery (tag,node=_node,msg=True))
        if messageQuery == True:
            returnBuffer = attributes.returnMessageData(_node,tag,False)
            if not returnBuffer:
                return False
            elif VALID.get_mayaType(returnBuffer[0]) == 'reference':
                if attributes.repairMessageToReferencedTarget(_node,tag):
                    return attributes.returnMessageData(_node,tag,False)[0]
                return returnBuffer[0]
            return returnBuffer[0]
        else:
            infoBuffer = mc.getAttr('%s.%s' % (_node,tag))
            if infoBuffer is not None and len(list(str(infoBuffer))) > 0:
                return infoBuffer
            else:
                return False
    else:
        return False    

def get_objectSetsDict():
    """ 
    Return a semi intelligent dictionary of sets in a mays scene file.

    Return dict keys:
    all(list) -- all sets found
    maya(list) -- maya made and controlled sets (tweakSet, etc)
    render(list) -- sets returned by mc.listSets(type=1)
    deformer(list) -- sets returned by mc.listSets(type=2)
    referenced(dict) -- ['From Scene'] are local sets, all other sets are indexed to their reference prefix
    qss(list) -- quick select sets
    types(dict) -- Sets indexed to their type as understood by cgm tools. 'typeModifier' tag in this case

    """    
    returnSetsDict = {'maya':[],'qss':[],'referenced':{},'cgmTypes':{},'objectSetGroups':[]}

    returnSetsDict['all'] = mc.ls(type='objectSet') or []
    returnSetsDict['render'] = mc.listSets(type = 1) or []
    returnSetsDict['deformer'] = mc.listSets(type = 2) or []    

    refBuffer = {'From Scene':[]}
    returnSetsDict['referenced'] = refBuffer

    typeBuffer = {'NONE':[]}
    returnSetsDict['cgmTypes'] = typeBuffer

    for s in returnSetsDict['all']:
        #Get our qss sets
        if mc.sets(s,q=True,text=True) == 'gCharacterSet':
            returnSetsDict['qss'].append(s)

        #Get our maya sets
        for check in ['defaultCreaseDataSet',
                      'defaultObjectSet',
                      'defaultLightSet',
                      'initialParticleSE',
                      'initialShadingGroup',
                      'Vray',
                      'SG',
                      ['cluster','Set'],
                      ['skinCluster','Set'],
                      'tweakSet']:
            if type(check) is list:
                buffer = []
                for c in check:
                    if c in s:
                        buffer.append(1)
                    else:buffer.append(0)
                if len(buffer) == sum(buffer):
                    returnSetsDict['maya'].append(s)
                    break

            elif check in s:
                returnSetsDict['maya'].append(s)
                break

        # Get our reference prefixes and sets sorted out
        if mc.referenceQuery(s, isNodeReferenced=True):
            refPrefix = NAME.get_refPrefix(s)

            if refPrefix in refBuffer.keys():
                refBuffer[refPrefix].append(s)
            else:
                refBuffer[refPrefix] = [s]
        else:
            refBuffer['From Scene'].append(s)

        #Type sort
        buffer = ATTR.get(s,'cgmType')
        for tag,v in coreShared.objectSetTypes.iteritems():
            if v == buffer:
                if tag in typeBuffer.keys():
                    typeBuffer[tag].append(s)
                else:
                    typeBuffer[tag] = [s]
        else:
            typeBuffer['NONE'].append(s)

        #Set group check
        if ATTR.get(s,'cgmType') == 'objectSetGroup':
            returnSetsDict['objectSetGroups'].append(s)

    return returnSetsDict



def get_nonintermediateShape(shape):
    """
    Get the nonintermediate shape on a transform
    
    :parameters:
        shape(str): Shape to check

    :returns
        non intermediate shape(string)
    """   
    _str_func = "get_nonintermediate"
    
    if not VALID.is_shape(shape):
        _shapes = mc.listRelatives(shape, fullPath = True)
        _l_matches = []
        for s in _shapes:
            if not ATTR.get(s,'intermediateObject'):
                _l_matches.append(s)
        if len(_l_matches) == 1:
            return _l_matches[0]
        else:
            raise ValueError,"Not sure what to do with this many intermediate shapes: {0}".format(_l_matches)        
    elif ATTR.get(shape,'intermediateObject'):
        _type = VALID.get_mayaType(shape)
        _trans = SEARCH.get_transform(shape)
        _shapes = mc.listRelatives(_trans,s=True,type=_type, fullPath = True)
        _l_matches = []
        for s in _shapes:
            if not ATTR.get(s,'intermediateObject'):
                _l_matches.append(s)
        if len(_l_matches) == 1:
            return _l_matches[0]
        else:
            raise ValueError,"Not sure what to do with this many intermediate shapes: {0}".format(_l_matches)
    else:
        return shape

def get_all_parents(node = None, shortNames = True):
    """
    Get all the parents of a given node where the last parent is the top of the heirarchy
    
    :parameters:
        node(str): Object to check
        shortNames(bool): Whether you just want short names or long

    :returns
        parents(list)
    """   
    _str_func = 'get_all_parents'
    _node = VALID.stringArg(node,False,_str_func) 
    
    _l_parents = []
    tmpObj = node
    noParent = False
    while noParent == False:
        tmpParent = mc.listRelatives(tmpObj,allParents=True,fullPath=True)
        if tmpParent:
            if len(tmpParent) > 1:
                raise ValueError,"Resolve what to do with muliple parents...{0} | {1}".format(node,tmpParent)
            _l_parents.append(tmpParent[0])
            tmpObj = tmpParent[0]
        else:
            noParent = True
    if shortNames:
        return [NAME.get_short(o) for o in _l_parents]
    return _l_parents 

def get_time(mode = 'current'):
    """
    Get time line frame data
    
    :parameters:
        mode(str): O
            current - current frame
            slider - slider range
            scene - scene range
            selected - selected frames in timeline
        
    :returns
        float/[float,float]
    """   
    _str_func = 'get_time'
    returnDict = {}
    if mode == 'current':
        return mc.currentTime(q=True)
    elif mode == 'scene':
        return [mc.playbackOptions(q=True,animationStartTime=True), mc.playbackOptions(q=True,animationEndTime=True)]
    elif mode == 'slider':
        return [mc.playbackOptions(q=True,min=True), mc.playbackOptions(q=True,max=True)]
    elif mode == 'selected':
        #Thanks to Brad Clark for this one
        aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
        if not mc.timeControl(aPlayBackSliderPython, query=True, rangeVisible=True):
            log.info("|{0}| >> No time selected".format(_str_func))        
            return False
        return mc.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)


def get_timeline_dict():
    """
    Returns timeline info as a dictionary
    
    :returns
        dict :: currentTime,sceneStart,sceneEnd,rangeStart,rangeEnd
    """   
    _str_func = 'get_timeline_dict'
    returnDict = {}
    returnDict['currentTime'] = mc.currentTime(q=True)
    returnDict['sceneStart'] = mc.playbackOptions(q=True,animationStartTime=True)
    returnDict['sceneEnd'] = mc.playbackOptions(q=True,animationEndTime=True)
    returnDict['rangeStart'] = mc.playbackOptions(q=True,min=True)
    returnDict['rangeEnd'] = mc.playbackOptions(q=True,max=True)

    return returnDict    

def get_key_indices_from(node = None, mode = 'all'):
    """
    Return a list of the time indexes of the keyframes on an object

    :parameters:
        node(str): What you want to get the keys of
        mode(str):
            all -- Every key
            next --
            previous -- 
            forward --
            back --
            selected - from selected range
    
    :returns
        list of keys(list)
    """ 
    _str_func = 'get_key_indices'
    
    if not ATTR.get_keyed(node):
        return []
    
    initialTimeState = mc.currentTime(q=True)
    keyFrames = []
    
    if mode == 'next':
        _key = mc.findKeyframe(node,which = 'next',an='objects')
        if _key > initialTimeState:
            return [_key]
        return []
    elif mode == 'forward':
        lastKey = mc.findKeyframe(node,which = 'last',an='objects')
        mc.currentTime(initialTimeState-1)        
        while mc.currentTime(q=True) != lastKey:
            keyBuffer = mc.findKeyframe(node,which = 'next',an='objects')
            if keyBuffer > initialTimeState:
                keyFrames.append(keyBuffer)
            mc.currentTime(keyBuffer)
        if lastKey > initialTimeState:
            keyFrames.append(lastKey) 
    elif mode in ['previous','back']:
        firstKey = mc.findKeyframe(node,which = 'first',an='objects')
        lastKey = mc.findKeyframe(node,which = 'last',an='objects')        
        mc.currentTime(firstKey-1)
        while mc.currentTime(q=True) != lastKey:
            if mc.currentTime(q=True) >= initialTimeState:
                log.debug('higher: {0}'.format(mc.currentTime(q=True)))
                break
            keyBuffer = mc.findKeyframe(node,which = 'next',an='objects')
            if keyBuffer < initialTimeState:
                keyFrames.append(keyBuffer)
                #log.debug(keyFrames)
                mc.currentTime(keyBuffer)
            else:
                break
        if mode == 'previous' and keyFrames:
            keyFrames = [keyFrames[-1]]

        
        
    elif mode in ['all','selected']:
        firstKey = mc.findKeyframe(node,which = 'first',an='objects')
        lastKey = mc.findKeyframe(node,which = 'last',an='objects')
    
        keyFrames.append(firstKey)
        mc.currentTime(firstKey-1)
        while mc.currentTime(q=True) != lastKey:
            keyBuffer = mc.findKeyframe(node,which = 'next',an='objects')
            keyFrames.append(keyBuffer)
            mc.currentTime(keyBuffer)
    
        keyFrames.append(lastKey)
    
        # Put the time back where we found it
        mc.currentTime(initialTimeState)
        if mode == 'selected':
            _range = get_time('selected')
            if not _range:
                return False
            _l_cull = []
            for k in keyFrames:
                if k > (_range[0]-1) and k < (_range[1]):
                    _l_cull.append(k)
            keyFrames = _l_cull
                
        
    else:
        raise ValueError,"Unknown mode: {0}".format(mode)
    
    mc.currentTime(initialTimeState)
    return lists.returnListNoDuplicates(keyFrames)
    

def get_selectedFromChannelBox(attributesOnly = False):
    """ 
    Returns a list of selected object attributes from the channel box
    
    :parameters:
        attributesOnly(bool): Whether you want
        
    Keyword arguments:
    returnRaw() -- whether you just want channels or objects combined with selected attributes

    """    
    _sel = mc.ls(sl=True)
    ChannelBoxName = mel.eval('$tmp = $gChannelBoxName');

    sma = mc.channelBox(ChannelBoxName, query=True, sma=True)
    ssa = mc.channelBox(ChannelBoxName, query=True, ssa=True)
    sha = mc.channelBox(ChannelBoxName, query=True, sha=True)
    soa = mc.channelBox(ChannelBoxName, query=True, soa=True)


    channels = []
    if sma:
        channels.extend(sma)
    if ssa:
        channels.extend(ssa)
    if sha:
        channels.extend(sha)
    if soa:
        channels.extend(soa)
    
    if channels and _sel:
        _channels_long = []
        for c in channels:
            _channels_long.append(ATTR.get_nameLong(_sel[0],c))
            
        if attributesOnly:
            return _channels_long
        else:
            _res = []
            for item in _sel:
                for attr in _channels_long:
                    _res.append("{0}.{1}".format(item,attr))
            return _res
    return False 

def get_referencePrefix(node = None):
    """
    Get the reference prefix of a node...

    :parameters:
        node(str): What you want to get the keys of

    :returns
        list of keys(list)
    """ 
    _str_func = 'get_referencePrefix'
    _node =  VALID.mNodeString(node)
    
    if mc.referenceQuery(_node, isNodeReferenced=True):
        splitBuffer = _node.split(':')
        return (':'.join(splitBuffer[:-1]))
    return False


def seek_upStream(startingNode,endObjType = None, mode = 'objType', getPlug=False):
    """
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    NOT DONE>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ACKNOWLEDGEMENT:
    Modified from Scott Englert's MEL script

    DESCRIPTION:
    Replacement for getAttr which get's message objects as well as parses double3 type
    attributes to a list

    ARGUMENTS:
    obj(string)
    attr(string)

    RETURNS:
    attrInfo(varies)
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    #
    _str_func = 'seek_upStream'    
    currentNode = startingNode
    destNodeType = ''
    timeOut = 0
    # do a loop to keep doing down stream on the connections till the type
    # of what we are searching for is found
    _done = False
    if mode == 'objType':
        if endObjType == None:
            raise ValueError,"Must have endObjType when objType mode is True"
        else:
            destNodeType = ''
        
    while not _done and timeOut < 50:
        destNodeName = mc.listConnections(currentNode, scn = True, d=False, s= True)
        if not destNodeName:
            endNode = 'not found'
            break
        if getPlug:
            destNodeNamePlug = mc.listConnections(currentNode, scn = True, p = True,d=False, s= True)
            endNode = destNodeName[0]
        else:
            endNode = destNodeName[0]
        # Get the Node Type
        destNodeTypeBuffer = mc.ls(destNodeName[0], st = True)
        destNodeType = destNodeTypeBuffer[1]
        
        if mode == 'objType' and destNodeType == endObjType:
            _done = True
        elif mode == 'isTransform' and is_transform(destNodeName[0]):
            _done = True

        if _done and getPlug:
            return destNodeNamePlug[0]         

        if destNodeType == 'pairBlend':
            pairBlendInPlug = mc.listConnections(currentNode, scn = True, p = True,d=False, s= True)
            print ('pairBlendInPlug is %s' %pairBlendInPlug)
        else:
            currentNode = destNodeName[0]
            log.info("|{0}| >> Current: {1} | {2} | {3}".format(_str_func,timeOut,destNodeType,currentNode))
        timeOut +=1
    return endNode

def seek_downStream(startingNode, endObjType = None, mode = 'objType', getPlug=False):
    """
    endObjType
    isTransform
    
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    ACKNOWLEDGEMENT:
    Pythonized from Scott Englert's MEL

    DESCRIPTION:
    Replacement for getAttr which get's message objects as well as parses double3 type
    attributes to a list

    ARGUMENTS:
    obj(string)
    attr(string)

    RETURNS:
    attrInfo(varies)
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    #
    _str_func = 'seek_downStream'
    currentNode = startingNode
    destNodeType = ''
    timeOut = 0
    # do a loop to keep doing down stream on the connections till the type
    # of what we are searching for is found
    _done = False
    if mode == 'objType':
        if endObjType == None:
            raise ValueError,"Must have endObjType when objType mode is True"
        else:
            destNodeType = ''
        
    while not _done  and timeOut < 50:
        if timeOut == 50:
            log.warning("|{0}| >> downStream seek timed out".format(_str_func))
            break
        else:
            destNodeName = mc.listConnections(currentNode, scn = True, s= False)
            if not destNodeName:
                log.warning("|{0}| >> Node not found: {1}".format(_str_func,destNodeName))
                endNode = 'not found'
                break
            if getPlug:
                destNodeNamePlug = mc.listConnections(currentNode, scn = True, p = True, s= False)
                endNode = destNodeName[0]
            else:
                endNode = destNodeName[0]
                
            # Get the Node Type
            destNodeTypeBuffer = mc.ls(destNodeName[0], st = True)
            destNodeType = destNodeTypeBuffer[1]
            
            if mode == 'objType' and destNodeType == endObjType:
                _done = True
            elif mode == 'isTransform' and is_transform(destNodeName[0]):
                _done = True

            if _done and getPlug:
                return destNodeNamePlug[0] 
            
            if destNodeType == 'pairBlend':
                pairBlendInPlug = mc.listConnections(currentNode, scn = True, p = True, s= False)
                print ('pairBlendInPlug is %s' %pairBlendInPlug)
            else:
                currentNode = destNodeName[0]
                log.debug("|{0}| >> Current: {1} | {2} | {3}".format(_str_func,timeOut,destNodeType,currentNode))                
            timeOut +=1
    return endNode

    
    