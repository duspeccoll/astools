import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import make_digital_object
from make_digital_object import *
from asnake.client.web_client import ASnakeAuthError

item_dict = dict()
pad_width = 10
mag = magic.Magic(mime=True, magic_file=r"magic.mgc")
ignored_file_extensions = ('db', 'xml', '.DS_Store')


class MainFrame(ttk.Frame):
    def __init__(self, master):
        super(MainFrame, self).__init__(master)
        self.item_listbox = ItemListbox(self)
        self.item_listbox.grid(column=3, row=0, rowspan=3)
        self.item_listbox_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.item_listbox.yview)
        self.item_listbox_scrollbar.grid(column=4, row=0, rowspan=3, sticky='NS')
        self.item_listbox.configure(yscrollcommand=self.item_listbox_scrollbar.set)
        self.file_listbox = FileListbox(self, self.item_listbox)
        self.file_listbox.grid(column=0, row=0, rowspan=3)
        self.file_listbox_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.file_listbox.yview)
        self.file_listbox_scrollbar.grid(column=1, row=0, rowspan=3, sticky='NS')
        self.file_listbox.configure(yscrollcommand=self.file_listbox_scrollbar.set)
        self.file_info_frame = FileInfoFrame(self, self.file_listbox, self.item_listbox)
        self.file_info_frame.grid(column=0, row=3, sticky="W", padx=pad_width)
        self.item_info_frame = ItemInfoFrame(self, self.file_listbox, self.item_listbox)
        self.item_info_frame.grid(column=3, row=3)
        self.process_buttons_frame = ttk.Frame(self)
        self.process_buttons_frame.grid(column=2, row=1, padx=pad_width)
        self.process_button = ProcessButton(self.process_buttons_frame, self.file_listbox, self.item_listbox)
        self.process_button.grid(column=0, row=0, sticky='WE')
        self.process_all_button = ProcessAllButton(self.process_buttons_frame, self.file_listbox, self.item_listbox)
        self.process_all_button.grid(column=0, row=1, sticky='WE')


class FileInfoFrame(ttk.Frame):
    def __init__(self, master, file_listbox, item_listbox):
        super(FileInfoFrame, self).__init__(master)
        self.file_path_entry = FilePathEntry(self)
        self.file_path_entry.grid(column=0, row=0, columnspan=3)
        self.add_remove_buttons_frame = ttk.Frame(self)
        self.add_remove_buttons_frame.grid(column=0, row=1, sticky='W')
        self.add_button = AddButton(self.add_remove_buttons_frame, self.file_path_entry, file_listbox, item_listbox)
        self.add_button.grid(column=0, row=0, sticky='W')
        self.remove_button = RemoveButton(self.add_remove_buttons_frame, file_listbox, item_listbox)
        self.remove_button.grid(column=1, row=0, sticky='W')
        self.add_remove_buttons_frame.columnconfigure('all', pad=2)
        self.browse_button = BrowseButton(self.file_path_entry, self.file_path_entry)
        self.browse_button.grid(column=1, row=1, padx=pad_width)


class ItemInfoFrame(ttk.Frame):
    def __init__(self, master, file_listbox, item_listbox):
        super(ItemInfoFrame, self).__init__(master)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox
        self.caption_entry = CaptionEntry(self)
        self.caption_entry.grid(column=0, row=0, sticky='W')
        self.kaltura_entry = KalturaIDEntry(self)
        self.kaltura_entry.grid(column=0, row=1, sticky='W')
        self.set_caption_button = SetCaptionButton(self.caption_entry, self.caption_entry, self.kaltura_entry,
                                                   self.file_listbox, self.item_listbox)
        self.set_caption_button.grid(column=1, row=1, sticky='S', padx=pad_width)
        self.columnconfigure('all', pad=pad_width)
        self.rowconfigure('all', pad=pad_width)


class FilePathEntry(ttk.Frame):
    def __init__(self, master):
        super(FilePathEntry, self).__init__(master)
        self.label = tk.Label(self, text="File Path")
        self.label.grid(column=0, row=0, sticky="W")
        self.entry = tk.Entry(self, width=30)
        self.entry.grid(column=0, row=1, sticky="W")

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, 'end')
        self.entry.insert(9, value)


class KalturaIDEntry(ttk.Frame):
    def __init__(self, master):
        super(KalturaIDEntry, self).__init__(master)
        self.label = tk.Label(self, text="Kaltura ID")
        self.label.grid(column=0, row=0, sticky='W')
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky='W')

    def get(self):
        return self.entry.get()


class CaptionEntry(ttk.Frame):
    def __init__(self, master):
        super(CaptionEntry, self).__init__(master)
        self.label = tk.Label(self, text="Caption")
        self.label.grid(column=0, row=0, sticky='W')
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky='W')

    def get(self):
        return self.entry.get()


class AddButton(tk.Button):
    def __init__(self, master, file_path_entry, file_listbox, item_listbox):
        super(AddButton, self).__init__(master, text="Add", command=self._button_command)
        self.file_path_entry = file_path_entry
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        file_path = self.file_path_entry.get()
        if file_path != "":
            try:
                uri = check_uri_txt(file_path)
                print(uri)
                ref = check_digital_object(uri)
                tree_id = self.file_listbox.insert('', 'end', text=file_path)
                self.file_listbox.selection_set((tree_id,))
                find_items(ref, file_path, tree_id)
            except DigitalObjectException as e:
                print(e.message)
            self.file_path_entry.entry.delete(0, 'end')


class RemoveButton(tk.Button):
    def __init__(self, master, file_listbox, item_listbox):
        super(RemoveButton, self).__init__(master, text="Remove", command=self._button_command)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        self.file_listbox.delete_selection()


class BrowseButton(tk.Button):
    def __init__(self, master, file_path_entry):
        super(BrowseButton, self).__init__(master, text="Browse", command=self._button_command)
        self.file_path_entry = file_path_entry

    def _button_command(self):
        dirname = filedialog.askdirectory(initialdir=r"C:\Users\alice.tarrant\vbox_shared")
        self.file_path_entry.set(dirname)


class SetCaptionButton(tk.Button):
    def __init__(self, master, caption_entry, kaltura_entry, file_listbox, item_listbox):
        super(SetCaptionButton, self).__init__(master, text='Set', command=self._button_command)
        self.caption_entry = caption_entry
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox
        self.kaltura_entry = kaltura_entry

    def _button_command(self):
        file_selection = self.file_listbox.selection()
        file_index = file_selection[0]
        item_selection = self.item_listbox.selection()
        item_index = int(item_selection[0][1:]) - 1
        item_list = item_dict[file_index]
        item_list[item_index]['caption'] = self.caption_entry.get()
        item_list[item_index]['kaltura'] = self.kaltura_entry.get()
        self.caption_entry.entry.delete(0, 'end')
        self.kaltura_entry.entry.delete(0, 'end')
        display_items(self.file_listbox, self.item_listbox)


class ProcessButton(tk.Button):
    def __init__(self, master, file_listbox, item_listbox):
        super(ProcessButton, self).__init__(master, text="Process", command=self._button_command)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        file_selection = self.file_listbox.selection()[0]
        process_items(self.file_listbox, file_selection)


class ProcessAllButton(tk.Button):
    def __init__(self, master, file_listbox, item_listbox):
        super(ProcessAllButton, self).__init__(master, text='Process All', command=self._button_command)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        files = self.file_listbox.get_children()
        for f in files:
            process_items(self.file_listbox, f)


class FileListbox(ttk.Treeview):
    def __init__(self, master, item_listbox):
        super(FileListbox, self).__init__(master, selectmode='browse')
        self.item_listbox = item_listbox
        self.heading('#0', text='Path')
        self.column('#0', width=300)
        self.bind('<<TreeviewSelect>>', lambda e: display_items(self, self.item_listbox))

    def delete_selection(self):
        index = self.selection()
        for i in index:
            self.delete(i)

    def delete(self, index):
        super(FileListbox, self).delete((index,))
        del item_dict[index]
        display_items(self, self.item_listbox)


class ItemListbox(ttk.Treeview):
    def __init__(self, master):
        super(ItemListbox, self).__init__(master, columns=("kaltura", "caption"), selectmode='browse')
        self.heading('#0', text="Digital Object ID")
        self.heading('caption', text="Caption")
        self.heading('kaltura', text='Kaltura ID')
        self.column('#0', width=125)
        self.column('caption', width=200)
        self.column('kaltura', width=75)


def process_items(file_listbox, file_selection):
    item_list = item_dict[file_selection]
    for item in item_list:
        if item['type'] == 'new':
            data = item['data']
            if item['caption'] != '':
                data['children'][0]['file_versions'][0]['caption'] = item['caption']
            if item['kaltura'] != '':
                data['children'][0]['component_id'] = item['kaltura']
            post_json("{}/children".format(item['ref']), data)
        else:
            record = item['data']
            if item['caption'] != '':
                record['file_versions'][0]['caption'] = item['caption']
            if item['kaltura'] != '':
                record['component_id'] = item['kaltura']
            record['digital_object'] = {'ref': item['ref']}
            post_json(item['record_uri'], record)

    file_listbox.delete(file_selection)


def find_items(ref, path, tree_id):
    if tree_id not in item_dict:
        item_dict[tree_id] = list()

    print("Fetching digital object tree... ")
    tree = get_json("{}/tree".format(ref))

    print("Checking files... ")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
             and f != 'uri.txt' and f.split(".")[-1] not in ignored_file_extensions]
    if files:
        for file in files:
            path_to_file = os.path.join(path, file)
            try:
                file_format_name = mag.from_file(path_to_file).split("/")[-1]
            except magic.MagicException:
                print('MIME problem, setting file_format_name to blank', file=sys.stderr)
                continue
            print("\nProcessing {}... ".format(file))
            file_format_name = magic_to_as(file_format_name)

            file_size_bytes = os.path.getsize(path_to_file)

            tree_files = [child for child in tree['children'] if child['title'] == file]

            if tree_files:
                print("Checking for file-level metadata updates... ")
                for child in tree['children']:
                    # is this if statement redundunt considering the above list comprehension? -Alice
                    if child['title'] == file:
                        record = get_json(child['record_uri'])

                        if record['file_versions']:
                            version = record['file_versions'][0]
                            if 'file_uri' not in version or version['file_uri'] != file:
                                record['file_versions'][0]['file_uri'] = file
                            if 'file_format_name' not in version or version['file_format_name'] != file_format_name:
                                record['file_versions'][0]['file_format_name'] = file_format_name
                            if 'file_size_bytes' not in version or version['file_size_bytes'] != file_size_bytes:
                                record['file_versions'][0]['file_size_bytes'] = file_size_bytes
                        else:
                            record['file_versions'].append({
                                'jsonmodel_type': "file_version",
                                'file_uri': file,
                                'file_format_name': file_format_name,
                                'file_size_bytes': file_size_bytes,
                                'is_representative': True,
                            })
                        caption = ''
                        if 'caption' in record['file_versions'][0]:
                            caption = record['file_versions'][0]['caption']
                        item_dict[tree_id].append({'child': file, 'caption': caption, 'kaltura': '',
                                                   'data': record, 'type': 'old', 'ref': ref,
                                                   'record_uri': child['record_uri']})
            else:
                data = {
                    'jsonmodel_type': "digital_record_children",
                    'children': [{
                        'title': file,
                        'file_versions': [{
                            'jsonmodel_type': "file_version",
                            'file_uri': file,
                            'file_format_name': file_format_name,
                            'file_size_bytes': file_size_bytes,
                            'is_representative': True
                        }],
                        'digital_object': {'ref': ref}
                    }]
                }
                item_dict[tree_id].append({'child': file, 'caption': '', 'kaltura': '',
                                           'data': data, 'type': 'new', 'ref': ref})


def display_items(file_listbox, item_listbox):
    item_listbox.delete(*item_listbox.get_children())
    selection_id = file_listbox.selection()
    id_counter = 1
    if len(selection_id) > 0:
        for entry in item_dict[selection_id[0]]:
            item_listbox.insert('', 'end', text=entry['child'], iid='I' + str(id_counter),
                                values=(entry['kaltura'], entry['caption']))
            id_counter += 1
        if len(item_dict[selection_id[0]]) > 0:
            item_listbox.selection_set(('I1',))


def setup_gui(root):
    main_frame = MainFrame(root)
    main_frame.grid()


def test_scrollbars(file_listbox):
    for i in range(30):
        file_name = 'file' + str(i)
        file_listbox.insert('', 'end', text=file_name)


def main():
    try:
        make_digital_object.AS = ASpace()
    except ASnakeAuthError:
        print("Could not connect to ArchivesSpace.", file=sys.stderr)
    root = tk.Tk()
    root.title("Make Digital Object")
    root.configure(padx=pad_width, pady=pad_width)
    setup_gui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
