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

# def getKernValue(layer1, layer2):
# 	if Glyphs.buildNumber > 3000:
# 		return layer1.nextKerningForLayer_direction_(layer2, LTR)
# 	else:
# 		return layer1.rightKerningForLayer_(layer2)


class NineBoxView(NSView):

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
		if glyph is None:
			glyph = font.glyphs['.notdef']
		return glyph

	def drawRect_(self, rect):
		self.wrapper._backColour.set() # 填充背景色
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
			transform.translateXBy_yBy_(tab*upm/s+s*upm/s, (h-2*s)*upm/s) # 移動位置(tab*原始大小/顯示大小, (視窗高度-顯示大小)*原始大小/顯示大小)
			previewPath.transformUsingAffineTransform_( transform )

			## 填滿路徑
			#------------------------
			NSColor.blackColor().set() # 字符顏色：黑色
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
					kernValue = 0
					# kerning check
					#------------------------------

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
				transform.translateXBy_yBy_(tab*upm/s+s*upm/s, (h-s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_(tab*upm/s+2*s*upm/s, (h-s)*upm/s)
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
				transform.translateXBy_yBy_(tab*upm/s+2*s*upm/s, (h-2*s)*upm/s)
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
				transform.translateXBy_yBy_(tab*upm/s+s*upm/s, (h-3*s)*upm/s)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill() # 填滿顏色
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
				#------------------------------
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_(tab*upm/s+2*s*upm/s, (h-3*s)*upm/s)
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
		self._glyphsList = []
		self._foreColour = None
		self._backColour = None
		self._instanceIndex = 0
		self._setupView(self.nsGlyphPreviewClass, posSize)
		self._nsObject.wrapper = self

	def redraw(self):
		self._nsObject.setNeedsDisplay_(True)


class ____PluginClassName____(GeneralPlugin):
	@objc.python_method # 設定外掛初始值方法
	def settings(self): # 預設選項
		self.name = Glyphs.localize({ # 外掛名稱
		'en': u'Nine Box View',
		'zh-Hant': u'九宮格預覽'
		})
		if Glyphs.versionNumber < 3: # Glyphs版本 3
			Glyphs.registerDefaults({
			"com.YinTzuYuan.NineBoxView.foreColour": [0, 0, 0, 1], # 預設前景色 黑色
			"com.YinTzuYuan.NineBoxView.backColour": [1, 1, 1, 1] # 預設背景色 白色
			})
		else: # Glyphs版本 2
			Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.foreColour"] = NSColor.blackColor()
			Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.backColour"] = NSColor.whiteColor()

	def showWindow_(self, sender): # 開啟視窗動作
		try:
			edY = 22
			clX = 22
			spX = 8
			spY = 8
			btnY = 17
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
			self.w.edit = EditText( (spX, spY, (-spX*3-clX*2)-80, edY), text="東", callback=self.textChanged_)
			self.w.edit.getNSTextField().setNeedsLayout_(True)
			defaultWhite = NSColor.colorWithCalibratedRed_green_blue_alpha_(1,1,1,1)
			defaultBlack = NSColor.colorWithCalibratedRed_green_blue_alpha_(0,0,0,1)
			self.w.foreColour = ColorWell((-spX*2-clX*2, spY, clX, edY), color=defaultBlack, callback=self.uiChange_)
			self.w.backColour = ColorWell((-spX-clX, spY, clX, edY), color=defaultWhite, callback=self.uiChange_)
			# self.w.refresh = Button((-spX-138, spY, 80, edY), "Refresh", callback=self.textChanged_)
			self.w.instancePopup = PopUpButton((spX, spY*2+edY, -spX, edY), insList, callback=self.changeInstance_)
			self.w.preview = TheView((0, spX*3+edY*2, -0, -0))
			self.w.preview._foreColour = defaultBlack
			self.w.preview._backColour = defaultWhite
			self.w.preview.instances = {}
			self.loadPrefs()
			self.w.open()
			self.uiChange_(None)
			self.changeInstance_(self.w.instancePopup)
			self.textChanged_(self.w.edit)
			Glyphs.addCallback(self.changeInstance_, UPDATEINTERFACE)  # will be called on every change to the interface
			Glyphs.addCallback(self.changeDocument_, DOCUMENTACTIVATED)
		except:
			print(traceback.format_exc())

	@objc.python_method # 載入預設值方法
	def loadPrefs(self):
		try:
			editText = Glyphs.defaults["com.YinTzuYuan.NineBoxView.edit"]
			if editText:
				self.w.edit.set(editText)
			if Glyphs.versionNumber < 3: # Glyphs版本 3
				R_f, G_f, B_f, A_f = Glyphs.defaults["com.YinTzuYuan.NineBoxView.foreColour"]
				self.w.foreColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_f), float(G_f), float(B_f), float(A_f)))
				R_b, G_b, B_b, A_b = Glyphs.defaults["com.YinTzuYuan.NineBoxView.backColour"]
				self.w.backColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_b), float(G_b), float(B_b), float(A_b)))
			else: # Glyphs版本 2
				f = Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.foreColour"]
				self.w.foreColour.set(f)
				b = Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.backColour"]
				self.w.backColour.set(b)
		except:
			print(traceback.format_exc())

	@objc.python_method # 修改輸入設定方法
	def makeList(self, string):
		try:
			newList = [c for c in string.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')]
			# print(newList)
			if newList:
				filtered = []
				skip = 0
				for i, c in enumerate(newList):
					if i < skip:
						continue
					if surrogate_start.match(c):
						codepoint = surrogate_pairs.findall(c+newList[i+1])[0]
						# skip over emoji skin tone modifiers
						if codepoint in [u'🏻', u'🏼', u'🏽', u'🏾', u'🏿']:
							continue
						filtered.append(codepoint)
					elif surrogate_start.match(newList[i-1]):
						continue
					elif emoji_variation_selector.match(newList[i]):
						continue
					else:
						if c == "/":
							if i+1 > len(newList)-1:
								filtered.append(c)
								continue
							j = i
							longest = ''.join(newList[i+1:])
							while True:
								if Glyphs.font.glyphs[longest]:
									filtered.append(longest)
									skip = j + len(longest) + 1
									break
								longest = longest[:-1]
								if len(longest) <= 1:
									break
						else:
							filtered.append(c)
				if filtered:
					return filtered
		except:
			print("Waterfall Error (makeList)", traceback.format_exc())
			Glyphs.showMacroWindow()

	def textChanged_(self, sender): # 修改輸入文本
		self.w.preview._glyphsList = self.makeList(self.w.edit.get())
		self.w.preview.redraw()

	def uiChange_(self, sender): # 修改顏色
		try:
			NSC_f = self.w.foreColour.get()
			NSC_b = self.w.backColour.get()
			self.w.preview._foreColour = NSC_f
			self.w.preview._backColour = NSC_b
			self.w.preview.redraw()
			try:
				if Glyphs.versionNumber < 3:
					R_f, G_f, B_f, A_f = NSC_f.redComponent(), NSC_f.greenComponent(), NSC_f.blueComponent(), NSC_f.alphaComponent()
					R_b, G_b, B_b, A_b = NSC_b.redComponent(), NSC_b.greenComponent(), NSC_b.blueComponent(), NSC_b.alphaComponent()
					Glyphs.defaults["com.YinTzuYuan.NineBoxView.foreColour"] = (R_f, G_f, B_f, A_f)
					Glyphs.defaults["com.YinTzuYuan.NineBoxView.backColour"] = (R_b, G_b, B_b, A_b)
				else:
					Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.foreColour"] = NSC_f
					Glyphs.colorDefaults["com.YinTzuYuan.NineBoxView.backColour"] = NSC_b
			except:
				print(traceback.format_exc())
		except:
			print(traceback.format_exc())

	def changeDocument_(self, sender): # 修改文件？
		"""
		Update when current document changes (choosing another open Font)
		"""
		self.w.preview.instances = {}
		# self.w.instancePopup.setItems([])
		self.w.preview._instanceIndex = 0
		self.w.preview.redraw()
		self.changeInstance_(self.w.instancePopup)
		(None)

	def changeInstance_(self, sender): # 修改主板/匯出實體
		currentIndex = self.w.instancePopup.get()
		insList = [i.name for i in Glyphs.font.instances]
		insList.insert(0, 'Current Master')
		if insList != self.w.instancePopup.getItems():
			self.w.instancePopup.setItems(insList)
			currentIndex = 0
		self.w.preview._instanceIndex = currentIndex
		self.w.preview.redraw()

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

	## 以下程式碼務必保留置底
	#------------------------------
	@objc.python_method # 關閉外掛行為方法
	def __del__(self):
		Glyphs.removeCallback(self.changeInstance_, UPDATEINTERFACE)
		Glyphs.removeCallback(self.changeDocument_, DOCUMENTACTIVATED)

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
