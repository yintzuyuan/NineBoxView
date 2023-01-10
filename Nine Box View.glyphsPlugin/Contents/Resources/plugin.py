# encoding: utf-8

###########################################################################################################
#
#
#	General Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


#https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

from __future__ import print_function, unicode_literals
from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *
from AppKit import NSAffineTransform, NSRectFill, NSView, NSNoBorder, NSColor, NSBezierPath, NSMutableParagraphStyle, NSParagraphStyleAttributeName, NSFloatingWindowLevel
from Foundation import NSWidth, NSHeight, NSMidX, NSMidY
import traceback
import re, objc

surrogate_pairs = re.compile(u'[\ud800-\udbff][\udc00-\udfff]', re.UNICODE)
surrogate_start = re.compile(u'[\ud800-\udbff]', re.UNICODE)
emoji_variation_selector = re.compile(u'[\ufe00-\ufe0f]', re.UNICODE)


class Viwer(NSView):

	@objc.python_method
	def glyphForName(self, name, font):
		if len(name) == 1:
			glyph_unicode = "%.4X" % ord(name)
		else:
			glyph_unicode = name.encode('unicode-escape')
		glyph = font.glyphs[glyph_unicode]
		if glyph is None:
			if len(glyph_unicode) == 10:
				glyph_unicode = glyph_unicode[5:].upper()
			glyph = f.glyphForUnicode_(glyph_unicode)
		# if glyph is None:
		# 	glyph = font.glyphs['.notdef']
		return glyph

	def drawRect_(self, rect):
		self.wrapper.backColour.set() # 填充背景色
		NSBezierPath.fillRect_(rect)

		lineSpace = 8
		tab = 30
		w = NSWidth(self.frame())
		h = NSHeight(self.frame())
		glyphNames = self.wrapper._glyphsList
		insIndex = self.wrapper._instanceIndex
		if insIndex == 0:
			font = Glyphs.font
			m = font.selectedFontMaster
		else:
			instance = Glyphs.font.instances[insIndex-1]
			font = self.wrapper.instances.get(instance.name)
			if font is None:
				font = instance.interpolatedFont
				self.wrapper.instances[instance.name] = font
			m = font.masters[0]
		fullPath = NSBezierPath.alloc().init()
		advance = 0
		self.wrapper.foreColour.set() # 設定前景色

		## 主要字
		#------------------------
		if Glyphs.font is None:
			return

		if not Glyphs.font.selectedLayers:
			return

		thisGlyph = None
		try:
			thisGlyph = Glyphs.font.selectedLayers[0]
		except:
			print(traceback.format_exc())

		if thisGlyph is None:
			return

		try:
			sSum = 0
			upm = float(font.upm)
			for i, s in enumerate([120]): # 顯示字型大小
				sSum += s # 顯示大小+(顯示大小/4)
			previewPath = thisGlyph.completeBezierPath

			transform = NSAffineTransform.transform()
			transform.scaleBy_(s/upm) # 縮放尺寸(顯示大小/原始大小)
			transform.translateXBy_yBy_((tab+s)*upm/s, (h-2*s)*upm/s) # 移動位置(tab*原始大小/顯示大小, (視窗高度-顯示大小)*原始大小/顯示大小)
			previewPath.transformUsingAffineTransform_( transform )

			## 填滿路徑
			#------------------------
			previewPath.fill()

		except:
			print(traceback.format_exc())

		## 參考字
		#------------------------
		try: # 選擇字符
			for i, glyphName in enumerate(glyphNames):

				glyph = self.glyphForName(glyphName, font)
				if glyph:
					layer = glyph.layers[m.id]

					layerPath = layer.completeBezierPath
					# kerning check
					if i + 1 < len(glyphNames): # 如果字數小於一
						nextGlyphName = glyphNames[i + 1]
						nextGlyph = self.glyphForName(nextGlyphName, font)
						if nextGlyph:
							nextLayer = nextGlyph.layers[m.id]
							if nextLayer:
								kernValue = getKernValue(layer, nextLayer)
								if kernValue > 10000:
									kernValue = 0

					fullPath.appendBezierPath_(layerPath)
		except:
			print(traceback.format_exc())

		if fullPath is None: # 判斷如果沒有找到路徑就返回
			return

		try: # 顯示位置
			sSum = 0
			upm = float(font.upm)
			for i, s in enumerate([120]): # 顯示字型大小
				sSum += s # 顯示大小+顯示大小

				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm) # 縮放尺寸(顯示大小/原始大小)
				transform.translateXBy_yBy_(tab*upm/s, (h-s)*upm/s) # 移動位置(tab*原始大小/顯示大小, (視窗高度-顯示大小-sSum)*原始大小/顯示大小)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_((tab+s)*upm/s, (h-s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_((tab+2*s)*upm/s, (h-s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_(tab*upm/s, (h-2*s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_((tab+2*s)*upm/s, (h-2*s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm) # 縮放尺寸(顯示大小/原始大小)
				transform.translateXBy_yBy_(tab*upm/s, (h-3*s)*upm/s) # 移動位置(tab*原始大小/顯示大小, (視窗高度-顯示大小-sSum)*原始大小/顯示大小)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_((tab+s)*upm/s, (h-3*s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_((tab+2*s)*upm/s, (h-3*s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
		except:
			print(traceback.format_exc())


class TheView(VanillaBaseObject):
	nsGlyphPreviewClass = Viwer # NSView的class檔名

	def __init__(self, posSize):
		self._glyphsList = []
		self.foreColour = None
		self.backColour = None
		self._instanceIndex = 0
		self._setupView(self.nsGlyphPreviewClass, posSize)
		self._nsObject.wrapper = self

	def redraw(self):
		self._nsObject.setNeedsDisplay_(True)


class NineBoxView(GeneralPlugin):
	@objc.python_method # 設定外掛初始值方法
	def settings(self): # 預設選項
		self.name = Glyphs.localize({ # 外掛名稱
		'en': u'Nine Box View',
		'zh-Hant': u'九宮格預覽',
		'zh-Hans': u'九宫格预览',
		'ja': u'九宮格プレビュー',
		'ko': u'구궁격 미리보기'
		})

	def showWindow_(self, sender): # 開啟視窗動作
		try:
			edY = 22 # 行高
			clX = 44 # 明暗模式按鈕寬度
			spX = 8
			spY = 8
			# btnY = 17
			self.windowWidth = 300
			self.windowHeight = 240
			self.currentDocument = Glyphs.currentDocument
			self.thisfont = Glyphs.font
			# self.thisfont = GlyphsApp.currentFont()
			self.w = FloatingWindow((self.windowWidth, self.windowWidth), self.name,
				autosaveName = "com.YinTzuYuan.NineBoxView.mainwindow",
				minSize=(self.windowWidth, self.windowWidth + 20))
			self.w.bind("close", self.windowClosed_)
			insList = [i.name for i in Glyphs.font.instances]
			insList.insert(0, 'Current Master')
			self.w.edit = EditText( (spX, spY, (-spX*3-clX)-80, edY), text="東", callback=self.textChanged_)
			self.w.edit.getNSTextField().setNeedsLayout_(True)
			self.w.uiChangeButton = Button((-spX-clX, spY, clX, edY), "◐", callback=self.uiChange_) # 明暗模式切換
			self.w.preview = TheView((0, spX*3+edY, -0, -0)) # 預覽畫面
			self.w.preview.foreColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(0,0,0,1) # 預覽畫面前景色
			self.w.preview.backColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(1,1,1,1) # 預覽畫面背景色
			self.w.preview.instances = {}
			self.LoadPreferences()
			self.w.open()
			self.uiChange_(None)
			self.changeInstance_([i.name for i in Glyphs.font.instances])
			self.textChanged_(self.w.edit)
			Glyphs.addCallback(self.changeInstance_, UPDATEINTERFACE)  # will be called on every change to the interface
			Glyphs.addCallback(self.changeDocument_, DOCUMENTACTIVATED)
		except:
			print(traceback.format_exc())

	@objc.python_method # 載入儲存值
	def LoadPreferences(self):
		try:
			# 預設值：
			Glyphs.registerDefault("com.YinTzuYuan.NineBoxView.edit", "東")
			Glyphs.registerDefault("com.YinTzuYuan.NineBoxView.uiChangeButton", "◐")

			# 載入修改後的偏好設定：
			self.w.edit.set(Glyphs.defaults["com.YinTzuYuan.NineBoxView.edit"])
			self.w.uiChangeButton.setTitle(Glyphs.defaults["com.YinTzuYuan.NineBoxView.uiChangeButton"])
			self.uiChange_(self.w.uiChangeButton)
		except:
			print(traceback.format_exc())

	@objc.python_method # 修改輸入設定方法
	def textChanged_(self, sender): # 修改輸入文本
		self.w.preview._glyphsList = self.w.edit.get()
		self.w.preview.redraw()

	def uiChange_(self, sender): # 修改顏色
		try:
			 # 取得當前模式名稱
			current_Mode = self.w.uiChangeButton.getTitle()

		    # 判斷當前模式是否為明亮模式
			is_Light_Mode = (current_Mode == "◐")

		    # 依據當前的模式設定新的模式
			if is_Light_Mode: # 如果是明亮模式
				self.w.uiChangeButton.setTitle("◑") # 切換為黑暗模式
				self.w.preview.foreColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(1,1,1,1)
				self.w.preview.backColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(0,0,0,1)
			else: # 否則
				self.w.uiChangeButton.setTitle("◐") # 切換為明亮模式
				self.w.preview.foreColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(0,0,0,1)
				self.w.preview.backColour = NSColor.colorWithCalibratedRed_green_blue_alpha_(1,1,1,1)

			self.w.preview.redraw() # 重新繪製預覽畫面
		except:
			print(traceback.format_exc())

	def changeDocument_(self, sender): # 修改文件？
		"""
		Update when current document changes (choosing another open Font)
		"""
		self.w.preview.instances = {}
		self.w.preview._instanceIndex = 0
		self.w.preview.redraw()
		self.changeInstance_([i.name for i in Glyphs.font.instances])
		(None)

	def changeInstance_(self, sender): # 修改主板/匯出實體
		currentIndex = 0 # 當前索引被賦值為零
		insList = [i.name for i in Glyphs.font.instances] # 主板選單被賦值為當前主板
		insList.insert(0, 'Current Master') # 主板選單變為當前主板
		self.w.preview._instanceIndex = currentIndex # 預覽畫面被賦值為當前索引
		self.w.preview.redraw() # 重新繪製預覽畫面

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow_)
		Glyphs.menu[WINDOW_MENU].append(newMenuItem)

	def setWindowController_(self, windowController):
		try:
			self._windowController = windowController
		except:
			self.logError(traceback.format_exc())

	def windowClosed_(self, sender):
		Glyphs.defaults["com.YinTzuYuan.NineBoxView.edit"] = self.w.edit.get()
		Glyphs.defaults["com.YinTzuYuan.NineBoxView.uiChangeButton"] = self.w.uiChangeButton.getTitle()

	## 以下程式碼務必保留置底
	#------------------------------
	@objc.python_method # 關閉外掛行為方法
	def __del__(self):
		Glyphs.removeCallback(self.changeInstance_, UPDATEINTERFACE)
		Glyphs.removeCallback(self.changeDocument_, DOCUMENTACTIVATED)

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
