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


class NineBoxView(NSView):

	@objc.python_method
	def drawRect_(self, rect):
		self.wrapper._backColour.set() # 設定背景色
		NSBezierPath.fillRect_(rect)

		lineSpace = 8
		tab = 30
		w = NSWidth(self.frame())
		h = NSHeight(self.frame())
		glyphNames = self.wrapper._glyphsList

		fullPath = NSBezierPath.alloc().init()
		self.wrapper._foreColour.set() # 設定前景色

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
					if i + 1 < len(glyphNames): # 如果字數大於一
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
	nsGlyphPreviewClass = NineBoxView # NSView的class檔名

	def __init__(self, posSize):
		self._glyphsList = [] # 參考字導出到GUI
		self._foreColour = None # 前景色導出到GUI
		self._backColour = None # 背景色導出到GUI
		self._setupView(self.nsGlyphPreviewClass, posSize)
		self._nsObject.wrapper = self

	def redraw(self):
		self._nsObject.setNeedsDisplay_(True)


class ____PluginClassName____(GeneralPlugin):
	@objc.python_method # 設定外掛初始值方法
	def settings(self): # 預設選項
		self.name = Glyphs.localize({ # 外掛名稱
		'en': u'Nine Box View',
		'zh-Hant': u'九宮格預覽',
		'zh-Hans': u'九宫格预览',
		'jp': u'九宮格プレビュー',
		'kr': u'구궁격 미리보기'
		})

	@objc.python_method
	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow)
		Glyphs.menu[WINDOW_MENU].append(newMenuItem)

	@objc.python_method
	def showWindow(self, sender): # 開啟視窗執行的指令
		try:
			edY = 22 # 行高
			clX = 44 # 明暗模式按鈕寬度
			spX = 8
			spY = 8
			self.windowWidth = 300
			self.windowHeight = 240
			self.thisfont = Glyphs.font
			self.w = FloatingWindow((self.windowWidth, self.windowWidth), self.name,
				autosaveName = "com.YinTzuYuan.NineBoxView.mainwindow",
				minSize=(self.windowWidth, self.windowWidth + 20))
			self.w.edit = EditText( (spX, spY, (-spX*3-clX)-80, edY), text="東", callback=self.textChanged_)
			self.w.uiMode = Button((-spX-clX, spY, clX, edY), "◐", callback=self.uiChange_) # 明暗模式切換
			self.w.preview = TheView((0, spX*3+edY, -0, -0)) # 預覽畫面
			self.w.preview.foreColour = NSColor.blackColor() # 預覽畫面前景色
			self.w.preview.backColour = NSColor.whiteColor() # 預覽畫面背景色
			self.LoadPreferences() # 載入偏好設定
			self.w.open()
			self.textChanged_(self.w.edit)
			self.uiChange_(None)
			# Glyphs.addCallback(self.changeInstance_, UPDATEINTERFACE)  # will be called on every change to the interface
			# Glyphs.addCallback(self.changeDocument_, DOCUMENTACTIVATED)
		except:
			print(traceback.format_exc())

	def SavePreferences(self, sender=None): # 儲存偏好設定
		try:
			# 將當前設定值存入偏好設定
			Glyphs.defaults["com.YinTzuYuan.NineBoxView.mainwindow.edit"] = self.w.edit.get()
			Glyphs.defaults["com.YinTzuYuan.NineBoxView.mainwindow.uiMode"] = self.w.preview.foreColour.get()

			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	@objc.python_method
	def LoadPreferences(self): # 載入偏好設定
		try:
			# register defaults:
			Glyphs.registerDefault("com.YinTzuYuan.NineBoxView.edit", "東")
			Glyphs.registerDefault("com.YinTzuYuan.NineBoxView.uiMode", "Light")

			# load previously written prefs:
			self.w.edit.set(Glyphs.defaults["com.YinTzuYuan.NineBoxView.edit"])
			self.w.preview.foreColour.set(Glyphs.defaults["com.YinTzuYuan.NineBoxView.uiMode"])
			return True
		except:
			import traceback
			print(traceback.format_exc())
			return False

	@objc.python_method # 修改輸入設定方法
	def textChanged_(self, sender): # 修改輸入文本
		self.w.preview._glyphsList = self.w.edit.get()
		self.w.preview.redraw()

	def uiChange_(self, sender): # 修改顏色
		try:
			if self.w.preview.foreColour == NSColor.blackColor():
				uiMode_Dark()
			else:
				uiMode_Light()
			self.w.preview.redraw() # 重新繪製預覽畫面
		except:
			print(traceback.format_exc())

	@objc.python_method # 明暗模式顏色設定
	def uiMode_Light(self): # 亮色模式
		self.w.preview.foreColour = NSColor.blackColor()
		self.w.preview.backColour = NSColor.whiteColor()

	def uiMode_Dark(self): # 暗色模式
		self.w.preview.foreColour = NSColor.whiteColor()
		self.w.preview.backColour = NSColor.blackColor()

	@objc.python_method # 關閉外掛行為方法
	# def __del__(self):
		# Glyphs.removeCallback(self.changeInstance_, UPDATEINTERFACE)
		# Glyphs.removeCallback(self.changeDocument_, DOCUMENTACTIVATED)

	## 以下程式碼務必保留置底
	#------------------------------

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
