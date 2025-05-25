# encoding: utf-8

###########################################################################################################
#
#
# 	Reporter Plugin
#
# 	Read the docs:
# 	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

from GlyphsApp import GSPath, objcObject, TABDIDOPEN, TABWILLCLOSE, Glyphs
from GlyphsApp.plugins import ReporterPlugin, pathForResource, objc
from typing import List, Optional
import traceback
from typing import Any

Glyphs: Any = Glyphs
# ------------------

# Shut up Pylance
from AppKit import (
    NSBezierPath,  # type: ignore
    NSMaxX,  # type: ignore
    NSImage,  # type: ignore
    NSMinX,  # type: ignore
    NSMaxY,  # type: ignore
    # NSMidX,  # type: ignore
    NSMidY,  # type: ignore
    NSMinY,  # type: ignore
    NSHeight,  # type: ignore
    NSWidth,  # type: ignore
    NSGradient,  # type: ignore
    NSColor,  # type: ignore
    NSFont,  # type: ignore
    NSMakeRect,  # type: ignore
    # NSZeroRect,  # type: ignore
    NSUserDefaults,  # type: ignore
    NSString,  # type: ignore
    NSMutableParagraphStyle,  # type: ignore
    NSAffineTransform,  # type: ignore
    NSCenterTextAlignment,  # type: ignore
    NSFontAttributeName,  # type: ignore
    NSParagraphStyleAttributeName,  # type: ignore
    NSForegroundColorAttributeName,  # type: ignore
    NSApplication,  # type: ignore
    NSFontWeightBold,  # type: ignore
    NSNotificationCenter,  # type: ignore
    NSUserDefaultsController,  # type: ignore
    NSButton,  # type: ignore
    NSRect,  # type: ignore
    NSTexturedRoundedBezelStyle,  # type: ignore
    NSToggleButton,  # type: ignore
    NSImageOnly,  # type: ignore
    NSImageScaleNone,  # type: ignore
    NSView,  # type: ignore
    NSSlider,  # type: ignore
    NSSliderTypeLinear,  # type: ignore
    NSSwitchButton,  # type: ignore
    NSOnState,  # type: ignore
    NSOffState,  # type: ignore
    NSViewHeightSizable,  # type: ignore
    NSViewWidthSizable,  # type: ignore
    NSControlSizeRegular,  # type: ignore
    NSLayoutAttributeLeft,  # type: ignore
    NSFontSystemFontSize,  # type: ignore
    NSRegularControlSize,  # type: ignore
    NSLeftTextAlignment,  # type: ignore
    NSViewMinYMargin,  # type: ignore
    NSViewMaxYMargin,  # type: ignore
)

# Changelog
# NEW:
# 	+ Fix observations
# 	+ Show predefined rotations in the bottom preview
# 	+ Add Selection Mode: draw only selected paths
# 	+ Add Mirror axis if Flipped V/H is active
# 	+ Add Center of Rotation

KEY_ROTATIONSBUTTON = "com_markfromberg_showRotations"
KEY_FLIPPED_HORIZONTAL = "com_markfromberg_showRotated_flip_horizontal"
KEY_FLIPPED_VERTICAL = "com_markfromberg_showRotated_flip_vertical"
KEY_ONLY_SELECTION = "com_markfromberg_showRotated_only_selection"
KEY_SUPERIMPOSED = "com_markfromberg_showRotated_superimposed"
KEY_ROTATION_ANGLE = "com_markfromberg_showRotated_angle"


class ShowRotated(ReporterPlugin):
    @objc.python_method
    def settings(self):
        self.color = 0.0, 0.5, 0.3, 0.3
        self.menuName = Glyphs.localize(
            {
                "en": "Rotated",
                "de": "Rotiert",
                "es": "Rotado",
                "it": "Ruotato",
                "fr": "Tourné",
                "ko": "회전",
                "zh-Hans": "旋转",
                "zh-Hant": "旋轉",
                "ar": "مدور",
                "el": "Περιστραμμένο",
                "hi": "घुमाया हुआ",
                "sv": "Roterad",
                "no": "Roterte",
                "da": "Roteret",
                "pl": "Obrócone",
                "cs": "Otočeno",
                "pt": "Rotacionado",
                "th": "หมุน",
                "vi": "Xoay",
            }
        )
        self.name = self.menuName
        self.button_instances = []

        self.setup_ui()
        self.setup_defaults()

    def setup_ui(self):
        # macOS 標準控制項間距
        standard_padding = 12
        checkbox_height = 18
        slider_height = 24
        text_offset = 20
        control_width = 200
        
        # 計算整體面板所需高度
        # 4個複選框 + 1個滑桿 + 間距
        total_height = (checkbox_height * 4) + slider_height + (standard_padding * 5)
        
        # 建立主視圖
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, control_width, total_height))
        # 修改自動調整掩碼：固定在底部，跟隨上緣變動
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        
        # 設定目前Y座標位置（從底部往上佈局）
        current_y = total_height - (checkbox_height + standard_padding)
        
        # 建立 Superimpose 複選框
        self.checkbox_superimposed = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, current_y, control_width, checkbox_height)
        )
        self.checkbox_superimposed.setButtonType_(NSSwitchButton)
        self.checkbox_superimposed.setTitle_("Superimpose in Layer")
        self.checkbox_superimposed.setAction_(objc.selector(self.update_, signature=b"v@:@"))
        self.checkbox_superimposed.setTarget_(self)
        self.checkbox_superimposed.setFont_(NSFont.systemFontOfSize_(NSFontSystemFontSize))
        self.checkbox_superimposed.sizeToFit()
        self.view.addSubview_(self.checkbox_superimposed)
        
        # 更新Y座標位置
        current_y -= (slider_height + standard_padding)
        
        # 建立旋轉角度滑桿
        self.slider = NSSlider.alloc().initWithFrame_(
            NSMakeRect(0, current_y, control_width, slider_height)
        )
        self.slider.setMinValue_(0)
        self.slider.setMaxValue_(360)
        self.slider.setNumberOfTickMarks_(17)
        self.slider.setAllowsTickMarkValuesOnly_(True)
        self.slider.setContinuous_(True)
        self.slider.setSliderType_(NSSliderTypeLinear)
        self.slider.setControlSize_(NSRegularControlSize)
        self.slider.setAction_(objc.selector(self.update_, signature=b"v@:@"))
        self.slider.setTarget_(self)
        self.view.addSubview_(self.slider)
        
        # 更新Y座標位置
        current_y -= (checkbox_height + standard_padding)
        
        # 建立水平翻轉複選框
        self.horizontal = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, current_y, control_width, checkbox_height)
        )
        self.horizontal.setButtonType_(NSSwitchButton)
        self.horizontal.setTitle_("Flip Horizontally")
        self.horizontal.setAction_(objc.selector(self.update_, signature=b"v@:@"))
        self.horizontal.setTarget_(self)
        self.horizontal.setFont_(NSFont.systemFontOfSize_(NSFontSystemFontSize))
        self.horizontal.sizeToFit()
        self.view.addSubview_(self.horizontal)
        
        # 更新Y座標位置
        current_y -= (checkbox_height + standard_padding)
        
        # 建立垂直翻轉複選框
        self.vertical = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, current_y, control_width, checkbox_height)
        )
        self.vertical.setButtonType_(NSSwitchButton)
        self.vertical.setTitle_("Flip Vertically")
        self.vertical.setAction_(objc.selector(self.update_, signature=b"v@:@"))
        self.vertical.setTarget_(self)
        self.vertical.setFont_(NSFont.systemFontOfSize_(NSFontSystemFontSize))
        self.vertical.sizeToFit()
        self.view.addSubview_(self.vertical)
        
        # 更新Y座標位置
        current_y -= (checkbox_height + standard_padding)
        
        # 建立僅選擇複選框
        self.checkbox_selection_mode = NSButton.alloc().initWithFrame_(
            NSMakeRect(0, current_y, control_width, checkbox_height)
        )
        self.checkbox_selection_mode.setButtonType_(NSSwitchButton)
        self.checkbox_selection_mode.setTitle_("Rotate Selection Only")
        self.checkbox_selection_mode.setAction_(objc.selector(self.update_, signature=b"v@:@"))
        self.checkbox_selection_mode.setTarget_(self)
        self.checkbox_selection_mode.setFont_(NSFont.systemFontOfSize_(NSFontSystemFontSize))
        self.checkbox_selection_mode.sizeToFit()
        self.view.addSubview_(self.checkbox_selection_mode)
        
        # 為所有子視圖設定相同的自動調整掩碼，確保它們相對於主視圖的位置保持不變
        for subview in [self.checkbox_superimposed, self.slider, self.horizontal, self.vertical, self.checkbox_selection_mode]:
            subview.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        
        # 設定側邊欄選單
        self.generalContextMenus = [
            {"name": "%s:" % self.name, "action": None},
            {"view": self.view},
        ]

    def setup_defaults(self):
        """Assumes that the UI is set up by now"""
        user_defaults = NSUserDefaultsController.sharedUserDefaultsController()
        user_defaults.defaults().registerDefaults_(
            {
                KEY_FLIPPED_HORIZONTAL: False,
                KEY_FLIPPED_VERTICAL: False,
                KEY_ONLY_SELECTION: False,
                KEY_SUPERIMPOSED: True,
                KEY_ROTATION_ANGLE: 180,
            }
        )
        
        # 綁定控制項到使用者預設值
        self.checkbox_superimposed.bind_toObject_withKeyPath_options_(
            "value", user_defaults, objcObject(f"values.{KEY_SUPERIMPOSED}"), None
        )
        self.horizontal.bind_toObject_withKeyPath_options_(
            "value", user_defaults, objcObject(f"values.{KEY_FLIPPED_HORIZONTAL}"), None
        )
        self.vertical.bind_toObject_withKeyPath_options_(
            "value", user_defaults, objcObject(f"values.{KEY_FLIPPED_VERTICAL}"), None
        )
        self.checkbox_selection_mode.bind_toObject_withKeyPath_options_(
            "value", user_defaults, objcObject(f"values.{KEY_ONLY_SELECTION}"), None
        )
        self.slider.bind_toObject_withKeyPath_options_(
            "value", user_defaults, objcObject(f"values.{KEY_ROTATION_ANGLE}"), None
        )
        
        # 啟用/禁用控制項
        self.slider.bind_toObject_withKeyPath_options_(
            "enabled", user_defaults, objcObject(f"values.{KEY_SUPERIMPOSED}"), None
        )
        self.horizontal.bind_toObject_withKeyPath_options_(
            "enabled", user_defaults, objcObject(f"values.{KEY_SUPERIMPOSED}"), None
        )
        self.vertical.bind_toObject_withKeyPath_options_(
            "enabled", user_defaults, objcObject(f"values.{KEY_SUPERIMPOSED}"), None
        )
        self.checkbox_selection_mode.bind_toObject_withKeyPath_options_(
            "enabled", user_defaults, objcObject(f"values.{KEY_SUPERIMPOSED}"), None
        )

    def update_(self, sender):
        self.update(sender)

    @objc.python_method
    def start(self):
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "addRotationsButton:", TABDIDOPEN, objc.nil
        )
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "removeRotationsButton:", TABWILLCLOSE, objc.nil
        )
        user_defaults = NSUserDefaultsController.sharedUserDefaultsController()
        user_defaults.addObserver_forKeyPath_options_context_(
            self,
            objcObject(f"values.{KEY_ROTATIONSBUTTON}"),
            0,
            123,
        )
        iconPath = pathForResource("rotatedIcon", "pdf", __file__)
        self.toolBarIcon = NSImage.alloc().initWithContentsOfFile_(iconPath)
        self.toolBarIcon.setTemplate_(True)

    def addRotationsButton_(self, notification):
        tab = notification.object()
        if hasattr(tab, "addViewToBottomToolbar_"):
            bottom_button = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 18, 14))
            bottom_button.setBezelStyle_(NSTexturedRoundedBezelStyle)
            bottom_button.setBordered_(False)
            bottom_button.setButtonType_(NSToggleButton)
            bottom_button.setTitle_("")
            bottom_button.cell().setImagePosition_(NSImageOnly)
            bottom_button.cell().setImageScaling_(NSImageScaleNone)
            bottom_button.setImage_(self.toolBarIcon)
            bottom_button.setToolTip_(self.menuName)
            tab.addViewToBottomToolbar_(bottom_button)
            self.button_instances.append(bottom_button)
            try:
                tab.tempData["rotationsButton"] = bottom_button  # Glyphs 3
            except:
                tab.userData["rotationsButton"] = bottom_button  # Glyphs 2
            user_defaults = NSUserDefaultsController.sharedUserDefaultsController()
            bottom_button.bind_toObject_withKeyPath_options_(
                "value",
                user_defaults,
                objcObject(f"values.{KEY_ROTATIONSBUTTON}"),
                None,
            )
            self.toggle_buttons_hidden(
                True
            )  # Hide all buttons first, otherwise they show when the plugin is off but a font with tabs is opened.

    def removeRotationsButton_(self, notification):
        tab = notification.object()
        try:
            bottom_button = tab.tempData["rotationsButton"]  # Glyphs 3
        except:
            bottom_button = tab.userData["rotationsButton"]  # Glyphs 2
        if bottom_button is not None:
            bottom_button.unbind_("value")
            self.button_instances.remove(bottom_button)

    def observeValueForKeyPath_ofObject_change_context_(self, keypath, object, change, context):
        # print("__observeValueForKeyPath_ofObject_change_context_ %@", keypath)
        NSNotificationCenter.defaultCenter().postNotificationName_object_("GSRedrawEditView", None)

    # @objc.python_method
    # def rotation_transform(self, angle, center):
    #     rotation = NSAffineTransform.transform()
    #     rotation.translateXBy_yBy_(center.x, center.y)
    #     rotation.rotateByDegrees_(angle)
    #     rotation.translateXBy_yBy_(-center.x, -center.y)
    #     return rotation

    @objc.python_method
    def toggle_buttons_hidden(self, value):
        for bottom_button in self.button_instances:
            if bottom_button:
                bottom_button.setHidden_(value)

    def willActivate(self):
        self.toggle_buttons_hidden(False)

    def willDeactivate(self):
        self.toggle_buttons_hidden(True)

    @objc.python_method
    def rotation(self, x, y, angle):
        rotation = NSAffineTransform.transform()
        rotation.translateXBy_yBy_(x, y)
        rotation.rotateByDegrees_(angle)
        rotation.translateXBy_yBy_(-x, -y)
        return rotation

    @objc.python_method
    def selected_paths(self, layer) -> Optional[List[GSPath]]:  # type: ignore
        try:
            # fmt: off
            return [shape for shape in layer.selectedObjects()["shapes"] if isinstance(shape, GSPath)]
            # fmt: on
        except:
            return None

    @objc.python_method
    def draw_rotated(self, layer):
        angle = int(Glyphs.defaults[KEY_ROTATION_ANGLE])
        bezier_path = layer.copyDecomposedLayer().bezierPath
        if not bezier_path:
            return

        try:
            NSColor.colorWithCalibratedRed_green_blue_alpha_(*self.color).set()
            bounds = bezier_path.bounds()
            if Glyphs.boolDefaults[KEY_ONLY_SELECTION]:
                selected_paths = NSBezierPath.alloc().init()
                layer_paths_selected = self.selected_paths(layer)
                if not layer_paths_selected:
                    return
                for p in layer_paths_selected:
                    selected_paths.appendBezierPath_(p.bezierPath)
                bezier_path = selected_paths
                bounds = selected_paths.bounds()

            x, y = self.get_center(bounds)
            self.transform_path(bezier_path, x, y, angle)
            self.apply_flip_transformations(bezier_path, bounds, x, y)
            self.draw_path(bezier_path, bounds, x, y)
        except:
            print(traceback.format_exc())

    def get_center(self, bounds):
        try:
            return (
                bounds.origin.x + 0.5 * bounds.size.width,
                bounds.origin.y + 0.5 * bounds.size.height,
            )
        except:
            return 0, 0

    def transform_path(self, bezier_path, x, y, angle):
        rotation = self.rotation(x, y, angle)
        bezier_path.transformUsingAffineTransform_(rotation)

    def apply_flip_transformations(self, bezier_path, bounds, x, y):
        flip_transform = NSAffineTransform.transform()
        flip_transform.translateXBy_yBy_(x, y)

        if Glyphs.boolDefaults[KEY_FLIPPED_HORIZONTAL]:
            flip_transform.scaleXBy_yBy_(-1, 1)
            self.draw_mirror_line(x, NSMaxY(bounds), x, NSMinY(bounds), x, y, 0)
        if Glyphs.boolDefaults[KEY_FLIPPED_VERTICAL]:
            flip_transform.scaleXBy_yBy_(1, -1)
            self.draw_mirror_line(
                NSMinX(bounds), NSMidY(bounds), NSMaxX(bounds), NSMidY(bounds), x, y, 0
            )

        flip_transform.translateXBy_yBy_(-x, -y)
        if (
            Glyphs.boolDefaults[KEY_FLIPPED_HORIZONTAL]
            or Glyphs.boolDefaults[KEY_FLIPPED_VERTICAL]
        ):
            bezier_path.transformUsingAffineTransform_(flip_transform)

    def draw_mirror_line(self, x1, y1, x2, y2, x, y, angle):
        mirror_line = NSBezierPath.alloc().init()
        mirror_line.setLineWidth_(0.75 / self.getScale())
        mirror_line.moveToPoint_((x1, y1))
        mirror_line.lineToPoint_((x2, y2))
        mirror_line.transformUsingAffineTransform_(self.rotation(x, y, angle))
        mirror_line.setLineDash_count_phase_(
            [4 / self.getScale(), 4 / self.getScale()], 2, 0
        )
        mirror_line.stroke()

    def draw_path(self, bezier_path, bounds, x, y):
        if bezier_path:
            bezier_path.setLineDash_count_phase_(
                [4 / self.getScale(), 4 / self.getScale()], 2, 0
            )
            bezier_path.setLineWidth_(1 / self.getScale())
            bezier_path.stroke()
            bezier_path.fill()
            self.draw_center_cross(x, y)
            self.draw_gradient(bounds, x, y)

    def draw_center_cross(self, x, y):
        cross_size = 10 / self.getScale()
        center_cross_1 = NSBezierPath.alloc().init()
        center_cross_2 = NSBezierPath.alloc().init()
        center_cross_1.moveToPoint_((x, y - cross_size))
        center_cross_2.moveToPoint_((x + cross_size, y))
        center_cross_1.lineToPoint_((x, y + cross_size))
        center_cross_2.lineToPoint_((x - cross_size, y))
        center_cross_1.setLineWidth_(0.75 / self.getScale())
        center_cross_2.setLineWidth_(0.75 / self.getScale())
        center_cross_1.stroke()
        center_cross_2.stroke()

    def draw_gradient(self, bounds, x, y):
        thickness = 100
        mirror_color = NSColor.colorWithDeviceRed_green_blue_alpha_(
            *self.color[:3], 0.2
        )
        mirror_color_clear = NSColor.clearColor()
        if Glyphs.boolDefaults[KEY_FLIPPED_HORIZONTAL]:
            gradient_rect_horizontal = NSMakeRect(
                x, NSMinY(bounds), thickness, NSHeight(bounds)
            )
            gradient_path_horizontal = NSBezierPath.bezierPathWithRect_(
                gradient_rect_horizontal
            )
            gradient_horizontal = NSGradient.alloc().initWithColors_(
                [mirror_color, mirror_color_clear]
            )
            gradient_horizontal.drawInBezierPath_angle_(gradient_path_horizontal, 0)
        if Glyphs.boolDefaults[KEY_FLIPPED_VERTICAL]:
            gradient_rect_vertical = NSMakeRect(
                NSMinX(bounds), NSMidY(bounds), NSWidth(bounds), thickness
            )
            gradient_path_vertical = NSBezierPath.bezierPathWithRect_(
                gradient_rect_vertical
            )
            gradient_vertical = NSGradient.alloc().initWithColors_(
                [mirror_color, mirror_color_clear]
            )
            gradient_vertical.drawInBezierPath_angle_(gradient_path_vertical, 90)

    @objc.python_method
    def update(self, sender):
        try:
            Glyphs = NSApplication.sharedApplication()
            current_tab_view = Glyphs.font.currentTab
            if current_tab_view:
                current_tab_view.graphicView().setNeedsDisplay_(True)
        except:
            pass

    @objc.python_method
    def background(self, layer):  # def foreground(self, layer):
        if Glyphs.boolDefaults[KEY_SUPERIMPOSED]:
            self.draw_rotated(layer)

    def needsExtraMainOutlineDrawingInPreviewLayer_(self, layer):
        return not Glyphs.boolDefaults[KEY_ROTATIONSBUTTON]

    def drawForegroundInPreviewLayer_options_(self, layer, options):
        if not Glyphs.boolDefaults[KEY_ROTATIONSBUTTON]:
            return

        try:
            # Check if there are any selected layers
            selected_layers = Glyphs.font.selectedLayers
            if len(selected_layers) == 0:
                return
            
            # Get the currently selected character
            current_layer = selected_layers[0]
            current_glyph = current_layer.parent
            
            # Get the glyph of the preview layer
            layer_glyph = layer.parent
            
            # If glyph names are different, skip this glyph
            if current_glyph.name != layer_glyph.name:
                return
                
            # Check layer matching conditions
            # If it's the same glyph but different layer, and not a preview layer, don't draw
            if current_layer.layerId != layer.layerId and layer.name != "Preview":
                # In some special cases, preview layer might not have a name
                if not hasattr(layer, "isPreviewLayer") or not layer.isPreviewLayer:
                    return

        except Exception as e:
            print(f"Selection check error: {str(e)}")
            print(traceback.format_exc())
            return

        is_black = NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")

        base_position_transform = NSAffineTransform.transform()
        padding = 100
        label_height = 100

        paragraph_style = NSMutableParagraphStyle.alloc().init()
        paragraph_style.setAlignment_(NSCenterTextAlignment)
        string_attributes = {
            NSFontAttributeName: NSFont.systemFontOfSize_weight_(80, NSFontWeightBold),
            NSForegroundColorAttributeName: NSColor.redColor(),
            NSParagraphStyleAttributeName: paragraph_style,
        }

        # Draw 8 different rotation angles
        for i in range(8):
            rotation_transform = NSAffineTransform.transform()
            layer_path = layer.completeBezierPath.copy()
            if not layer_path:
                return

            try:
                rotation_degrees = 90 * i
                bounds = layer.bounds
                bounds_orientation_sideways = rotation_degrees / 90 % 2 == 1

                if bounds_orientation_sideways:
                    base_position_transform.translateXBy_yBy_(NSHeight(bounds) / 2, 0)
                else:
                    base_position_transform.translateXBy_yBy_(NSWidth(bounds) / 2, 0)

                x, y = self.get_center(bounds)

                rotation_transform.translateXBy_yBy_(x, y)
                if i > 3:
                    rotation_transform.scaleXBy_yBy_(-1, 1)
                rotation_transform.rotateByDegrees_(rotation_degrees)
                rotation_transform.translateXBy_yBy_(-x, -y)

                combined_transform = NSAffineTransform.transform()
                combined_transform.appendTransform_(rotation_transform)
                combined_transform.appendTransform_(base_position_transform)

                layer_path.transformUsingAffineTransform_(combined_transform)

                if is_black:
                    NSColor.whiteColor().set()
                else:
                    NSColor.blackColor().set()
                layer_path.fill()

                label = NSString.stringWithString_(
                    f"{rotation_degrees % 360}° {'↔' if i > 3 else ''}"
                )
                label.drawInRect_withAttributes_(
                    NSRect(
                        (
                            NSMinX(layer_path.bounds()) - padding,
                            layer.descender - label_height,
                        ),
                        (NSWidth(layer_path.bounds()) + padding * 2, label_height),
                    ),
                    string_attributes,
                )

                if bounds_orientation_sideways:
                    base_position_transform.translateXBy_yBy_(NSHeight(bounds) / 2, 0)
                else:
                    base_position_transform.translateXBy_yBy_(NSWidth(bounds) / 2, 0)

                base_position_transform.translateXBy_yBy_(padding, 0)

            except Exception as e:
                print(f"Rotation drawing error: {str(e)}")
                print(traceback.format_exc())
