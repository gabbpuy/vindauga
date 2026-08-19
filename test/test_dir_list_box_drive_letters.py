# -*- coding: utf-8 -*-
import platform
from unittest import SkipTest, TestCase

from vindauga.widgets.dir_list_box import DirListBox


class Test_DirListBoxDriveLetters(TestCase):
    """Regression test for the Windows GetLogicalDriveStringsW buffer-size bug (see
    CODE_REVIEW.md item 7): GetLogicalDriveStringsW(0, None) returns the required buffer
    size in WCHARs, but the original __getDriveLetters allocated that many *bytes* via
    ctypes.create_string_buffer(size) -- half the space actually needed for a UTF-16 string
    -- so the real GetLogicalDriveStringsW call overflowed the undersized buffer and crashed
    the whole process with a native access violation, no Python traceback at all. Opening
    any file/directory dialog (ChangeDirDialog, FileDialog) on Windows hit this
    unconditionally, since DirListBox.__init__ calls this method every time.
    """

    def setUp(self):
        if platform.system().lower() != 'windows':
            raise SkipTest('GetLogicalDriveStringsW is Windows-only')

    def test_returns_well_formed_drive_letters_without_crashing(self):
        letters = DirListBox._DirListBox__getDriveLetters()

        self.assertTrue(letters, 'expected at least one drive letter on a real Windows machine')
        for entry in letters:
            # The trailing entry is legitimately '' -- GetLogicalDriveStringsW
            # double-NUL-terminates the list.
            self.assertTrue(entry == '' or (len(entry) == 3 and entry[1:] == ':\\'),
                            f'unexpected drive entry: {entry!r}')

    def test_change_dir_dialog_constructs_without_crashing(self):
        from vindauga.dialogs.change_dir_dialog import ChangeDirDialog, cmChangeDir

        dialog = ChangeDirDialog(0, cmChangeDir)

        self.assertIsNotNone(dialog)
