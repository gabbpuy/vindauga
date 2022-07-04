# Technical Information Database
**TI813C.txt   Understanding & Using Turbo Vision's Palette.**     

* Category   :General
* Platform    :All
* Product    :Borland C++  3.1    


### DESCRIPTION
The palette system in Turbo Vision is designed to make it easy
for either the programmer or the user to customize the colors of
an application.  The system uses an object oriented approach
which relies on an implementation where the colors of a
particular view are dependent on the colors of the owner view.
So, if there is a view X that can appear inside either of two
`TWindow` objects A and B, the colors seen by the user will depend
on whether it is a child of A or B at that moment.
There are two ways of thinking about colors in Turbo Vision: One
is to consider a palette entry as a particular color.  The other
is to envision it as representing the color currently used for a
particular type of object, like selected text or normal text.
Which of these is used will depend upon the nature of the object
being drawn.  The latter method should be employed when
considering the palettes for pre-defined Turbo Vision objects.
When the programmer is writing a draw function for a view, he/she
will want to be able to select a particular color or style for
drawing.  It may be desirable to have similar components of
unrelated views to be drawn in the same color.  It may also be
desirable to give the user a method of changing at runtime the
colors used for the application. The palette system in Turbo
Vision will allow both of these possiblities.  A further benefit
of the Turbo Vision palettes is that the system automatically
detects the type of display being used (color, black and white,
or monochrome) and sets up the palette accordingly.  If the
programmer chooses to modify the system palette, this should be
taken into account when the new palette is designed.
See the `CONSTRUCTION` section for further details.

### HOW IT WORKS
So, how does one actually get a particular color from the palette
inside the draw member function of a view?  The answer lies in
understanding in greater detail how a given palette is related to
its parents.
Every class derived from `TView` (which means every visible Turbo
Vision object) has a color palette.  The palette may be inherited
(like `TApplication`) or it may be NULL (like `TDeskTop`) but all
views do have one.  The virtual function getPalette() is used to
supply the palette for each view. It is important to realize that
this particular function is never called explicitly by the
programmer; it will be called by Turbo Vision when necessary.
The member functions of`TView` that actually do write to the view,
with one exception, all take a color index as one of their
parameters.  This parameter must be thought of as the value of an
index to a style, not the actual color.
For example, When using `TView::writeStr()`, one parameter
specifies a color index.  Inside of `writeStr()` the following
procedure is applied to convert this index into an actual color
value.  The current view's palette is examined at the specified
index entry and a value X is found there.  Next, the view's
owner's palette is retrieved and X is used as an index into this
palette where another value Y resides.  This process continues
until the view being examined no longer has an owner.  At this
time, the value at the current index is returned and interpreted
as a standard PC color attribute byte.

### EXAMPLE
Here are the palettes for the classes in the enclosed example and
how they map into each other:

```
                            x01   x02   x03   x04   x05   x06
     +--------------------+-----+-----+-----+-----+-----+-----+
     |TTextView           | x09 | x0A | x0B | x0C | x0D | x0E |
     +--------------------+-----+-----+-----+-----+-----+-----+

                             v     v     v     v     v     v
                   x01-x08  x09   x0A   x0B   x0C   x0D   x0E
     +------------+-------+-----+-----+-----+-----+-----+-----+
     |TTextWindow |  ...  | x40 | x41 | x42 | x43 | x44 | x45 |
     +------------+-------+-----+-----+-----+-----+-----+-----+

                             v     v     v     v     v     v
                   x01-x3F  x40   x41   x42   x43   x44   x45
     +------------+-------+-----+-----+-----+-----+-----+-----+
     ?TTestApp    |  ...  | x3E | x2D | x72 | x5F | x68 | x4E |
     +------------+-------+-----+-----+-----+-----+-----+-----+

                                  Table I
```

All numbers used in the palettes in this document are in
hexadecimal (it is easier to understand attributes in that base.)
Here is a concrete case of a "palette" walk, taken from the code
supplied with this document.  Suppose there is a view of type
`TTestView` inserted inside a window of type`TTestWindow`, itself
inserted in the desktop.  The palettes for these views are shown
above.  To draw something with color 0x01, simply use 0x01 as the
parameter to the write functions used in`TTestView::draw`().
`TTestView`'s palette contains the number 0x09 at index 0x01 and
`TTestView`'s owner is`TTestWindow`.  Index 0x09 in`TTestWindow`'s
palette contains 0x40. `TTestWindow`'s owner is`TDesktop` which has
a NULL palette and is skipped (see notes).`TDesktop`'s owner is
`TTestApp` and it's palette contains 0x3E at index 0x40.  So the
color that will be used is 0x3E or yellow on cyan.
The writeXXX functions in`TView` all take color index values in
the current palette except one, `writeLine(...,TDrawBuffer)`.  A
`TDrawBuffer` is a buffer for an entire line.  Once constructed, it
is drawn into the view using writeLine(). `TDrawBuffer`'s member
functions for drawing are quite similar to`TView`'s with one
exception.  They do NOT use color index values.  They use
attribute bytes to determine the colors used. What this means is
that in order to use the color palettes, one must obtain the
color attribute for a member of the current palette by hand. This
is done with the function getColor().  Pass it the index and it
performs the "palette walk" and returns the actual attribute
represented.  Use this value in`TDrawBuffer`'s write functions.
Note that any attribute byte can be with a`TDrawBuffer`.
getColor() need not be the source of the value used.

### PALETTE CONSTRUCTION
Creating a new palette for a given view is quite simple, though
deciding what indexes to use may take some thought.  It requires
inheriting from the view and overriding the `getPalette()` member
function.  This function has the following prototype:

```cpp
  TPalette & TTestView::getPalette() const;
```

The actual palette is a character string where the bytes contain
the appropriate reference values.  These bytes are normally
written out in hex when the string is created.  For example,

```cpp
#define cpTestView "\x9\xA\xB\xC\xD\xE"
```

is the definition of the palette for`TTestView`.  The `cpTestView`
symbol is then used in`TPalette` constructor like this:
 `TPalette` palette( cpTestView, sizeof(cpTestView)-1 );
The subtraction of 1 from sizeof() is to remove the terminating
NULL that all C++ literal strings have by default.  Also, since a
reference to this palette is returned by `getPalette()`, it must
exist from the first call to `getPalette` onward and is normally
made a static local variable to function (to avoid polluting the
global name space.)  So the entire function looks like this:

```cpp
#define cpTestView "\x9\xA\xB\xC\xD\xE"
TPalette& TTestView::getPalette() const;
{
  static TPalette palette(cpTestView, sizeof(cpTestView)-1);
  return palette;
}
```      

What if a user has a black and white display?  A palette that has
been designed with the benefit of color will usually look
terrible when viewed in either black and white or monochrome
mode.  For this reason, Turbo Vision has three completely
distinct system palettes: `cpColor`, `cpBlackWhite`, and
`cpMonoChrome`.  At startup, the program will detect what kind of
display is attached and use the appropriate settings.  So, when
modifying the system palette, one needs to modify all three of
the basic system palettes.  The enclosed example addresses this
issue, as well as a similar one involving windows, since they
also have three palettes (for a different reason.)  The color
choices for the alternate color palettes can be select from the
lists below:

```
          cpBlackWhite                        cpMonochrome
      0x07    Light Grey on Black         0x07    White on Black
      0x0F    White on Black              0x70    Black on White
      0x70    Black on Light Grey         0x09    White on Black
                                                  Underlined
      0x78    Dark Grey on Light Grey             (not recommended)
      0x7F    White on Light Grey
```

One final note on`TWindow`'s.  This view has three palettes, like
`TProgram`.  However, this is so that it is easy to have three
different color schemes for windows used in an application, such
as yellow on blue for an editor but black on grey for a dialog
box.  Extending each of these palettes is done in a similar
fashion to the three palettes for`TProgram` with the exception
that`TWindow`'s palettes are not in a header file and thus must be
included by the programmer in the application along with the
extensions.  See the example for further details.

  ### NOTES
1. In some of the example programs and the User's Guide, you will
see getColor() being called with a value greater than 255.  In
this case, both bytes of the word passed are mapped into colors
and returned as a word with the attributes stored in the high and
low bytes.  This is required if one is uses
 `TDrawBuffer::writeCStr` to display strings with highlighted
characters (see documentation on writeCStr() for more details.)
2. The missing entries in table I can be found in the Turbo
  Vision User's Guide by looking under`TWindow` and`TProgram`.
3. If at anytime the index being used is out of range for the
  palette being examined, the error attribute is returned
  immediately.  The error attribute is Flashing White on Red.
4. If at anytime the current palette has no entries (NULL
  palette), then the owner's palette is examined directly.
 `TDeskTop` is one view that has a NULL palette.
5. The top of the chain will always be the application object,
  for it is the only view that will not have an owner.  The palette
  for the application is inherited from`TProgram`, but can be
  changed by overriding getPalette() in the application object (The
  class derived from`TApplication`.)
6. Using the`TDrawBuffer` object because of it's ability to
  completely bypass the palette system is sometimes desirable, but
  can produce unexpected side effects.  For example, running such a
  program on a VGA system running video mode 2 (BW80) will still
  produce colors, even though Turbo Vision itself will be running
  black and white.  ( This example will display this behaviour so
  try typing 'mode BW80' at the DOS prompt and then running the
  demo.)

```cpp
  //
  // PALETTE.CPP - Example module for palette system.
  //
  #define Uses_TView
  #define Uses_TWindow
  #define Uses_TPalette
  #define Uses_TDrawBuffer
  #include 
  #include "palette.h"                    // Class definitions for
                                          // this module
  #include                       // For sprintf()
  //
  //  TTestView constructor
  //
  #define cpTestView "\x9\xA\xB\xC\xD\xE" // SIX colors available
                                          // in this view.
  TTestView::TTestView(`TRect`& r ) :`TView`( r )
  {
  }
  void TTestView::draw()
  {
      TDrawBuffer buf;
      char textAttr, text[128];
      for(int i = 1; i <= 6; i++)         // Loop through palette
                                          // (6 entries.)
      {
          textAttr = getColor( i );       // Obtain attribute for
                                          // given index.
          sprintf(text, " This line uses index %02X, color is
                  %02X", i, textAttr);
          buf.moveStr(0, text, textAttr);      // Write to buffer.
          writeLine(0, i-1, size.x, i, buf);   // Write buffer to
                                               // view.
      }
  //
  // The last line of this view will not use the palettes at all,
  // but rather will print in Purple on Black, always.
  //
      buf.moveStr(0, "   This line bypasses the palettes!   ", 5);
      writeLine(0, 6, size.x, 7, buf);
  }
  //
  // getPalette: Create and return a palette with the given values.
  //
  TPalette& TTestView::getPalette() const
  {
      static`TPalette` palette( cpTestView, sizeof(cpTestView)-1 );
      return palette;
  }
  //
  //`TTestWindow`
  //
  #define cpTestWindow "\x40\x41\x42\x43\x44\x45"
  // SIX new colors!
  #define cpBlueWindow "\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
  // original palettes
  #define cpCyanWindow "\x10\x11\x12\x13\x14\x15\x16\x17"
  #define cpGrayWindow "\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F"
  TTestWindow::TTestWindow() :
      TWindow(`TRect`(0, 0,`TEST`_WIDTH,`TEST`_HEIGHT), 0,
               wnNoNumber),
      TWindowInit( initFrame )
  {
      TRect r = getExtent();
      r.grow(-2, -2);
      insert( new`TTestView`(r) );
      options |= ofCentered;
      flags = wfMove | wfClose;
  }
  //
  // getPalette: Like the system palette, windows employ more than
  // one possible set of colors: blue, cyan, and gray.  Only one //
  new set of colors has been defined though, so we simply //
  concatenate that set to each of the others by applying the //
  compiler feature that concatenates adjacent literal strings.  //
  This is why we use #defines instead of a  'const char *'.
  //
  TPalette& TTestWindow::getPalette() const
  {
      static TPalette blue( cpBlueWindow cpTestWindow,
                            sizeof( cpBlueWindow cpTestWindow )-1
                          );
      static TPalette cyan( cpCyanWindow cpTestWindow,
                            sizeof( cpCyanWindow cpTestWindow )-1
                          );
      static TPalette gray( cpGrayWindow cpTestWindow,
                            sizeof( cpGrayWindow cpTestWindow )-1
                          );
      static TPalette *palettes[] = { &blue, &cyan, &gray };
      return *(palettes[palette]);    // 'palette' is a member
                                      // variable that
                                      // represents the palette
                                      // being used
                                      // currently.
  }
```

```cpp
  //
  // CMDS.H - Various commands used in the message system (menus,
  // status line, dialog boxes).
  //
  #if !defined( _CMDS_H )
  #define _CMDS_H
  const unsigned short cmAbout            = 100;
  const unsigned short cmPaletteView      = 101;
  #endif  // _CMDS_H
  //
  // PALETTE.H - Example view with own palette.
  //
  //  Copyright (C) Borland International, 1991.
  //
  #if !defined( _PALETTE_H )
  #define _PALETTE_H
  //
  // class`TTestView`
  //      View that simply displays some text on the screen in a 
  //        random color.
  //
  // Member functions:
  //      TTestView - Constructor
  //      ~TTestView - Destructor
  //      draw - Display the text
  //      getPalette - To have a color to display the text in.
  //
  class TTestView : public TView
  {
  public:
      TTestView(TRect& r );
      virtual ~TTestView() {}
      virtual void draw();
      virtual`TPalette`& getPalette() const;
  private:
  };
  //
  // TTestWindow - provides encapsulation for TTestView, as well as
  // the ability to move the view around the screen and remove it
  // from the desktop with little coding (since TWindow's 
  // automatically call cmClose)
  //
  // Member functions:
  //      TTestWindow  - constructor
  //      getPalette  -
  //      sizeLimits  - so we can have a smaller than regulation
  //                   `TWindow`.
  //
  #define TEST_WIDTH   42
  #define TEST_HEIGHT  11
  class TTestWindow : public`TWindow`
  {
  public:
     `TTestWindow`();
      virtual ~TTestWindow() {}
      virtual TPalette& getPalette() const;
      virtual void sizeLimits(TPoint & min, TPoint & max )
      {
            min.x = max.x = TEST_WIDTH;
            min.y = max.y = TEST_HEIGHT;
      }
  };
  #endif  // _PALETTE_H
```

```cpp
  //
  // TEST.H - The class definition for TTestApp.
  //
  //
  // class TTestApp
  //      The application object, derived from the abstract class
  //     `TApplication`
  //
  // Member functions:
  //      TTestApp - Constructor
  //      initMenuBar - custom menu
  //      handleEvent - now handling menu events
  //      aboutDlg - creates and shows about box
  //
  class TTestApp : public`TApplication`
  {
  public:
      TTestApp();
      static`TMenuBar` *initMenuBar(`TRect` r );
      virtual void handleEvent(`TEvent`& event);
      virtual`TPalette`& getPalette() const;
  private:
      void aboutDlg();
      void paletteView();
  };
```

```cpp
  //
  //`TEST`.CPP - Main Test module for Turbo Vision example program.
  //
  #define Uses_TKeys
  #define Uses_TRect
  #define Uses_TEvent
  #define Uses_TMenuBar
  #define Uses_TMenu
  #define Uses_TMenuItem
  #define Uses_TDialog
  #define Uses_TButton
  #define Uses_TStaticText
  #define Uses_TDeskTop
  #define Uses_TApplication
  #define Uses_MsgBox
  #include 
  #include "cmds.h"       // User defined command set for this
                          // application
  #include "test.h"       // Application class definition
  #include "palette.h"    //`TTestWindow` class definition
  //
  //`TTestApp` - Constructor.
  //
  #define cpTestAppC  "\x3E\x2D\x72\x5F\x68\x4E"
  #define cpTestAppBW "\x07\x07\x0F\x70\x78\x7F"
  #define cpTestAppM  "\x07\x0F\x70\x09\x0F\x79"
  TTestApp::TTestApp() :
      TProgInit( initStatusLine, initMenuBar, initDeskTop )
  {
  }
  //
  // initMenuBar - Initialize the menu bar. It will be called by //         
        the
  virtual base TProgInit constructor.
  //
  TMenuBar *TTestApp::initMenuBar(TRect bounds )
  {
      bounds.b.y = bounds.a.y + 1;
      TMenuBar *mainMenu = new TMenuBar (bounds, new`TMenu`(
            *new TMenuItem("~A~bout...", cmAbout, kbAltA,
                           hcNoContext, 0,
           new TMenuItem("~P~alette", cmPaletteView, kbAltP,
                           hcNoContext, 0,
           new TMenuItem("E~x~it", cmQuit, kbAltX)))
          ));
      return( mainMenu );
  }
  //
  // handleEvent - Need to handle the event for the menu and status
  // line choices
  //
  void`TTestApp::handleEvent`(TEvent& event)
  {
     TApplication::handleEvent(event);
      switch(event.what)
      {
      case evCommand:             // handle COMMAND events.
          switch(event.message.command)
          {
          case cmAbout:           // Bring up the dialog box.
              aboutDlg();
              break;
          case cmPaletteView:     // Bring up palette example.
              paletteView();
              break;
          default:                // these events not handled.
              return;
          }
          break;
      default:                    // these events not handled.
          return;
      }
      clearEvent(event);          // Clear the events we did
                                  // handle.
  }
  //
  // getPalette: define a new system palette.  Notice that the //
  system palette must define palettes for three different types //
  of displays: color, BW, and mono.  Also, we are using Borland //
  C++ string concatenation in this function to join the system //
  default palette to our extension.
  //
  TPalette& TTestApp::getPalette() const
  {
      static TPalette
          newColor( cpColor cpTestAppC,
                    sizeof( cpColor cpTestAppC )-1 ),
          newBlackWhite( cpBlackWhite cpTestAppBW,
                         sizeof( cpBlackWhite cpTestAppBW)-1 ),
          newMonochrome( cpMonochrome cpTestAppM,
                         sizeof( cpMonochrome cpTestAppM)-1 );
      static TPalette *palettes[] =
          {
          &newColor,
          &newBlackWhite,
          &newMonochrome
          };
      return *(palettes[appPalette]); // 'appPalette' is a member
                                      // variable that
                                      // indicates which palette
                                      // (color, BW,
                                      // Mono) is being used.
  }
  //
  // aboutDlg - Creates a about dialog box and execute the dialog
  //             box.
  //
  void TTestApp::aboutDlg()
  {
     `TDialog` *aboutDlgBox = new`TDialog`(TRect(0, 0, 47, 13),
                                        "About");
      if( validView( aboutDlgBox ) )
      {
          aboutDlgBox->insert(
              newTStaticText(
                 TRect(2,1,45,9),
                  "\n\003PALETTE EXAMPLE\n \n"
                  "\003A Turbo Vision Demo\n \n"
                  "\003written by\n \n"
                  "\003Borland C++ Tech Support\n"
              ));
          aboutDlgBox->insert(
              newTButton(TRect(18,10,29,12), "OK", cmOK,
                           bfDefault)
              );
          aboutDlgBox->options |= ofCentered;     // Centered on
                                                  // the screen
          execView( aboutDlgBox );                // Bring up the
                                                  // box as modal
          destroy( aboutDlgBox );                 // Destroy the
                                                  // box
      }
  }
  void TTestApp::paletteView()
  {
     `TView` *view = new`TTestWindow`;
      if( validView( view ) )
          deskTop->insert( view );
  }
  int main()
  {
     `TTestApp` testApp;
      testApp.run();
      return 0;
  }
```

DISCLAIMER: You have the right to use this technical information
subject to the terms of the No-Nonsense License Statement that
you received with the Borland product to which this information
pertains.

Reference:


7/2/98 10:39:22 AM