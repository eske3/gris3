from gris3 import hotkeyManager

HOTKEY_TABLE = (
    (
        'grsSelectToolMM',
        'from gris3 import markingMenus; markingMenus.selectToolCommand(%s);',
        'Set tool to Select Tool with option.',
        'GrisMarkingMenu',
    ),
    (
        'grsAttributeEditorMM',
        'from gris3 import markingMenus; markingMenus.showAttributeEditor(%s);',
        'Show AE window or menu to open any general window.',
        'GrisMarkingMenu',
    ),
   (
        'grsParentAndPrefMM',
        'from gris3 import markingMenus; markingMenus.parentAndPreference(%s);',
        'Parent or menu to open any preference window.',
        'GrisMarkingMenu',
    ),
   (
        'grsObjectDisplayMM',
        'from gris3 import markingMenus; markingMenus.showDisplayMenu(%s);',
        'Reset display or menu to change any display.',
        'GrisMarkingMenu',
    ),
    (
        'grsModelDisplayMM',
        'from gris3 import markingMenus; markingMenus.showModelDisplayMenu(%s);',
        'Isolate selected or menu to change any model display.',
        'GrisMarkingMenu',
    ),
    (
        'grsCopyMM',
        'from gris3 import markingMenus; markingMenus.showCopyMenu(%s);',
        'Show marking menu to copy any things.',
        'GrisMarkingMenu',
    ),
    (
        'grsPasteMM',
        'from gris3 import markingMenus; markingMenus.showPasteMenu(%s);',
        'Show marking menu to paste any things.',
        'GrisMarkingMenu',
    ),
)

HOTKEY_TABLE = [
    hotkeyManager.Hotkey('_'.join((rc, act)), c%i, '%s(%s)' % (ann, act), cat)
    for rc, c, ann, cat in HOTKEY_TABLE
    for i, act in enumerate(('Press', 'Release'))
]
