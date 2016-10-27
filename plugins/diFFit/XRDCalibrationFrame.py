#!/usr/bin/env pythonw
'''
popup for 2D XRD calibration

'''
import os

import wx
from wxmplot.imagepanel import ImagePanel
#from ImageControlsFrame import ImageToolboxFrame
from larch_plugins.diFFit.ImageControlsFrame import ImageToolboxFrame

import matplotlib.pyplot as plt
import matplotlib.cm as colormap
import numpy as np

HAS_pyFAI = False
try:
    import pyFAI
    import pyFAI.calibrant
    from pyFAI.calibration import Calibration
    HAS_pyFAI = True
except ImportError:
    pass
    
HAS_fabio = False
try:
    import fabio
    HAS_fabio = True
except ImportError:
    pass

IMAGE_AND_PATH = '/Users/koker/Data/XRMMappingCode/Search_and_Match/exampleDIFF.tif'
#IMAGE_AND_PATH = '/Users/margaretkoker/Data/XRMMappingCode/Search_and_Match/exampleDIFF.tif'


class CalibrationPopup(wx.Frame):

    def __init__(self,parent):
    
        wx.Frame.__init__(self, parent, title='Calibration',size=(900,700))
        
        self.parent = parent
        
                
        self.statusbar = self.CreateStatusBar(2,wx.CAPTION )
        
        self.Init()
        self.Show()
        
#        wx.Window.GetEffectiveMinSize
#        wx.GetBestSize(self)

        ## Sets some typical defaults specific to GSE 13-ID procedure
        self.pixel.SetValue('400')     ## binned pixels (2x200um)
        self.EorL.SetValue('19.0')     ## 19.0 keV
        self.Distance.SetValue('0.5')  ## 0.5 m
        self.detslct.SetSelection(22)  ## Perkin detector
        self.calslct.SetSelection(19)  ## CeO2
        
        if self.slctDorP.GetSelection() == 0:
            self.parbox.Hide(self.pixel)

        ## Do not need flags if defaults are set
        #self.FlagCalibrant = False
        #self.FlagDetector  = False
        self.FlagCalibrant = True
        self.FlagDetector  = True
        
        self.AutoContrast()
        
    def Init(self):    

        self.panel = wx.Panel(self)

        self.DirectionsSizer()
        self.MainSizer()
        self.OKsizer()

        framebox = wx.BoxSizer(wx.VERTICAL)
        framebox.Add(self.dirbox,  flag=wx.ALL|wx.EXPAND, border=10)
        framebox.Add(self.mainbox, flag=wx.ALL|wx.EXPAND, border=10)
        framebox.Add(self.okbox,   flag=wx.ALL|wx.ALIGN_RIGHT, border=10)
        
        ###########################
        ## Pack all together in self.panel
        self.panel.SetSizer(framebox) 

        self.FindWindowById(wx.ID_OK).Disable()


        ###########################
        ## Set default information
        self.stepno = 0
        self.checkRANGE()
        self.showDirection()

    def DirectionsSizer(self):

        ###########################
        ## Directions
        dirbx = wx.StaticBox(self.panel,label='DIRECTIONS', size=(100, 50))
        self.dirbox = wx.StaticBoxSizer(dirbx,wx.VERTICAL)
        
        hbox_direct = wx.BoxSizer(wx.HORIZONTAL)
        self.followdir = wx.StaticText(self.panel,label='')

        #hbox_direct.Add(self.txt_shp, flag=wx.RIGHT, border=8)
        hbox_direct.Add(self.followdir, flag=wx.EXPAND, border=8)
       
        self.dirbox.Add(hbox_direct, flag=wx.ALL|wx.EXPAND, border=10)
    
        hbox_next = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_prev = wx.Button(self.panel,label='PREVIOUS')
        self.btn_next = wx.Button(self.panel,label='NEXT')

        self.btn_prev.Bind(wx.EVT_BUTTON,self.onPREVIOUS)
        self.btn_next.Bind(wx.EVT_BUTTON,self.onNEXT)

        hbox_next.Add(self.btn_prev, flag=wx.ALL, border=8)
        hbox_next.Add((-1, 100))
        hbox_next.Add(self.btn_next, flag=wx.ALIGN_RIGHT|wx.ALL, border=8)
       
        self.dirbox.Add(hbox_next, flag=wx.ALL|wx.EXPAND, border=10)

    def MainSizer(self):
    
        self.mainbox = wx.BoxSizer(wx.VERTICAL)

        ###########################
        ## -----> Main Panel
        hbox_main = wx.BoxSizer(wx.HORIZONTAL)
        
        self.ImageSizer()
        self.ParameterSizer()

        hbox_main.Add(self.imagebox,proportion=1,flag=wx.ALL|wx.EXPAND, border=10)
        hbox_main.Add(self.parbox,   flag=wx.ALL|wx.EXPAND, border=10)
        
        self.mainbox .Add(hbox_main, flag=wx.ALL|wx.EXPAND, border=10)

    def ParameterSizer(self):
        '''
        This is where the parameters will be.
        '''
        
        self.parbox = wx.BoxSizer(wx.VERTICAL)
        
        ###########################
        ## Calibration starting values


        ###################################
        ###################################        
        ###################################
        ## Establish lists from pyFAI        
        clbrnts = [] #['None']
        self.dets = [] #['None']
        for key,value in pyFAI.detectors.ALL_DETECTORS.items():
            self.dets.append(key)
        for key,value in pyFAI.calibrant.ALL_CALIBRANTS.items():
            clbrnts.append(key)    
        self.CaliPath = None

        #####
        ## Calibration Image selection        
        hbox_cal1 = wx.BoxSizer(wx.HORIZONTAL)
        caliImg     = wx.StaticText(self.panel, label='Calibration Image:' )
        self.calFil = wx.TextCtrl(self.panel, size=(190, -1))
        fileBtn1    = wx.Button(self.panel, label='Browse...')
        
        fileBtn1.Bind(wx.EVT_BUTTON,   self.onBROWSE)
        
        hbox_cal1.Add(caliImg,     flag=wx.RIGHT,  border=8)
        hbox_cal1.Add(self.calFil, flag=wx.RIGHT,  border=8)
        hbox_cal1.Add(fileBtn1,    flag=wx.RIGHT,  border=8)
        self.parbox.Add(hbox_cal1, flag=wx.BOTTOM, border=8)

        #####
        ## Calibrant selection
        hbox_cal2 = wx.BoxSizer(wx.HORIZONTAL)
        CalLbl = wx.StaticText(self.panel, label='Calibrant:')# ,style=LEFT) 
        self.calslct = wx.Choice(self.panel,choices=clbrnts)

        self.calslct.Bind(wx.EVT_CHOICE,  self.onCalSel)

        hbox_cal2.Add(CalLbl,       flag=wx.RIGHT,  border=8)
        hbox_cal2.Add(self.calslct, flag=wx.RIGHT,  border=8)
        self.parbox.Add(hbox_cal2,  flag=wx.BOTTOM, border=8)        

        #####
        ## Detector selection
        hbox_cal3 = wx.BoxSizer(wx.HORIZONTAL)
        self.slctDorP = wx.Choice(self.panel,choices=['Detector','Pixel size (um)'])
        self.detslct  = wx.Choice(self.panel, choices=self.dets)
        self.pixel    = wx.TextCtrl(self.panel, size=(140, -1))

        self.detslct.Bind(wx.EVT_CHOICE,  self.onDetSel)
        self.slctDorP.Bind(wx.EVT_CHOICE, self.onDorPSel)

        hbox_cal3.Add(self.slctDorP, flag=wx.RIGHT,  border=8)
        hbox_cal3.Add(self.detslct,  flag=wx.RIGHT,  border=8)
        hbox_cal3.Add(self.pixel,    flag=wx.RIGHT,  border=8)        
        self.parbox.Add(hbox_cal3,   flag=wx.BOTTOM, border=8)

        #####
        ## Energy or Wavelength
        hbox_cal4 = wx.BoxSizer(wx.HORIZONTAL)
        self.slctEorL = wx.Choice(self.panel,choices=['Energy (keV)','Wavelength (A)'])
        self.EorL = wx.TextCtrl(self.panel, size=(140, -1))
 
        self.slctEorL.Bind(wx.EVT_CHOICE, self.onEorLSel)
 
        hbox_cal4.Add(self.slctEorL, flag=wx.RIGHT,  border=8)
        hbox_cal4.Add(self.EorL,     flag=wx.RIGHT,  border=8)
        self.parbox.Add(hbox_cal4,   flag=wx.BOTTOM, border=8) 

        ## Refine label
        RefLbl = wx.StaticText(self.panel, label='To be refined...')# ,style=LEFT)

        self.parbox.Add(RefLbl, flag=wx.BOTTOM, border=8) 

        ## Distance
        hbox_cal6 = wx.BoxSizer(wx.HORIZONTAL)
        self.Distance = wx.TextCtrl(self.panel, size=(140, -1))
        DstLbl = wx.StaticText(self.panel, label='Distance (m):')# ,style=LEFT)
        
        hbox_cal6.Add(self.Distance, flag=wx.RIGHT,  border=8)
        hbox_cal6.Add(DstLbl,        flag=wx.RIGHT,  border=8)
        self.parbox.Add(hbox_cal6,   flag=wx.BOTTOM, border=8) 


    def onCalSel(self,event):
        #if self.calslct.GetSelection() == 0:
        #    self.FlagCalibrant = False
        #else:
        #    self.FlagCalibrant = True
        self.checkOK()

    def onDetSel(self,event):
        #if self.detslct.GetSelection() == 0:
        #    self.FlagDetector = False
        #else:
        #    self.FlagDetector = True
        self.checkOK()

    def onCheckOK(self,event):
        self.checkOK()

    def checkOK(self):
        if self.FlagCalibrant and self.CaliPath is not None:
            if self.slctDorP.GetSelection() == 1:
                self.FindWindowById(wx.ID_OK).Enable()
            else:
                if self.FlagDetector:
                    self.FindWindowById(wx.ID_OK).Enable()
                else:
                    self.FindWindowById(wx.ID_OK).Disable()
        else:
            self.FindWindowById(wx.ID_OK).Disable()

    def onEorLSel(self,event): 
        hc = constants.value(u'Planck constant in eV s') * \
                       constants.value(u'speed of light in vacuum') * 1e-3 ## units: keV-m
        if self.slctEorL.GetSelection() == 1:
            energy = float(self.EorL.GetValue()) ## units keV
            wavelength = hc/(energy)*1e10 ## units: A
            self.EorL.SetValue(str(wavelength))
        else:
            wavelength = float(self.EorL.GetValue())*1e-10 ## units: m
            energy = hc/(wavelength) ## units: keV
            self.EorL.SetValue(str(energy))
            
        self.checkOK()

    def onDorPSel(self,event): 
        if self.slctDorP.GetSelection() == 0:
            self.parbox.Hide(self.pixel)
            self.parbox.Show(self.detslct)
        else:
            self.parbox.Hide(self.detslct)
            self.parbox.Show(self.pixel)

        self.checkOK()


    def onBROWSE(self, event): 
        wildcards = 'XRD image (*.edf,*.tif,*.tiff)|*.tif;*.tiff;*.edf|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, message='Choose XRD calibration file',
                           defaultDir=os.getcwd(),
                           wildcard=wildcards, style=wx.FD_OPEN)

        path, read = None, False
        if dlg.ShowModal() == wx.ID_OK:
            read = True
            path = dlg.GetPath().replace('\\', '/')
        dlg.Destroy()
        
        if read:
            self.calFil.Clear()
            self.calFil.SetValue(os.path.split(path)[-1])
            self.CaliPath = path
            self.checkOK()

    def ImageSizer(self):
        '''
        Image Panel
        '''
        self.imagebox = wx.BoxSizer(wx.VERTICAL)
        
        self.plot2Dimage()
        
        self.btn_image = wx.Button(self.panel,label='IMAGE TOOLS')

        self.btn_image.Bind(wx.EVT_BUTTON,self.onImageTools)

        self.imagebox.Add(self.plot2Dimg,proportion=1,flag=wx.ALL|wx.EXPAND, border=10)
        self.imagebox.Add(self.btn_image, flag=wx.ALL, border=10) 

    def OKsizer(self):
        ###########################
        ## OK - CANCEL
        self.okbox = wx.BoxSizer(wx.HORIZONTAL)
        
        okBtn  = wx.Button(self.panel, wx.ID_OK     )
        canBtn = wx.Button(self.panel, wx.ID_CANCEL )

        self.okbox.Add(canBtn,  flag=wx.RIGHT, border=5)
        self.okbox.Add(okBtn,   flag=wx.RIGHT, border=5)
     
    def write_message(self, s, panel=0):
        """write a message to the Status Bar"""
        self.SetStatusText(s, panel)

    def onImageTools(self,event):
        
        self.toolbox = ImageToolboxFrame(self.plot2Dimg,self.raw_img)

    def plot2Dimage(self):
    
        self.plot2Dimg = ImagePanel(self.panel,size=(300, 300))
        self.plot2Dimg.messenger = self.write_message
        
        ## Image opening eventually needs to be its own function
        ## mkak 2016.10.20
        if self.parent == None:
            self.raw_img = fabio.open(IMAGE_AND_PATH).data
        else:
            self.raw_img = self.parent.raw_img

        self.plot2Dimg.display(self.raw_img)       

        self.plot2Dimg.redraw()

    def AutoContrast(self):
    
        self.minINT = int(np.min(self.raw_img))
        self.maxINT = int(np.max(self.raw_img)/15) # /15 scales image to viewable 
        if self.maxINT == self.minINT:
            self.minINT = self.minINT-50
            self.maxINT = self.minINT+100

        self.minCURRENT = self.minINT
        self.maxCURRENT = self.maxINT
        if self.maxCURRENT > self.maxINT:
            self.maxCURRENT = self.maxINT
        
        self.plot2Dimg.conf.auto_intensity = False        
        self.plot2Dimg.conf.int_lo['int'] = self.minCURRENT
        self.plot2Dimg.conf.int_hi['int'] = self.maxCURRENT
        
        ## vertical flip default
        self.plot2Dimg.conf.flip_ud = True
        self.plot2Dimg.conf.flip_lr = False 
       
        self.plot2Dimg.redraw()   
        
    def checkRANGE(self):
    
        if self.stepno <= 0:
            self.stepno = 0
            self.btn_prev.Disable()
        else:
            self.btn_prev.Enable()

        if self.stepno >= 8:
            self.stepno = 8
            self.btn_next.Disable()
        else:
            self.btn_next.Enable()

    def onNEXT(self, event):
        self.stepno = self.stepno + 1
        self.checkRANGE()
        self.showDirection()
    
    def onPREVIOUS(self,event):
        self.stepno = self.stepno - 1
        self.checkRANGE()
        self.showDirection()
    
    def showDirection(self):
        
        dirsteps = ['Enter parameters into the fields below.',
                    'Select point(s) on the first ring.',
                    'Select point(s) on the second ring.',
                    'Select point(s) on the third ring.',
                    'Select point(s) on the fourth ring.',
                    'Select point(s) on the fifth ring.',
                    'Select point(s) on the sixth ring.',
                    'Check preliminary calibration. Continue for final refinement.',
                    'Refinement complete.' ]
                    
        self.followdir.SetLabel(dirsteps[self.stepno])

class diFFit_XRDcal(wx.App):
    def __init__(self):
        wx.App.__init__(self)

    def run(self):
        self.MainLoop()

    def createApp(self):
        frame = CalibrationPopup(None)
        frame.Show()
        self.SetTopWindow(frame)

    def OnInit(self):
        self.createApp()
        return True

def registerLarchPlugin():
    return ('_diFFit', {})

class DebugViewer(diFFit_XRDcal):
    def __init__(self, **kws):
        diFFit_XRDcal.__init__(self, **kws)

    def OnInit(self):
        #self.Init()
        self.createApp()
        #self.ShowInspectionTool()
        return True

if __name__ == '__main__':
    diFFit_XRDcal().run()
