"""
------------------------------------------
cgm.core.mrs.blocks.simple.master
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

================================================================
"""
# From Python =============================================================
import copy
import re

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
from cgm.core.lib import curve_Utils as CURVES
from cgm.core.lib import rigging_utils as RIG
from cgm.core.lib import snap_utils as SNAP
from cgm.core.lib import attribute_utils as ATTR
reload(ATTR)
# From cgm ==============================================================
from cgm.core import cgm_Meta as cgmMeta

#=============================================================================================================
#>> Block data
#=============================================================================================================
__version__ = 'alpha.06142017'
__autoTemplate__ = True

l_attrsStandard = ['proxyType','hasRootJoint','moduleTarget']

d_attrsToMake = {'puppetName':'string'}

d_defaultSettings = {'version':__version__,
                     'puppetName':'NotBatman',
                     'baseSize':10,
                     'attachPoint':'end',
                     'proxyType':1}


#=============================================================================================================
#>> Template
#=============================================================================================================
def template(self):
    _crv = CURVES.create_controlCurve(self.mNode,shape='circleArrow',direction = 'y+', sizeMode = 'fixed', size = self.baseSize)
    RIG.shapeParent_in_place(self.mNode,_crv,False)
    return True

def templateDelete(self):
    pass#...handled in generic callmc.delete(self.getShapes())

def is_template(self):
    if self.getShapes():
        return True
    return False
#=============================================================================================================
#>> Prerig
#=============================================================================================================
def prerig(self):
    self._factory.puppet_verify()    
    pass

def prerigDelete(self):
    try:self.moduleTarget.delete()
    except Exception,err:
        for a in err:
            print a
    return True   

def is_prerig(self):
    _str_func = 'is_prerig'
    _l_missing = []
    
    _d_links = {self : ['moduleTarget']}
    
    for plug,l_links in _d_links.iteritems():
        for l in l_links:
            if not plug.getMessage(l):
                _l_missing.append(plug.p_nameBase + '.' + l)
                
    if _l_missing:
        log.info("|{0}| >> Missing...".format(_str_func))  
        for l in _l_missing:
            log.info("|{0}| >> {1}".format(_str_func,l))  
        return False
    return True
#=============================================================================================================
#>> rig
#=============================================================================================================
def rig(self):
    #
    self.moduleTarget._verifyMasterControl(size = self.baseSize)
    
    if self.hasRootJoint:
        if not is_skeletonized(self):
            skeletonize(self)
            
        mJoint = self.getMessage('rootJoint', asMeta = True)[0]
        log.info(mJoint)
        mJoint.p_parent = self.moduleTarget.masterNull.skeletonGroup  

def rigDelete(self):
    try:self.moduleTarget.masterControl.delete()
    except Exception,err:
        for a in err:
            print a
    return True
            
def is_rig(self):
    _str_func = 'is_rig'
    _l_missing = []
    
    _d_links = {'moduleTarget' : ['masterControl']}
    
    for plug,l_links in _d_links.iteritems():
        _mPlug = self.getMessage(plug,asMeta=True)
        if not _mPlug:
            _l_missing.append("{0} : {1}".format(plug,l_links))
            continue
        for l in l_links:
            if not _mPlug[0].getMessage(l):
                _l_missing.append(plug.p_nameBase + '.' + l)
                

    if _l_missing:
        log.info("|{0}| >> Missing...".format(_str_func))  
        for l in _l_missing:
            log.info("|{0}| >> {1}".format(_str_func,l))  
        return False
    return True

#=============================================================================================================
#>> Skeleton
#=============================================================================================================
def skeletonize(self):
    #    
    if is_skeletonized(self):
        return True
    
    if self.hasRootJoint:
        mJoint = self.doCreateAt('joint')
        mJoint.connectParentNode(self,'module','rootJoint')
        #mJoint.parent = self.moduleTarget.masterNull.skeletonGroup        
        #mJoint.connectParentNode(self.moduleTarget.masterNull.mNode,'module','rootJoint')
        #mJoint.doStore('cgmName',"{0}.puppetName".format(self.mNode))
        self.copyAttrTo('puppetName',mJoint.mNode,'cgmName',driven='target')
        mJoint.doStore('cgmTypeModifier','root')
        mJoint.doName()
        return mJoint.mNode
        #self.msgList_connect('modul')
        
def is_skeletonized(self):
    if self.hasRootJoint:
        if not self.getMessage('rootJoint'):
            return False
    return True


            






 








