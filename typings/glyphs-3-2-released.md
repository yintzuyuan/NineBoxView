---
Title: Glyphs 3.2 released | Glyphs
URL: https://glyphsapp.com/news/glyphs-3-2-released
Date: 2021-04-08 12:00
Author: Rainer Erich Scheichelbauer
Tags: #glyphs #font #design #python #api
---
Markdown Content:

Glyph data and script support
-----------------------------

In GlyphData.xml, you can now **override default positions of anchors** for individual glyphs. You can use these codes:

*   `minY` and `maxY`: bottom and top edges of the bounding box
*   `minX` and `maxX`: left and right edges of the bounding box
*   `centerX` and `centerY`: horizontal and vertical centers of the bounding box
*   `width`: the advance width of the glyph (or right sidebearing)
*   `descender`, `baseline`, `ascender`: vertical metrics

You can add one math operation with any of these operators: `+-/*`, followed by an integer or floating point number like `20` or `0.7`. Separate x and y operations with a semicolon, the order of which does not matter. Examples:

*   `bottom@maxX`: bottom anchor on the baseline but moved to the right edge of the bounding box.
*   `ogonek@baseline;maxX`: at baseline, to the right.
*   `_top@centerX+20`: top connecting anchor, shifted 20 units towards the right.
*   `ogonek@baseline+5;maxX-10`:
*   `ogonek@baseline+5;width*0.7`: ogonek anchor positioned at 5 units above baseline, 70% of the width

Glyphs will first calculate the default positioning and then apply the extra keys. So you only need to specify what you want to change. Needless to say, we tried to set a good example and updated default anchor positions in Basic Latin, e.g., in `d`, `h`, `B` and `H`.

More GlyphData improvements include:

*   Glyphs now allows more than one `GlyphData.xml` file next to the `.glyphs` file, just like it does inside the `Info` folder in Application Support.
*   We fixed the default setup for `softhyphen`, it is now zero-widthed and empty. Thanks to the fontbakery users out there for pointing this out to us.
*   `ordfeminine` and `ordmasculine` are now cased as _Minor,_ allowing for vertically shifting components by default. Useful if you populate them with components of lowercase `a` and `o`.
*   Added Ogham script, many thanks to Michael Everson for his input.
*   Added Kawi script.
*   Added more Canadian syllabary.
*   Added a bunch of missing Han infos, and some more CJK infos, specifically CJK Ideograph Extension H+I blocks. If you know, you know.
*   Adjustments and corrections for Coptic and Mongolian.
*   Improved sorting of math glyphs.
*   CustomFilter.xml files now also work via aliases. No more managing of file copies.

Python and scripting
--------------------

Everybody uninstall and reinstall their Python module via _Window \> Plugin Manager \> Modules._ You will get **Python 3.11**, including `PyObjC`, `brotli` and `zopfli`, so you can do post production. In the meantime, Python 3.12 got out. Glyphs supports it too now, if you use your own custom installation of _Python in Glyphs \> Settings \> Addons._ [Do not forget to install PyObjC](https://glyphsapp.com/learn/extending-glyphs) and other necessary modules if you do so.

We improved _Window \> Macro Panel._ Firstly, there are way **more autocomplete keywords** available while typing code. And secondly, you can now minimize the window with the yellow button. (Of course, you can also still toggle its display with Cmd-Opt-M.) And we added a user default `GSMacroWindowAllowNoneAsciiInput`, which, if set to `False`, will only allow you to type good old 7-bit ASCII. The default key is added to the _Hidden Settings_ mekkablue script.

Speaking of which, there is a new boolean user default `IgnoreRecentScriptInvokedByKeyboard` which may improve your life significantly if you use **keyboard shortcuts for scripts** in the _Script_ menu. If it is turned on (set to `1` or `True`), the Cmd-Opt-R shortcut for repeating the most recent script will only be used for scripts that were mouse-picked from the menu. Scripts that were triggered with a keyboard shortcut (or opened through the _Help_ menu) will not change the _Script \> Run:…_ entry.

For debugging, you can now press Cmd-Opt-Shift-M to invoke a **floating console window** (or hold down Shift and pick _Window \> Floating Macro Console_), which, contrary to the conventional _Window \> Macro Panel,_ even stays visible when the app is in the background:

![Image 18](https://glyphsapp.com/news/glyphs-3-2-released)

We changed the behavior of `tab.layers` (where `tab` is an Edit view tab) to return the layers actually visible in the tab, and we added a setter for `tab.layersCursor`. But be careful to set it within the range of the visible layers. Here is a code sample that moves the cursor gracefully, note the modulo operator `%`:

```
def moveCursorInTab(tab, move=1):
    newPosition = (tab.layersCursor + move) % (len(tab.layers) + 1)
    tab.layersCursor = newPosition

moveCursorInTab(Glyphs.font.currentTab, 1)
```

We added `PickGlyphs()` to the Python wrapper: `PickGlyphs(content, masterID, searchString, defaultsKey)` so you can have you user pick a glyph. `content` is a list of `GSGlyph` objects, `masterID` the ID of a font master, and a `str` as search string. Here is an example:

```
font = Glyphs.font
choice = PickGlyphs(
    list([g for g in font.glyphs if g.case == GSUppercase]), # must be a list of GSGlyph objects
    font.selectedFontMaster.id,
    "circumflex",
    )
print(choice)
```

… which will give you a glyph picker dialog that pre-populates the search field with the `searchString` you specified:

![Image 19](https://glyphsapp.com/news/glyphs-3-2-released)

And as a result you get a tuple of two things: a list of your selected `GSGlyph` objects, and your search string:

```
([<GSGlyph 0x2a89629b0> Acircumflex, <GSGlyph 0x2a99a4290> Ecircumflex], 'circumflex')
```

Alternatively, you can specify a fourth argument, `defaultsKey`, which stores the search string the user types in a preference with that key, e.g.:

```
font = Glyphs.font
choice = PickGlyphs(
    list(font.glyphs),
    font.selectedFontMaster.id,
    None,
    "com.mekkablue.GlyphMangler.search",
    )
```

If you specify a `defaultsKey`, the third argument, `searchString`, will be ignored. The return value is the same tuple as above, but this time, you can query and overwrite the search string with the defaults key:

```
print(Glyphs.defaults["com.mekkablue.GlyphMangler.search"]) # yields whatever the user typed in last
```

There is a new object called `Glyphs.colorDefaults` which allows you to **override all kinds of UI colors**, provided you know the pref name for the color in question. The defaults take [NSColor](https://developer.apple.com/documentation/appkit/nscolor?language=objc) objects as values. E.g., if you wanted to change the grey component color, you could do it like this:

```
from AppKit import NSColor
myColor = NSColor.colorWithRed_green_blue_alpha_(.8, .5, .2, .4)
Glyphs.colorDefaults["GSColorComponent"] = myColor
```

Here’s the list of currently supported pref names:

```
GSColorBackgroundCanvas
GSColorBackgroundCanvasDark
GSColorBackgroundStroke
GSColorBackgroundStrokeDark
GSColorCanvas
GSColorCanvasDark
GSColorComponent
GSColorComponentLocked
GSColorComponentAligned
GSColorComponentHorizontalAligned
GSColorComponentDark
GSColorComponentLockedDark
GSColorComponentAlignedDark
GSColorComponentHorizontalAlignedDark
GSColorForeground
GSColorForegroundDark
GSColorGridMain
GSColorGridMainDark
GSColorGridSub
GSColorGridSubDark
GSColorKerningNegative
GSColorKerningNegativeDark
GSColorKerningPositive
GSColorKerningPositiveDark
GSColorNodeCorner
GSColorNodeCornerDark
GSColorNodeSmooth
GSColorNodeSmoothDark
GSColorOtherLayersStroke
GSColorOtherLayersStrokeDark
GSColorZones
GSColorZonesDark
```

The ones that end in `Dark` are the variants for Dark Mode. Make sure you pick a more subdued, less screaming color, and brightness-wise, expect an inverted (white on black) environment. `GSColorForeground` and `GSColorForegroundDark` are (a) the colors of the paths while being edited, as well as (b) the fill color of the glyphs when you are typing with the Text tool (shortcut T). I think all the others are pretty self-explanatory.

For reporter plug-ins, we added a drawing API for Font View cells

```
self.drawFontViewBackgroundForLayer_inFrame_(layer, frame)
self.drawFontViewForegroundForLayer_inFrame_(layer, frame)
```

… where `frame` is the `NSRect` that represents the glyph cell. Use this as reference for any drawing you want to do in the cell (e.g. a dot or a symbol). `Foreground` and `Background` mean that you draw in front of or behind the image of the glyph.

For reference, I implemented it [in the Show Component Order plug-in](https://github.com/mekkablue/ShowComponentOrder/blob/17da2a1c176a6afd1b5d515b8685df471c6ac377/ShowComponentOrder.glyphsReporter/Contents/Resources/plugin.py#L64-L81), and [in the Show Export Status plug-in](https://github.com/mekkablue/ShowExportStatus/blob/cf23f2768cb50da6aeca97c32762c27c7d283228/ShowExportStatus.glyphsReporter/Contents/Resources/plugin.py#L46-L52). The former also contains a useful function called `fitLayerInFrame()`, which helps scale the content of the layer into the cell the same way Glyphs does it. Comes in handy if you want to draw over the shapes of the glyph. We are discussing a convenience function for the future.

And we have something for drawing in the Preview area as well:

```
self.drawBackgroundInPreviewLayer_options_(layer, options)
self.drawForegroundInPreviewLayer_options_(layer, options)
self.needsExtraMainOutlineDrawingInPreviewLayer_(layer)
```

The variants for `Background` and `Foreground` are, like above, for drawing in front or behind the main outline. The argument `options` is a `dict` passed to the function, containing two keys for now:

*   `options["Scale"]` is a `float` representing the scale factor, similar to `self.getScale()` elsewhere, but exclusively for the preview in question. Use this for line widths that need to stay the same on the screen, no matter what the user scales the preview to. E.g., `lineWidth = 1.0 / options["Scale"]` always gives you one pixel thickness.
*   `options["Black"]` is a `bool` representing the inverse setting in the Preview area: `True` if it is white type on black background, `False` if it is black type on white background. You may want to choose different color depending on context.

If you add a `needsExtraMainOutlineDrawingInPreviewLayer_()` function to your reporter, and it returns `False`, then Glyphs will not draw anything and leave it all to you.

More scripting news:

*   Plug-ins and modules are updated more aggressively, though still quietly in the background
*   Added documentation for `GSPathSegment`
*   Added `GSGradient` to python wrapper
*   Fixed the `drawingTools` Python API
*   Fixed `GSComponent.automaticAlignment`
*   Fixed `GSFont.newTab()`, sorry about the issues you may have run into
*   Fixed missing `countOfUserData`
*   Fixed `GSBackgroundImage` wrapper
*   Fixed `GSInstance.active`: it always gives you the updated value now
*   `GSElement.orientation` allows accessing the clockwise or counterclockwise orientation of components
*   Fixed setting `GSGlyph.color` to `None` for deleting the assigned glyph color
*   Improved handling of external scripts
*   Refactored the _Extrude_ filter so you can access its objects from within a script
*   Glyphs is now much better at catching plug-in exceptions
*   Improved memory usage of Python scripts

And, last but not least, we cleaned up the code samples on [docu.glyphsapp.com](https://docu.glyphsapp.com/). Sorry for any inconvenience you may have had in recent weeks.
