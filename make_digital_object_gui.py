import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import make_digital_object
from make_digital_object import *
from asnake.client.web_client import ASnakeAuthError
import threading
from asnake.client import ASnakeClient

item_dict = dict()
pad_width = 10
try:
    mag = magic.Magic(mime=True, magic_file=r"magic.mgc")
    pymagic_flag = True
except magic.MagicException:
    pymagic_flag = False
    print("default loaded")

ignored_file_extensions = ('db', 'xml', '.DS_Store')
log_text = None
root = None
process_lock = threading.Lock()


class MainFrame(ttk.Frame):
    def __init__(self, master):
        global log_text
        super(MainFrame, self).__init__(master)
        self.item_listbox = ItemListbox(self)
        self.item_listbox.grid(column=3, row=0, rowspan=3, sticky='NSWE')
        self.item_listbox_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.item_listbox.yview)
        self.item_listbox_scrollbar.grid(column=4, row=0, rowspan=3, sticky='NSW')
        self.item_listbox.configure(yscrollcommand=self.item_listbox_scrollbar.set)
        self.file_listbox = FileListbox(self, self.item_listbox)
        self.file_listbox.grid(column=0, row=0, rowspan=3, sticky='WENS')
        self.file_listbox_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.file_listbox.yview)
        self.file_listbox_scrollbar.grid(column=1, row=0, rowspan=3, sticky='NS')
        self.file_listbox.configure(yscrollcommand=self.file_listbox_scrollbar.set)

        self.file_info_frame = FileInfoFrame(self, self.file_listbox, self.item_listbox)
        self.file_info_frame.grid(column=0, row=3, sticky="W", padx=pad_width)
        self.item_info_frame = ItemInfoFrame(self, self.file_listbox, self.item_listbox)
        self.item_info_frame.grid(column=3, row=3, sticky="W")

        self.process_buttons_frame = ttk.Frame(self)
        self.process_buttons_frame.grid(column=2, row=1, padx=pad_width)
        self.process_button = ProcessButton(self.process_buttons_frame, self.file_listbox, self.item_listbox)
        self.process_button.grid(column=0, row=0, sticky='WE')
        self.process_all_button = ProcessAllButton(self.process_buttons_frame, self.file_listbox, self.item_listbox)
        self.process_all_button.grid(column=0, row=1, sticky='WE')

        self.log_frame = ttk.Frame(self)
        self.log_frame.grid(column=0, row=5, columnspan=5, sticky='NSWE', pady=pad_width)
        self.log_text = LogText(self.log_frame)
        log_text = self.log_text
        self.log_text.grid(column=0, row=0, sticky='WENS')
        self.log_text_scrollbar = ttk.Scrollbar(self.log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text_scrollbar.grid(column=1, row=0, sticky='WNS')
        self.log_text.configure(yscrollcommand=self.log_text_scrollbar.set)
        self.log_frame.grid_remove()
        self.show_log_button = ShowLogButton(self, log_frame=self.log_frame)
        self.show_log_button.grid(column=3, row=4, sticky="ES")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=2)

        self.rowconfigure(0, weight=2)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=2)

        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure('all', weight=1)


class FileInfoFrame(ttk.Frame):
    def __init__(self, master, file_listbox, item_listbox):
        super(FileInfoFrame, self).__init__(master)
        self.file_path_entry = FilePathEntry(self)
        self.file_path_entry.grid(column=0, row=0, columnspan=3)
        self.add_remove_buttons_frame = ttk.Frame(self)
        self.add_remove_buttons_frame.grid(column=0, row=1, sticky='W')
        self.add_button = AddButton(self.add_remove_buttons_frame, self.file_path_entry, file_listbox, item_listbox)
        self.add_button.grid(column=0, row=0, sticky='WE', padx=2, pady=2)
        self.remove_button = RemoveButton(self.add_remove_buttons_frame, file_listbox, item_listbox)
        self.remove_button.grid(column=1, row=0, sticky='W')
        self.batch_add_button = BatchAddButton(self.add_remove_buttons_frame, self.file_path_entry,
                                               file_listbox, item_listbox)
        self.batch_add_button.grid(column=0, row=1, sticky="WE", padx=2)
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
        global root
        add_thread = AddThread(self.file_path_entry, self.file_listbox, self.item_listbox)
        add_thread.start()
        disable_all_buttons(root)


class BatchAddButton(tk.Button):
    def __init__(self, master, file_path_entry, file_listbox, item_listbox):
        super(BatchAddButton, self).__init__(master, text='Batch Add', command=self._button_command)
        self.file_path_entry = file_path_entry
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        global root
        root.configure(cursor='wait')
        batch_add_thread = BatchAddThread(self.file_path_entry, self.file_listbox, self.item_listbox)
        batch_add_thread.start()


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
        dirname = filedialog.askdirectory()
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
        if self.caption_entry.get() != item_list[item_index]['caption'] or \
                self.kaltura_entry.get() != item_list[item_index]['kaltura']:
            item_list[item_index]['caption'] = self.caption_entry.get()
            item_list[item_index]['kaltura'] = self.kaltura_entry.get()
            if item_list[item_index]['type'] == 'old':
                item_list[item_index]['type'] = 'changed'
        self.caption_entry.entry.delete(0, 'end')
        self.kaltura_entry.entry.delete(0, 'end')
        display_items(self.file_listbox, self.item_listbox)


class ProcessButton(tk.Button):
    def __init__(self, master, file_listbox, item_listbox):
        super(ProcessButton, self).__init__(master, text="Process", command=self._button_command)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        process_thread = ProcessThread(self.file_listbox)
        process_thread.start()


class ProcessAllButton(tk.Button):
    def __init__(self, master, file_listbox, item_listbox):
        super(ProcessAllButton, self).__init__(master, text='Process All', command=self._button_command)
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def _button_command(self):
        process_all_thread = ProcessAllThread(self.file_listbox)
        process_all_thread.start()


class ShowLogButton(tk.Button):
    def __init__(self, master, log_frame):
        super(ShowLogButton, self).__init__(master, text='Show Log', command=self._button_command)
        self.hidden = True
        self.log_frame = log_frame

    def _button_command(self):
        if self.hidden:
            self.log_frame.grid()
            self.hidden = False
            self.configure(text='Hide Log')
        else:
            self.log_frame.grid_remove()
            self.hidden = True
            self.configure(text='Show Log')


class FileListbox(ttk.Treeview):
    def __init__(self, master, item_listbox):
        super(FileListbox, self).__init__(master, selectmode='browse')
        self.item_listbox = item_listbox
        self.heading('#0', text='Path')
        self.column('#0', width=300)
        self.bind('<<TreeviewSelect>>', lambda _: display_items(self, self.item_listbox))

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


class LogText(tk.Text):
    def __init__(self, master):
        super(LogText, self).__init__(master, height=20, state='disabled', width=110)


class AddThread(threading.Thread):
    def __init__(self, file_path_entry, file_listbox, item_listbox):
        super(AddThread, self).__init__()
        self.file_path_entry = file_path_entry
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def run(self):
        lock_process()

        file_path = self.file_path_entry.get()
        if file_path != "":
            add_file(file_path, self.file_listbox, self.item_listbox, self.file_path_entry)

        unlock_process()


class BatchAddThread(threading.Thread):
    def __init__(self, file_path_entry, file_listbox, item_listbox):
        super(BatchAddThread, self).__init__()
        self.file_path_entry = file_path_entry
        self.file_listbox = file_listbox
        self.item_listbox = item_listbox

    def run(self):
        lock_process()

        path = self.file_path_entry.get()
        if path != "":
            files = [f for f in os.scandir(path) if f.is_dir()]
            for file in files:
                add_file(file.path.replace("\\", '/'), self.file_listbox, self.item_listbox, self.file_path_entry)

        unlock_process()


class ProcessThread(threading.Thread):
    def __init__(self, file_listbox):
        super(ProcessThread, self).__init__()
        self.file_listbox = file_listbox

    def run(self):
        lock_process()

        file_selection = self.file_listbox.selection()[0]
        process_items(self.file_listbox, file_selection)

        unlock_process()


class ProcessAllThread(threading.Thread):
    def __init__(self, file_listbox):
        super(ProcessAllThread, self).__init__()
        self.file_listbox = file_listbox

    def run(self):
        lock_process()

        files = self.file_listbox.get_children()
        for f in files:
            process_items(self.file_listbox, f)

        unlock_process()


class CredentialsWindow(tk.Tk):
    def __init__(self):
        global root
        super(CredentialsWindow, self).__init__()

        self.title('Credentials')

        self.baseurl_label = ttk.Label(self, text="Base Archivesspace URL")
        self.baseurl_label.grid(column=0, row=0)
        self.baseurl_entry = ttk.Entry(self)
        self.baseurl_entry.grid(column=0, row=1)

        self.username_label = ttk.Label(self, text="Username")
        self.username_label.grid(column=0, row=2)
        self.username_entry = ttk.Entry(self)
        self.username_entry.grid(column=0, row=3)

        self.password_label = ttk.Label(self, text="Password")
        self.password_label.grid(column=0, row=4)
        self.password_entry = ttk.Entry(self)
        self.password_entry.grid(column=0, row=5)

        self.confirm_button = ttk.Button(text="Confirm", command=self._confirm_button_command)
        self.confirm_button.grid(column=0, row=6)

        self.bind('<Return>', self._confirm_button_command)

        self.mainloop()

    def _confirm_button_command(self, _):
        global root
        try:
            make_digital_object.AS = ASpace(baseurl=self.baseurl_entry.get(),
                                            username=self.username_entry.get(),
                                            password=self.password_entry.get())

            with open('credentials.json', mode='w') as credentials:
                data = {'baseurl': self.baseurl_entry.get(),
                        'username': self.username_entry.get(),
                        'password': self.password_entry.get()}
                json.dump(data, credentials)
                self.destroy()

        except ASnakeAuthError:
            self.baseurl_entry.delete(0, 'end')
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')


def add_file(file_path, file_listbox, item_listbox, file_path_entry):
    try:
        uri = check_uri_txt(file_path)
        as_log(uri)
        ref = check_digital_object(uri)
        tree_id = file_listbox.insert('', 'end', text=file_path)
        find_items(ref, file_path, tree_id)
        display_items(file_listbox, item_listbox)
        file_listbox.see(tree_id)
        file_listbox.selection_set((tree_id,))
    except DigitalObjectException as exc:
        as_log(exc.message)
    file_path_entry.entry.delete(0, 'end')


def gui_as_log(message=''):
    log_text.configure(state='normal')
    log_text.insert('end', message + '\n')
    log_text.see('end')
    log_text.configure(state='disabled')


make_digital_object.as_log = gui_as_log
as_log = gui_as_log


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
        elif item['type'] == 'changed':
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

    as_log("Fetching digital object tree... ")
    tree = get_json("{}/tree".format(ref))

    as_log("Checking files... ")
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
             and f != 'uri.txt' and f.split(".")[-1] not in ignored_file_extensions]
    if files:
        for file in files:
            path_to_file = os.path.join(path, file)
            try:
                file_format_name = magic_from_file(path_to_file).split("/")[-1]
            except magic.MagicException:
                print('MIME problem, setting file_format_name to blank', file=sys.stderr)
                continue
            as_log("\nProcessing {}... ".format(file))
            file_format_name = magic_to_as(file_format_name)

            file_size_bytes = os.path.getsize(path_to_file)

            tree_files = [child for child in tree['children'] if child['title'] == file]

            if tree_files:
                as_log("Checking for file-level metadata updates... ")
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


def magic_from_file(path_to_file):
    if pymagic_flag:
        return mag.from_file(path_to_file)
    else:
        return magic.from_file(path_to_file, mime=True)


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


def setup_gui(toplevel):
    main_frame = MainFrame(toplevel)
    main_frame.grid(column=0, row=0, sticky='WENS', padx=pad_width, pady=pad_width)
    toplevel.columnconfigure(0, weight=1)
    toplevel.rowconfigure(0, weight=1)


def disable_all_buttons(widget, enable=False):
    for c in widget.winfo_children():
        if c.winfo_class() == "Button":
            if enable:
                c.configure(state='normal')
            else:
                c.configure(state='disabled')
        disable_all_buttons(c, enable=enable)


def lock_process():
    global root
    process_lock.acquire()
    root.configure(cursor='wait')
    disable_all_buttons(root)


def unlock_process():
    global root
    process_lock.release()
    root.configure(cursor='')
    disable_all_buttons(root, True)


def check_credentials():
    try:
        with open('credentials.json') as credentials:
            data = json.load(credentials)
            make_digital_object.AS = ASpace(baseurl=data['baseurl'],
                                            username=data['username'],
                                            password=data['password'])
    except FileNotFoundError:
        CredentialsWindow()


def main():
    global root

    check_credentials()

    root = tk.Tk()
    root.title("Make Digital Object Utility")
    root.iconbitmap('favicon.ico')
    setup_gui(root)

    root.mainloop()


if __name__ == "__main__":
    main()
