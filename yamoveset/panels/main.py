import wx
from wx.dataview import TreeListCtrl, EVT_TREELIST_ITEM_CONTEXT_MENU, TL_MULTIPLE
from wx.lib.dialogs import MultiMessageDialog
from pubsub import pub

from collections import defaultdict
import pickle

from yamoveset import KNOWN_ENTRIES, BLACKLISTED_WORDS
from yamoveset.dlg.changed import ChangedDialog
from pyxenoverse.gui.file_drop_target import FileDropTarget
from pyxenoverse.bac.sub_entry import ITEM_TYPES
from pyxenoverse.bac.entry import Entry
from pyxenoverse.bac.types.animation import Animation
from pyxenoverse.bac.types.camera import Camera
from pyxenoverse.bac.types.hitbox import Hitbox
from pyxenoverse.bdm.entry import Entry as BdmEntry
from pyxenoverse.ean.animation import Animation as EanAnimation


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.code = ''
        self.bac = None
        self.bdm = None
        self.ean = None
        self.cam_ean = None
        self.dirname = ''
        self.parent = parent
        self.links = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

        # Name
        self.name = wx.StaticText(self, -1, '(No file loaded)')
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.name.SetFont(self.font)

        # Buttons
        self.open = wx.Button(self, wx.ID_OPEN, "Load")
        self.save = wx.Button(self, wx.ID_SAVE, "Save")
        self.save.Disable()
        self.paste = wx.Button(self, wx.ID_PASTE, "Paste")
        self.paste.Disable()
        self.add = wx.Button(self, wx.ID_ADD, "Add Copy")
        self.add.Disable()

        # Entry List
        self.entry_list = TreeListCtrl(self, style=TL_MULTIPLE)
        self.entry_list.AppendColumn("BAC Entry")
        self.entry_list.Bind(EVT_TREELIST_ITEM_CONTEXT_MENU, self.on_right_click)

        # Bind
        self.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.on_paste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_BUTTON, self.on_add, id=wx.ID_ADD)
        self.Bind(wx.EVT_MENU, self.on_paste, id=wx.ID_PASTE)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('v'), wx.ID_PASTE),
        ])
        self.entry_list.SetAcceleratorTable(accelerator_table)
        self.SetDropTarget(FileDropTarget(self, "load_main_moveset"))
        pub.subscribe(self.on_enable_paste, 'enable_paste')


        # Button Sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.open)
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.save)
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.paste)
        button_sizer.AddSpacer(5)
        button_sizer.Add(self.add)

        # Use some sizers to see layout options
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.name, 0, wx.CENTER)
        sizer.Add(button_sizer)
        sizer.Add(self.entry_list, 1, wx.ALL | wx.EXPAND, 10)

        # Layout sizers
        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def on_open(self, _):
        pub.sendMessage('open_main_moveset')

    def on_save(self, _):
        pub.sendMessage('save_moveset')

    def build_tree(self):
        self.entry_list.DeleteAllItems()
        root = self.entry_list.GetRootItem()
        for i, entry in enumerate(self.bac.entries):
            if not entry.sub_entries:
                continue
            self.entry_list.AppendItem(
                root, f'{entry.index}: {KNOWN_ENTRIES.get(entry.index, "Unknown")}', data=entry)
        self.save.Enable()
        self.paste.Disable()
        self.add.Disable()

    def on_right_click(self, _):
        selected = self.entry_list.GetSelections()
        if not selected:
            return
        menu = wx.Menu()
        paste = menu.Append(wx.ID_PASTE)
        paste.Enable(self.parent.copied is not None)
        self.PopupMenu(menu)
        menu.Destroy()

    def find_next_available_index(self, item_type):
        if item_type == Animation:
            return len(self.ean.animations)
        elif item_type == Hitbox:
            return max([entry.id for entry in self.bdm.entries]) + 1
        elif item_type == Camera:
            return len(self.cam_ean.animations)
        else:
            raise(TypeError(f'Unsupported type: {item_type.__name__}'))

    def find_conflict(self, item_type, entry_pair, depend_value, selected_data, value):
        if value in list(self.links[item_type][entry_pair][depend_value].values()):
            return True
        for entry in self.bac.entries:
            # Skip this entry if its already in the selected data
            if entry in selected_data:
                continue
            for sub_entry in entry.sub_entries:
                # Skip if this is not the type we want
                if item_type != ITEM_TYPES[sub_entry.type]:
                    continue
                for item in sub_entry.items:
                    if item[entry_pair[1]] == depend_value and item[entry_pair[0]] == value:
                        return True
        return False

    def create_new_index(self, item_type):
        new_value = self.find_next_available_index(item_type)
        if item_type == Animation:
            animation = EanAnimation(self.ean)
            self.ean.animations.append(animation)
        elif item_type == Hitbox:
            self.bdm.entries.append(BdmEntry(entry_id=new_value))
        elif item_type == Camera:
            self.cam_ean.animations.append(EanAnimation(self.cam_ean))
        else:
            raise(TypeError(f'Unsupported type: {item_type.__name__}'))
        return new_value

    def file_not_found_dialog(self, filename):
        with wx.MessageDialog(
                self, f'{filename} was not opened. Please add it and reload the moveset', 'Error') as dlg:
            dlg.ShowModal()

    def invalid_index_dialog(self, filename, index):
        with wx.MessageDialog(self, f'{filename} does not contain index {index}', 'Error') as dlg:
            dlg.ShowModal()

    def copy_index(self, item_type, old_value, new_value):
        new_code = self.code
        old_code = self.parent.side_panel.code
        if item_type == Animation:
            try:
                animation = self.ean.animations[new_value]
            except IndexError:
                self.invalid_index_dialog(f'{new_code}.ean', new_value)
                return False
            try:
                animation.paste(self.parent.side_panel.ean.animations[old_value], keep_name=True)
            except IndexError:
                self.invalid_index_dialog(f'{old_code}.ean', old_value)
                return False

        elif item_type == Hitbox:
            if not self.bdm:
                self.file_not_found_dialog(f'{new_code}_PLAYER.bdm')
                return False

            if not self.parent.side_panel.bdm:
                self.file_not_found_dialog(f'{old_code}_PLAYER.bdm')
                return False
            try:
                entry = [entry for entry in self.bdm.entries if entry.id == new_value][0]
            except IndexError:
                self.invalid_index_dialog(f'{new_code}_PLAYER.bdm', new_value)
                return False
            try:
                old_entry = [entry for entry in self.parent.side_panel.bdm.entries if entry.id == old_value][0]
            except IndexError:
                self.invalid_index_dialog(f'{old_code}_PLAYER.bdm', old_value)
                return False
            entry.paste(old_entry)
        elif item_type == Camera:
            if not self.cam_ean:
                self.file_not_found_dialog(f'{new_code}.cam.ean')
                return False
            if not self.parent.side_panel.cam_ean:
                self.file_not_found_dialog(f'{old_code}.cam.ean')
                return False
            try:
                camera = self.cam_ean.animations[new_value]
            except IndexError:
                self.invalid_index_dialog(f'{new_code}.cam.ean', new_value)
                return False
            try:
                camera.paste(self.parent.side_panel.cam_ean.animations[old_value], keep_name=True)
            except IndexError:
                self.invalid_index_dialog(f'{old_code}.cam.ean', old_value)
                return False
        else:
            raise(TypeError(f'Unsupported type: {item_type.__name__}'))
        return True

    def changed_value_message(self, entry_index, changed_values, item_type, old_value, new_value, new=True):
        old_string = str(old_value)
        new_string = str(new_value)
        if item_type == Animation:
            old_string += f' ({self.parent.side_panel.ean.animations[old_value].name})'
            new_string += f' ({"*new*" if new else self.ean.animations[new_value].name})'
        changed_values[item_type].append((f'[{entry_index}]', new_string, old_string))

    def get_changed_values(
            self, changed_values, item_type, entry_pair, depend_value, entry_values, selected_val, selected_data):
        entry_index = selected_val[0]
        selected_val = selected_val[1]
        entry_name = KNOWN_ENTRIES.get(entry_index, 'Unknown')
        n = 0
        for old_value in entry_values:
            # Continue if we already have a link
            old_animation_name = self.parent.side_panel.ean.animations[old_value].name \
                if item_type == Animation and old_value < len(self.parent.side_panel.ean.animations) else ''
            if item_type == Animation and any(
                    word in old_animation_name for word in BLACKLISTED_WORDS) \
                    and not old_animation_name.endswith(entry_name):
                continue
            if old_value in self.links[item_type][entry_pair][depend_value]:
                new_value = self.links[item_type][entry_pair][depend_value][old_value]
                # if (old_value, new_value) in list(zip(*changed_values[item_type])):
                self.changed_value_message(entry_index, changed_values, item_type, old_value, new_value, False)
                continue
            # If the current n is bigger then the selected values or selected values doesn't exist
            if item_type in selected_val and entry_pair in selected_val[item_type]:
                if n >= len(selected_val[item_type][entry_pair][depend_value]):
                    new_value = self.create_new_index(item_type)
                    self.changed_value_message(entry_index, changed_values, item_type, old_value, new_value)
                else:
                    while n < len(selected_val[item_type][entry_pair][depend_value]):
                        new_value = list(selected_val[item_type][entry_pair][depend_value])[n]
                        new_animation_name = self.ean.animations[new_value].name \
                            if item_type == Animation and new_value < len(self.ean.animations) else ''
                        if item_type != Animation or not any(
                                word in new_animation_name for word in BLACKLISTED_WORDS) \
                                or new_animation_name.endswith(entry_name):
                            if not new_animation_name.endswith(entry_name) and self.find_conflict(
                                    item_type, entry_pair, depend_value, selected_data, new_value):
                                new_value = self.create_new_index(item_type)
                                self.changed_value_message(
                                    entry_index, changed_values, item_type, old_value, new_value)
                            else:
                                self.changed_value_message(
                                    entry_index, changed_values, item_type, old_value, new_value, False)
                            break
                        n += 1
                    else:
                        new_value = self.create_new_index(item_type)
                        self.changed_value_message(
                            entry_index, changed_values, item_type, old_value, new_value)
            else:
                new_value = self.create_new_index(item_type)
                self.changed_value_message(entry_index, changed_values, item_type, old_value, new_value)

            # Copy EAN/BDM entries
            if not self.copy_index(item_type, old_value, new_value):
                return False
            self.links[item_type][entry_pair][depend_value][old_value] = new_value
            n += 1
        return True

    def on_enable_paste(self, enabled):
        self.paste.Enable(enabled)
        self.add.Enable(enabled)

    def on_paste(self, _):
        if not self.parent.copied:
            return

        selected = self.entry_list.GetSelections()
        if not selected:
            return

        copied = pickle.loads(self.parent.copied)

        # Cut length of selected to match copied
        copy_length = len(copied)
        selected_length = len(selected)
        if selected_length > copy_length:
            for item in selected[copy_length:]:
                self.entry_list.Unselect(item)
            selected = selected[:copy_length]
        item = selected[-1]
        self.entry_list.Select(item)

        # Increase length to match selected
        for n in range(copy_length - selected_length):
            item = self.entry_list.GetNextItem(item)
            if not item.IsOk():
                with wx.MessageDialog(self, f'Not enough entries to paste over. Expected {copy_length}') as dlg:
                    dlg.ShowModal()
                    return
            self.entry_list.Select(item)
            selected.append(item)

        selected_data = [self.entry_list.GetItemData(item) for item in selected]

        # Warn about changing multiple entries
        if len(copied) > 1:
            msg = ''
            for n, copied_data in enumerate(copied):
                msg += f' * {selected_data[n].index} -> {copied_data.index}\n'
            with MultiMessageDialog(self, 'Are you sure you want to replace the following entries?',
                                    'Warning', msg, wx.YES | wx.NO) as dlg:
                if dlg.ShowModal() != wx.ID_YES:
                    return

        # Paste entries
        selected_values = []
        copied_values = []
        changed_values = defaultdict(list)

        for n, copied_data in enumerate(copied):
            selected_values.append((selected_data[n].index, selected_data[n].get_static_values()))
            copied_values.append(copied_data.get_static_values())

        for selected_val, copied_val in zip(selected_values, copied_values):
            # Example:
            # Item type: Animation
            # entry: Index
            # dependency: Type
            # depend_value: 5
            # entry_values: {1, 2, 3}
            for item_type, v1 in copied_val.items():
                if item_type not in [Animation, Hitbox, Camera]:
                    continue
                for entry_pair, v2 in v1.items():
                    for depend_value, entry_values in v2.items():
                        # Skip if dependency isn't a character
                        if item_type.dependencies[entry_pair][depend_value] != 'Character':
                            continue
                        if not self.get_changed_values(
                                changed_values, item_type, entry_pair, depend_value, entry_values,
                                selected_val, selected_data):
                            return

        # Finally copy BAC Entries
        for n, copied_data in enumerate(copied):
            entry = self.entry_list.GetItemData(selected[n])
            entry.paste(copied_data, self.links)

        # Display message
        msg = f'Pasted {len(copied)} entry(s)'
        pub.sendMessage('set_status_bar', text=msg)
        with ChangedDialog(self, changed_values) as dlg:
            dlg.ShowModal()

        # changed_msg = ''
        # for item_type, values in changed_values.items():
        #     if item_type == Animation:
        #         changed_msg += f'{self.code}.ean -> {self.parent.side_panel.code}.ean\n'
        #     elif item_type == Hitbox:
        #         changed_msg += f'{self.code}_PLAYER.bdm -> {self.parent.side_panel.code}_PLAYER.bdm\n'
        #     elif item_type == Camera:
        #         changed_msg += f'{self.code}.cam.ean -> {self.parent.side_panel.code}.cam.ean\n'
        #     else:
        #         raise(TypeError(f'Unsupported type: {item_type.__name__}'))
        #     changed_msg += ''.join(sorted(list(zip(*values))[1]))

        # with MultiMessageDialog(
        #         self, 'The following entries in the listed files have been changed:', msg, changed_msg, wx.OK) as dlg:
        #     dlg.ShowModal()

    def on_add(self, _):
        if not self.parent.copied:
            with wx.MessageDialog(self, f'No entries are copied from the right panel to Add') as dlg:
                dlg.ShowModal()
            return

        copied = pickle.loads(self.parent.copied)

        # Paste entries
        changed_values = defaultdict(list)
        index_start = len(self.bac.entries)

        # same code as in on_paste(), but it compares to the added entry (i really have no idea why this works..)
        for n, copy in enumerate(copied):
            copied_val = copy.get_static_values()
            for item_type, v1 in copied_val.items():
                if item_type not in [Animation, Hitbox, Camera]:
                    continue
                for entry_pair, v2 in v1.items():
                    for depend_value, entry_values in v2.items():
                        # Skip if dependency isn't a character
                        if item_type.dependencies[entry_pair][depend_value] != 'Character':
                            continue

                        for old_value in entry_values:
                            # If we have a link already, use that
                            if old_value in self.links[item_type][entry_pair][depend_value]:
                                new_value = self.links[item_type][entry_pair][depend_value][old_value]
                                # if (old_value, new_value) in list(zip(*changed_values[item_type])):
                                self.changed_value_message(index_start + n, changed_values, item_type, old_value, new_value, False)
                                continue
                            # Otherwise, just create a new one
                            new_value = self.create_new_index(item_type)
                            self.changed_value_message(index_start + n, changed_values, item_type, old_value, new_value)

                            # Copy EAN/BDM entries
                            if not self.copy_index(item_type, old_value, new_value):
                                return
                            self.links[item_type][entry_pair][depend_value][old_value] = new_value

        # Add BAC Entry
        for n, copied_data in enumerate(copied):
            # add new entries to the end so we don't override important CMN entries
            new_entry = Entry(self.bac, index_start + n)
            root = self.entry_list.GetRootItem()
            new_entry.paste(copied_data, self.links)
            self.bac.entries.append(new_entry)
            new_item = self.entry_list.AppendItem(
                root, f'{new_entry.index}: {KNOWN_ENTRIES.get(new_entry.index, "Unknown")}', data=new_entry)
            self.entry_list.Select(new_item)

        # Display message
        msg = f'Added {len(copied)} entry(s) at index {index_start}'
        pub.sendMessage('set_status_bar', text=msg)
        with ChangedDialog(self, changed_values) as dlg:
            dlg.ShowModal()
