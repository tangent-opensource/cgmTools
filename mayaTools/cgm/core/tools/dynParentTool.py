"""
------------------------------------------
dynParentTool: cgm.core.tools
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------

================================================================
"""
# From Python =============================================================
import copy
import re

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


import maya.cmds as mc


import cgm.core.classes.GuiFactory as cgmUI
from cgm.core import cgm_RigMeta as cgmRigMeta

reload(cgmUI)
mUI = cgmUI.mUI

from cgm.core.lib import shared_data as SHARED
from cgm.core.lib import search_utils as SEARCH
from cgm.core.lib import name_utils as NAMES
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core import cgm_General as cgmGEN
from cgm.core import cgm_Meta as cgmMeta
from cgm.core.lib import attribute_utils as ATTR
from cgm.core.lib import list_utils as LISTS
from cgm.core.tools.markingMenus.lib import contextual_utils as CONTEXT
from cgm.core.cgmPy import str_Utils as STRINGS
from cgm.core.tools import attrTools as ATTRTOOLS
from cgm.lib import lists
#>>> Root settings =============================================================
__version__ = 'Alpha 1.0.05232017'

#__toolURL__ = 'www.cgmonks.com'
#__author__ = 'Josh Burton'
#__owner__ = 'CG Monks'
#__website__ = 'www.cgmonks.com'
#__defaultSize__ = 375, 350


class ui(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = 'cgmDynParentTool_ui'    
    WINDOW_TITLE = 'cgmDynParentTool - {0}'.format(__version__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 250,300
    #_checkBoxKeys = ['shared','default','user','others']
    __modes = 'space','orient','follow'
    
    def insert_init(self,*args,**kws):
            if kws:log.debug("kws: %s"%str(kws))
            if args:log.debug("args: %s"%str(args))
            log.info(self.__call__(q=True, title=True))
    
            self.__version__ = __version__
            self.__toolName__ = 'cgmMultiSet'		
            #self.l_allowedDockAreas = []
            self.WINDOW_TITLE = ui.WINDOW_TITLE
            self.DEFAULT_SIZE = ui.DEFAULT_SIZE

            self.uiPopUpMenu_parent = False
            self._l_toEnable = []
            self.create_guiOptionVar('dynParentMode',  defaultValue = ui.__modes[0])
            #self.create_guiOptionVar('valuesMode',  defaultValue = 'primeNode')                        
            #self.create_guiOptionVar('context',  defaultValue = 'loaded')            
            self.uiScrollList_parents = False
            self._mNode = False
            self._mGroup = False

    def build_menus(self):
        #self.uiMenu_context = mUI.MelMenu( l='Context', pmc=self.buildMenu_context)           

        self.uiMenu_help = mUI.MelMenu( l='Help', pmc=self.buildMenu_help)           
    
    def buildMenu_help( self, *args):
        self.uiMenu_help.clear()
    
        mc.menuItem(parent=self.uiMenu_help,
                    l = 'Get Help',
                    c='import webbrowser;webbrowser.open("http://www.cgmonks.com/tools/maya-tools/cgmmarkingmenu/attrtools-2-0/");',                        
                    rp = 'N')    
        mUI.MelMenuItem( self.uiMenu_help, l="Log Self",
                         c=lambda *a: cgmUI.log_selfReport(self) )      
                
    def uiFunc_clear_loaded(self):
        _str_func = 'uiFunc_clear_loaded'  
        self._mNode = False
        self._mGroup = False
        self._utf_obj(edit=True, l='')      
        self.uiField_report(edit=True, l='...')
        #self.uiReport_objects()
        self.uiScrollList_parents.clear()
        
        for o in self._l_toEnable:
            o(e=True, en=False)        
        

    def uiFunc_load_selected(self, bypassAttrCheck = False):
        _str_func = 'uiFunc_load_selected'  
        self._ml_parents = []
        self._mNode = False
        
        _sel = mc.ls(sl=True)
            
        #Get our raw data
        if _sel:
            mNode = cgmMeta.validateObjArg(_sel[0])
            _short = mNode.p_nameShort            
            log.debug("|{0}| >> Target: {1}".format(_str_func, _short))
            self._mNode = mNode
            
            self._utf_obj(edit=True, l=_short)
            self.uiFunc_updateDynParentDisplay()
        else:
            log.warning("|{0}| >> Nothing selected.".format(_str_func))            
            self.uiFunc_clear_loaded()
            
        #self.uiReport_do()
        #self.uiFunc_updateScrollAttrList()
        

    def uiFunc_updateDynParentDisplay(self):
        _str_func = 'uiFunc_updateDynParentDisplay'  
        self.uiScrollList_parents.clear()
        
        if not self._mNode:
            log.info("|{0}| >> No target.".format(_str_func))                        
            #No obj
            self._utf_obj(edit=True, l='')
            
            for o in self._l_toEnable:
                o(e=True, en=False)
                
        _d = get_dict(self._mNode.mNode)
        
        if _d:
            log.info("|{0}| >> dynParentGroup detected...".format(_str_func))
            
            self._utf_obj(edit=True, l=_d['dynChild'].p_nameShort)
            
            _l_report = ["mode: {0}".format(_d['mode']),'targets: {0}'.format(len(_d['dynParents']))]
            self.uiField_report(edit=True, label = 'DynGroup: {0}'.format(' | '.join(_l_report)))            
            self._mNode = _d['dynChild']
            self._mGroup = _d['dynGroup']
            self._uiList_modeButtons[_d['mode']].select()        
            
            for o in self._l_toEnable:
                o(e=True, en=True)  
                
            self.uiFunc_updateScrollParentList()
        else:
            log.info("|{0}| >> No dynParentGroup".format(_str_func))                        
            #Not dynParentGroup
            _short = self._mNode.p_nameShort            
            self._utf_obj(edit=True, l=_short)
    
            self.uiField_report(edit=True, label = 'No dynParentGroup detected')
    
            for o in self._l_toEnable:
                o(e=True, en=False)               
                   
        
    def uiFunc_updateScrollParentList(self):
        _str_func = 'uiFunc_updateScrollParentList'          
        self.uiScrollList_parents.clear()
        
        if not self._mGroup:
            return False      
        
        ml_parents = self._mGroup.msgList_get('dynParents')
        
        _l_dat = []
        _len = len(ml_parents)        
        
        if not ml_parents:
            return False
        
        #...menu...
        _progressBar = cgmUI.doStartMayaProgressBar(_len,"Processing...")
        _mode = self._mGroup.dynMode
        
        try:
            for i,mObj in enumerate(ml_parents):
                _short = mObj.p_nameShort
                log.debug("|{0}| >> scroll list update: {1}".format(_str_func, _short))  
                
                mc.progressBar(_progressBar, edit=True, status = ("{0} Processing Parent: {1}".format(_str_func,_short)), step=1)                    
                
                _l_report = [str(i)]
                
                _alias = ATTR.get(_short,'cgmAlias')
                if _alias:
                    _l_report.append("{0} ({1})".format(_alias,_short))
                    #_l_report.append('alias ({0})'.format(_alias))
                else:
                    _l_report.append(_short)
                    
                #if i == ATTR.get(self)
                if _mode == 0:
                    if self._mNode.space == i:
                        _l_report.append('((Space))')
                elif _mode == 1:
                    if self._mNode.orientTo == i:
                        _l_report.append('((Orient))')
                else:
                    if self._mNode.orientTo == i:
                        _l_report.append('((Orient))')
                    if self._mNode.follow == i:
                        _l_report.append('((Follow))')

                _str = " \ ".join(_l_report)
                log.debug("|{0}| >> str: {1}".format(_str_func, _str))  
                
                self.uiScrollList_parents.append(_str)

        except Exception,err:
            try:cgmUI.doEndMayaProgressBar(_progressBar)
            except:
                raise Exception,err

        cgmUI.doEndMayaProgressBar(_progressBar)
        
        
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
        self._d_uiCheckBoxes = {}
        
        _MainForm = mUI.MelFormLayout(parent,ut='cgmUISubTemplate')
        _header_top = cgmUI.add_Header('cgmDynParentGroup',overrideUpper=True)        

        #>>>Objects Load Row ---------------------------------------------------------------------------------------
        _row_objLoad = mUI.MelHSingleStretchLayout(_MainForm,ut='cgmUITemplate',padding = 5)        
        
        mUI.MelSpacer(_row_objLoad,w=20)
        mUI.MelLabel(_row_objLoad, 
                     l='dynChild:')
        
        _utf_objLoad = mUI.MelLabel(_row_objLoad,ut='cgmUITemplate',l='',
                                    en=False)
        self._utf_obj = _utf_objLoad
        cgmUI.add_Button(_row_objLoad,'<<',
                         cgmGEN.Callback(self.uiFunc_load_selected),
                         #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
                         "Load selected object.")   
        
        
        _row_objLoad.setStretchWidget(_utf_objLoad)
        mUI.MelSpacer(_row_objLoad,w=20)
        
        _row_objLoad.layout()
        
        #>>>Report ---------------------------------------------------------------------------------------
        _row_report = mUI.MelHLayout(_MainForm ,ut='cgmUIInstructionsTemplate',h=20)
        self.uiField_report = mUI.MelLabel(_row_report,
                                           bgc = SHARED._d_gui_state_colors.get('help'),
                                           label = '...',
                                           h=20)
        _row_report.layout()        
        
        
        #>>>Mode Row ---------------------------------------------------------------------------------------
        _row_modeSelect = mUI.MelHSingleStretchLayout(_MainForm,ut='cgmUISubTemplate',padding = 5,en=True)
        
        mUI.MelLabel(_row_modeSelect,l="Mode:")
        _row_modeSelect.setStretchWidget(mUI.MelSeparator(_row_modeSelect))
        
        _uiRC_mode = mUI.MelRadioCollection()
        _v = self.var_dynParentMode.value
        
        _d_annos = {'space':'Will use objects loaded to the ui',
                    'follow':'Will use any selected objects primNode type',
                    'orientTo':'Will use any objects below primeNode heirarchally and matching type'}
        self._uiList_modeButtons = []
        for i,item in enumerate(ui.__modes):
            _button = _uiRC_mode.createButton(_row_modeSelect,
                                              label=item,
                                              ann=_d_annos.get(item,'Fill out the dict!'),
                                              cc = cgmGEN.Callback(self.var_dynParentMode.setValue,item))
            if item == _v:
                _button.select()
            self._uiList_modeButtons.append(_button)
                  
        
        self._uiRC_mode = _uiRC_mode
        _row_modeSelect.layout()
        
        #self._l_toEnable.append(_row_modeSelect)
        #if self.CreateAttrTypeOptionVar.value:
        
        #>>> Group Buttons Row ---------------------------------------------------------------------------------------
        _row_groupsButtons = mUI.MelHLayout(_MainForm,ut='cgmUISubTemplate',padding = 2,en=True)
    
        cgmUI.add_Button(_row_groupsButtons,'Rebuild',
                         cgmGEN.Callback(self.uiFunc_dynGroup_rebuild),                         
                         "Rebuild a dynParentGroup. If it doens't exist, create it.")        
    
        cgmUI.add_Button(_row_groupsButtons,'Clear',
                         cgmGEN.Callback(self.uiFunc_dynGroup_clear),                         
                         "Remove a dynParentGroup")
        
        cgmUI.add_Button(_row_groupsButtons,'Copy',
                         cgmGEN.Callback(self.uiFunc_dynGroup_copy),                         
                         "Copy the loaded dynParentGroup data to selected objects")
        
        _row_groupsButtons.layout()           
        
        
        #>>>Push Values header ---------------------------------------------------------------------------------------        
        mc.setParent(_MainForm)        
        _header_parents = cgmUI.add_Header('Parents')        
        
        #>>> Parents list ---------------------------------------------------------------------------------------
        self.uiScrollList_parents = mUI.MelObjectScrollList(_MainForm, allowMultiSelection=True,en=False,
                                                            dcc = self.uiFunc_dc_fromList,
                                                            selectCommand = self.uiFunc_selectParent_inList)
        
                                                            #dcc = cgmGEN.Callback(self.uiFunc_attrManage_fromScrollList,**{'mode':'value'}),

        self._l_toEnable.append(self.uiScrollList_parents)

        
        #>>> Parent Buttons Row ---------------------------------------------------------------------------------------
        _row_parentsButtons = mUI.MelHLayout(_MainForm,ut='cgmUISubTemplate',padding = 2,en=False)
        self._l_toEnable.append(_row_parentsButtons)
            
        cgmUI.add_Button(_row_parentsButtons,'Add',
                         cgmGEN.Callback(self.uiFunc_dynGroup_addParents),                         
                         "Add selected objects as dynParent nodes")     
        cgmUI.add_Button(_row_parentsButtons,'Remove',
                         cgmGEN.Callback(self.uiFunc_dynGroup_removeParents),                        
                         "Refresh the attributes in the scroll list. Useful if keyed.")   
        cgmUI.add_Button(_row_parentsButtons,'Move Up',
                         cgmGEN.Callback(self.uiFunc_dynParents_reorder,0),                        
                         "Refresh the attributes in the scroll list. Useful if keyed.")         
        cgmUI.add_Button(_row_parentsButtons,'Move Dn',
                         cgmGEN.Callback(self.uiFunc_dynParents_reorder,1),                        
                         "Refresh the attributes in the scroll list. Useful if keyed.") 
        _row_parentsButtons.layout()        
        
        
        #>>> Layout form ---------------------------------------------------------------------------------------
        _MainForm(edit = True,
                  af = [(_header_top,"top",0),
                        (_header_top,"left",0),
                        (_header_top,"right",0),                        
                        (_row_objLoad,"left",0),
                        (_row_objLoad,"right",0),
                        (_row_report,"left",0),
                        (_row_report,"right",0),                        
                        (self.uiScrollList_parents,"left",0),
                        (self.uiScrollList_parents,"right",0),
                        (_row_parentsButtons,"left",0),
                        (_row_parentsButtons,"right",0),
                        (_row_groupsButtons,"left",0),
                        (_row_groupsButtons,"right",0),                        
                        (_header_parents,"left",0),
                        (_header_parents,"right",0),
                        (_row_modeSelect,"left",5),
                        (_row_modeSelect,"right",5),
                        (_row_parentsButtons,"bottom",0),

                        ],
                  ac = [(_row_objLoad,"top",2,_header_top),
                        (_row_report,"top",0,_row_objLoad),
                        (_row_modeSelect,"top",2,_row_report),
                        (_row_groupsButtons,"top",2,_row_modeSelect),                        
                        (_header_parents,"top",2,_row_groupsButtons),
                        (self.uiScrollList_parents,"top",0,_header_parents),
                        (self.uiScrollList_parents,"bottom",2,_row_parentsButtons),
                        
                       ],
                  attachNone = [(_row_parentsButtons,"top")])	        
        
        _sel = mc.ls(sl=True)
        if _sel:
            self.uiFunc_load_selected()                

        return
 
    #@cgmGEN.Timer
    def uiFunc_selectParent_inList(self): 
        _str_func = 'uiFunc_selectParent_inList'        
        if self.uiPopUpMenu_parent:
            self.uiPopUpMenu_parent.clear()
            self.uiPopUpMenu_parent.delete()
            self.uiPopUpMenu_parent = None
            
            
        ml_parents = self._mGroup.msgList_get('dynParents')
        _indices = self.uiScrollList_parents.getSelectedIdxs() or []
        log.debug("|{0}| >> indices: {1}".format(_str_func, _indices))    
        
        if not _indices:
            return
        
        self.uiPopUpMenu_parent = mUI.MelPopupMenu(self.uiScrollList_parents,button = 3)
        _popUp = self.uiPopUpMenu_parent           
                
        if len(_indices) == 1:
            _b_single = True
            
            log.debug("|{0}| >> Single pop up mode".format(_str_func))  
            _short = ml_parents[_indices[0]].p_nameShort
            mUI.MelMenuItem(_popUp,
                            label = "Single: {0}".format(_short),
                            en=False)            
        else:
            log.debug("|{0}| >> Multi pop up mode".format(_str_func))  
            mUI.MelMenuItem(_popUp,
                            label = "Mutli",
                            en=False)  
            _b_single = False
            
        
        if _b_single:
            mUI.MelMenuItem(_popUp,
                            label ='Alias',
                            ann = 'Enter value desired in prompt',
                            c = cgmGEN.Callback(self.uiFunc_parentManage_fromScrollList,**{'mode':'alias'}))
            mUI.MelMenuItem(_popUp,
                            label ='Clear Alias',
                            ann = 'Remove any alias',
                            c = cgmGEN.Callback(self.uiFunc_parentManage_fromScrollList,**{'mode':'aliasClear'}))
            mUI.MelMenuItem(_popUp,
                            label ='Switch To',
                            ann = 'Switch the mode to selected parent',
                            c = cgmGEN.Callback(self.uiFunc_parentManage_fromScrollList,**{'mode':'switch'}))            

        #Select
        mUI.MelMenuItem(_popUp,
                        label ='Select',
                        ann = 'Select specified indice parents',
                        c = cgmGEN.Callback(self.uiFunc_parentManage_fromScrollList,**{'mode':'select'}))  
        mUI.MelMenuItem(_popUp,
                        label ='Move Up',
                        ann = 'Move selected up in list',
                        c = cgmGEN.Callback(self.uiFunc_dynParents_reorder,0)) 
        mUI.MelMenuItem(_popUp,
                        label ='Move Down',
                        ann = 'Move selected down in list',
                        c = cgmGEN.Callback(self.uiFunc_dynParents_reorder,1)) 
        #Remove
        cgmGEN.Callback(self.uiFunc_dynParents_reorder,0),                        
        
        return
        
                
 
 
    def uiFunc_parentManage_fromScrollList(self,**kws):          
        
        _str_func = 'uiFunc_parentManage_fromScrollList'
        _indices = self.uiScrollList_parents.getSelectedIdxs()
                
        _mode = kws.get('mode',None)
        _fromPrompt = None
        
        if not self._mGroup:
            log.error("|{0}| >> No Group Loaded".format(_str_func))                                                        
            return False
        
        ml_parents = self._mGroup.msgList_get('dynParents')
            
        
        if not _indices:
            log.error("|{0}| >> Nothing selected".format(_str_func))                                                        
            return False
        
        _ml_targets = [ml_parents[i] for i in _indices]
        log.debug("|{0}| >> targets: {1}".format(_str_func,[mObj.mNode for mObj in _ml_targets]))                                                        
        
        
        _done = False

        if _mode is not None:
            log.debug("|{0}| >> mode: {1}".format(_str_func,_mode))  
            
            if _mode == 'alias':
                _fromPrompt = ATTRTOOLS.uiPrompt_getValue("Enter Alias","Type in your alias to be used in the marking menu")
                if _fromPrompt is None:
                    log.error("|{0}| >>  Mode: {1} | No value gathered...".format(_str_func,_mode)) 
                    return False
                else:
                    log.info("|{0}| >>  from prompt: {1} ".format(_str_func,_fromPrompt))  
                    _fromPrompt = STRINGS.strip_invalid(_fromPrompt,',[]{}()', functionSwap = False, noNumberStart = False)
                
                if _fromPrompt:
                    for mObj in _ml_targets:
                        mObj.addAttr('cgmAlias',value = _fromPrompt)
                        
            elif _mode == 'aliasClear':
                for mObj in _ml_targets:
                    mObj.delAttr('cgmAlias')    
                    
            elif _mode == 'select':
                mc.select([mObj.mNode for mObj in _ml_targets])
                
            elif _mode == 'switchTo':
                _dynMode = self._mGroup.dynMode
                if _dynMode == 0:
                    self._mGroup.doSwitchSpace('space',_indices[0])
                elif _dynMode == 1:
                    self._mGroup.doSwitchSpace('orientTo',_indices[0])
                else:
                    self._mGroup.doSwitchSpace('orientTo',_indices[0])
                    
                    
            

            else:
                log.error("|{0}| >>  Mode: {1} | Not implented...".format(_str_func,_mode))                                               
                return False
            
        self.uiFunc_updateDynParentDisplay()
        return True

        
    def uiFunc_get_buildDict(self):
        _str_func = 'uiFunc_get_buildDict' 
        _d = {}

        _idx = self._uiRC_mode.getSelectedIndex()
        _d['dynMode'] = _idx
        
        cgmGEN.log_info_dict(_d,_str_func)
        return _d
        
            
    def uiFunc_dynGroup_rebuild(self):
        _str_func = 'uiFunc_dynGroup_rebuild' 
        
        if not self._mNode:
            log.error("|{0}| >> No dyChild loaded to ui".format(_str_func))                                            
            return False
        
        _d_exists = get_dict(self._mNode.mNode)
        _d_build = self.uiFunc_get_buildDict()
        _d_build['dynChild'] = self._mNode
        if _d_exists and _d_exists.get('dynMode') != _d_build.get('dynMode'):
            log.error("|{0}| >> Modes don't match".format(_str_func))                                            
            
        
        
        #Build...
        verify_obj(self._mNode, _d_build.get('dynMode'))
        
        
        self.uiFunc_updateDynParentDisplay()
        
        
    def uiFunc_dynGroup_clear(self):
        _str_func = 'uiFunc_dynGroup_clear' 
    
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False    
        self._mGroup.doPurge()
        
        self.uiFunc_updateDynParentDisplay()
        
    def uiFunc_dynGroup_copy(self):
        _str_func = 'uiFunc_dynGroup_copy' 
    
        if not self._mNode:
            log.error("|{0}| >> No dyChild loaded to ui".format(_str_func))                                            
            return False  
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False              
        
        _l_context = CONTEXT.get_list('selection')
        _ml_copyTo = []
        for o in _l_context:
            mObj = cgmMeta.validateObjArg(o)
            if mObj == self._mNode:
                log.error("|{0}| >> Cannot copy to self".format(_str_func))                                            
            elif not VALID.is_transform(o):
                log.error("|{0}| >> Not a transform: {1}".format(_str_func,o))                                                            
            else:
                _ml_copyTo.append(mObj)
        
        if not _ml_copyTo:
            log.error("|{0}| >> No acceptable targets found".format(_str_func))                                            
            return False
        
        _d_build = {}
        for mObj in _ml_copyTo:
            if ATTR.get_message(mObj.mNode,'dynParentGroup'):
                mObj.dynParentGroup.doPurge()
                
            _d_build['dynChild'] = mObj.mNode
            _d_build['dynMode'] = self._mGroup.dynMode
            _d_build['dynParents'] = self._mGroup.msgList_get('dynParents')
            _mi_group = cgmRigMeta.cgmDynParentGroup(**_d_build)
            
    def uiFunc_dynGroup_addParents(self):
        _str_func = 'uiFunc_dynGroup_clear' 
    
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False    
        
        _l_context = CONTEXT.get_list('selection')
        _ml_add = []
        for o in _l_context:
            mObj = cgmMeta.validateObjArg(o)
            if mObj == self._mNode:
                log.error("|{0}| >> Cannot add self as parent".format(_str_func))                                            
            elif not VALID.is_transform(o):
                log.error("|{0}| >> Not a transform: {1}".format(_str_func,o))                                                            
            else:
                _ml_add.append(mObj)  
                
        if not _ml_add:
            log.error("|{0}| >> No eligible targets selected".format(_str_func))                                                                        
            return False
        
        for mObj in _ml_add:
            self._mGroup.addDynParent(mObj)
            
        self._mGroup.rebuild()
        self.uiFunc_updateDynParentDisplay()
        
    def uiFunc_dc_fromList(self):
        _str_func = 'uiFunc_dc_fromList'   
    
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False          
    
        ml_parents = self._mGroup.msgList_get('dynParents')
        _indices = self.uiScrollList_parents.getSelectedIdxs() or []
    
        if _indices:
            ml_parents[_indices[0]].select()
                        
    def uiFunc_dynGroup_removeParents(self):
        _str_func = 'uiFunc_dynGroup_removeParents'   
        
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False          
        
        _l_context = CONTEXT.get_list('selection')
        _ml_remove = []
        ml_parents = self._mGroup.msgList_get('dynParents')
        
        for o in _l_context:
            mObj = cgmMeta.validateObjArg(o)
            if mObj == self._mNode:
                log.error("|{0}| >> Cannot remove self as parent".format(_str_func))                                            
            elif not VALID.is_transform(o):
                log.error("|{0}| >> Not a transform: {1}".format(_str_func,o))                                                            
            else:
                _ml_remove.append(mObj)  
                
        _indices = self.uiScrollList_parents.getSelectedIdxs() or []
        if _indices:
            for i in _indices:
                if ml_parents[i] not in _ml_remove:
                    _ml_remove.append(ml_parents[i])
    
        if not _ml_remove:
            log.error("|{0}| >> No eligible targets selected".format(_str_func))                                                                        
            return False  
        
        log.error("|{0}| >> To remove: {1}".format(_str_func,_ml_remove))                                            
        self._mGroup.clearParents()
        
        for mObj in _ml_remove:
            _short = mObj.mNode
            log.info(mObj.mNode)
            for i,mP in enumerate(ml_parents):
                if mP.mNode == _short:
                    ml_parents.pop(i)
                
        for mObj in ml_parents:
            self._mGroup.addDynParent(mObj)
        
        self._mGroup.rebuild()        
            
        self.uiFunc_updateDynParentDisplay()
        
    def uiFunc_dynParents_reorder(self,direction = 0):
        """
        direction(int) - 0 is is negative (up), 1 is positive (dn)

        """
        _str_func = 'uiFunc_dynGroup_removeParents'   
        
        if not self._mGroup:
            log.error("|{0}| >> No dynGroup loaded to ui".format(_str_func))                                            
            return False          
        
        _l_context = CONTEXT.get_list('selection')
        _ml_remove = []
        ml_parents = self._mGroup.msgList_get('dynParents')
        _l_parents = [mObj.mNode for mObj in ml_parents]
      
        _indices = self.uiScrollList_parents.getSelectedIdxs() or []
        
        if not _indices:
            log.error("|{0}| >> No targets specified in parent list".format(_str_func))                                            
            return False  
        
        _to_move = []
        for i in _indices:
            _to_move.append(_l_parents[i])
            
        _initialValue = _l_parents[_indices[0]]
        
        _to_move = lists.reorderListInPlace(_l_parents,_to_move,direction)
        
        self._mGroup.clearParents()
        
        for o in _l_parents:
            self._mGroup.addDynParent(o)
        
        self._mGroup.rebuild()
        self.uiFunc_updateDynParentDisplay()
        
        
        self.uiScrollList_parents.selectByIdx(_l_parents.index(_initialValue))
        return True
            
                    
    
    def reorder(self, direction = 0):
        """   
        :Acknowledgement:
        Thank you to - http://www.the-area.com/forum/autodesk-maya/mel/how-can-we-reorder-an-attribute-in-the-channel-box/
    
        Reorders attributes on an object
    
        :parameters:
            node(str) -- 
            attrs(list) must be attributes on the object
            direction(int) - 0 is is negative (up on the channelbox), 1 is positive (up on the channelbox)
    
        :returns
            status(bool)
        """
        _str_func = 'reorder'    
        
        attrs = VALID.listArg(attrs)
        
        for a in attrs:
            assert mc.objExists(node+'.'+a) is True, "|{0}|>> . '{1}.{2}' doesn't exist. Swing and a miss...".format(_str_func,node,a)
            
        _l_user = mc.listAttr(node,userDefined = True)
        _to_move = []
        
        for a in _l_user:
            if not is_hidden(node,a):
                _to_move.append(a)
    
        log.info(_to_move)
        _to_move = lists.reorderListInPlace(_to_move,attrs,direction)
        log.info(_to_move)
        
        #To reorder, we need delete and undo in the order we want
        _d_locks = {}
        _l_relock = []    
        
            
        

def verify_obj(obj = None, mode = 0):
    """
    Given an object selection. Verify selection of first object with a dynParent group and add the subsequent 
    nodes if any as parents.
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "verify_obj"
    _buildD = {}
    
    if not obj:
        _l_context = CONTEXT.get_list('selection')
        
        _len_context = len(_l_context)
        if not _l_context:
            log.error("|{0}| >> Nothing selected.".format(_str_func))                                               
            return False
        
        _buildD['dynChild'] = _l_context[0]
        
        if _len_context > 1:
            _buildD['dynParents'] = _l_context[1:]
    else:
        _buildD['dynChild'] = obj
    
    #>>>Logging what we're gonna do.
    log.info("|{0}| >> Building....".format(_str_func))                                               
    log.info("|{0}| >> dynChild: {1}".format(_str_func,_buildD['dynChild'])) 

    #Initialize group
    _mi_group = cgmRigMeta.cgmDynParentGroup(dynChild = _buildD['dynChild'], dynMode=mode)
    
    #Add parents
    if _buildD.get('dynParents'):    
        log.info("|{0}| >> dynParents...".format(_str_func))         
        for i,p in enumerate(_buildD['dynParents']):
            log.info("|{0}| >> {1} | {2}".format(_str_func,i,p))   
            _mi_group.addDynParent(p)
    
    _mi_group.rebuild()    
    
    #mc.select(_l_context)
    return True    


def get_dict(obj = None):
    """
    Given an object selection. Get a data dict of the dynParentGroup on that object
    
    :parameters
        obj(string): Node or selection based

    :returns
        info(dict)
    """   
    _str_func = "get_dict"
    if not obj:
        _l_context = CONTEXT.get_list('selection')
        if not _l_context:
            log.error("|{0}| >> Nothing selected.".format(_str_func))                                                           
            return False
        obj = _l_context[0]
        
    _d = {}
    
    mGroup = False
    mObj = False
    if ATTR.get_message(obj,'dynParentGroup'):
        log.info("|{0}| >> dynParentGroup found...".format(_str_func))  
        mObj = cgmMeta.validateObjArg(obj)
        mGroup = mObj.dynParentGroup
    elif ATTR.get(obj,'mClass') == 'cgmDynParentGroup':
        log.info("|{0}| >> is dynParentGroup...".format(_str_func))   
        mGroup = cgmMeta.validateObjArg(obj)
        mObj = cgmMeta.validateObjArg(mGroup.dynChild)
    else:
        log.info("|{0}| >> No data found for: {1}".format(_str_func,obj))   
        return False
    
    log.info(cgmGEN._str_hardLine)
    #log.info("|{0}| >> dynChild: {1}".format(_str_func,mObj.mNode))
    #log.info("|{0}| >> dynGroup: {1}".format(_str_func,mGroup.mNode))
    _d['mode'] = mGroup.dynMode
    _d['dynParents'] = mGroup.msgList_get('dynParents')
    _d['dynDrivers'] = mGroup.msgList_get('dynDrivers')
    _d['dynChild'] = mObj
    _d['dynGroup'] = mGroup
    
    _d['aliases'] = []
    for p in _d['dynParents']:
        _d['aliases'].append(ATTR.get(p,'cgmAlias'))
    
    #cgmGEN.log_info_dict(_d,'Data:')
    return _d

def get_state(obj = None):
    """
    Given an object selection. Get a data dict of the dynParentGroup on that object
    
    :parameters
        obj(string): Node or selection based

    :returns
        info(dict)
d_DynParentGroupModeAttrs = {0:['space'],
                             1:['orientTo'],
                             2:['orientTo','follow']}        
        
        
        
    """   
    _str_func = "get_state"
    
    _d = get_dict(obj)
    
    if not _d:
        return False 
    
    _mGroup = _d['dynGroup']
    _mode = _d['mode']
    _dynChild = _d['dynChild']
    
    if _mode == 0:
        return _dynChild.space
    elif _mode == 1:
        return _dynChild.orientTo
    else:
        return _dynChild.orientTo, _dynChild.follow
    
    
    
    
    
    
