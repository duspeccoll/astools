import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import make_digital_object
from make_digital_object import *
from asnake.client.web_client import ASnakeAuthError


class MainFrame(ttk.Frame):
    def __init__(self, master):
        super(MainFrame, self).__init__(master)
        self.file_listbox = FileListbox(self)
        self.file_listbox.grid(column=0, row=0)
        file_info_frame = FileInfoFrame(self, self.file_listbox)
        file_info_frame.grid(column=0, row=1, sticky="W")
        item_listbox = tk.Listbox(self)
        item_listbox.grid(column=1, row=0)


class FileInfoFrame(ttk.Frame):
    def __init__(self, master, file_listbox):
        super(FileInfoFrame, self).__init__(master)
        self.file_path_entry = FilePathEntry(self)
        self.file_path_entry.grid(column=0, row=0, sticky="W")
        self.kaltura_id_entry = KalturaIDEntry(self)
        self.kaltura_id_entry.grid(column=0, row=1, sticky="W")
        self.add_button = AddButton(self, self.file_path_entry, self.kaltura_id_entry, file_listbox)
        self.add_button.grid(column=1, row=0, sticky="W")
        self.remove_button = RemoveButton(self, file_listbox)
        self.remove_button.grid(column=1, row=1, sticky="W")
        self.browse_button = BrowseButton(self, self.file_path_entry)
        self.browse_button.grid(column=2, row=0)
        self.process_button = ProcessButton(self)
        self.process_button.grid(column=2, row=1, sticky="W")


class FilePathEntry(ttk.Frame):
    def __init__(self, master):
        super(FilePathEntry, self).__init__(master)
        self.label = tk.Label(self, text="File Path")
        self.label.grid(column=0, row=0, sticky="W")
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky="W")

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, 'end')
        self.entry.insert(9, value)


class KalturaIDEntry(ttk.Frame):
    def __init__(self, master):
        super(KalturaIDEntry, self).__init__(master)
        self.label = tk.Label(self, text="Kaltura ID (Optional)")
        self.label.grid(column=0, row=0, sticky='W')
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky='W')

    def get(self):
        return self.entry.get()


class AddButton(tk.Button):
    def __init__(self, master, file_path_entry, kaltura_id_entry, file_listbox):
        super(AddButton, self).__init__(master, text="Add", command=self._button_command)
        self.file_path_entry = file_path_entry
        self.kaltura_id_entry = kaltura_id_entry
        self.file_listbox = file_listbox

    def _button_command(self):
        file_path = self.file_path_entry.get()
        kaltura_id = self.kaltura_id_entry.get()
        if file_path != "":
            self.file_listbox.insert('', 'end', text=file_path, values=(kaltura_id,))
            uri = check_uri_txt(file_path)
            print(uri)
            ref = check_digital_object(uri)


class RemoveButton(tk.Button):
    def __init__(self, master, file_listbox):
        super(RemoveButton, self).__init__(master, text="Remove", command=self._button_command)
        self.file_listbox = file_listbox

    def _button_command(self):
        index = self.file_listbox.selection()
        if len(index) > 0:
            self.file_listbox.delete(index)
            
            
class BrowseButton(tk.Button):
    def __init__(self, master, file_path_entry):
        super(BrowseButton, self).__init__(master, text="Browse", command=self._button_command)
        self.file_path_entry = file_path_entry

    def _button_command(self):
        dirname = filedialog.askdirectory(initialdir=r"/media/sf_vbox_shared")
        self.file_path_entry.set(dirname)


class ProcessButton(tk.Button):
    def __init__(self, master):
        super(ProcessButton, self).__init__(master, text="Process")


class FileListbox(ttk.Treeview):
    def __init__(self, master):
        super(FileListbox, self).__init__(master, columns=("kaltura_id",))
        self.heading('kaltura_id', text="Kaltura ID")


class ItemListbox(ttk.Treeview):
    def __init__(self, master):
        super(ItemListbox, self).__init__(master, columns=("caption",))
        self.heading('caption', text="Caption")


def setup_gui(root):
    main_frame = MainFrame(root)
    main_frame.grid()


def main():
    try:
        make_digital_object.AS = ASpace()
    except ASnakeAuthError:
        print("Could not connect to ArchivesSpace.", file=sys.stderr)
    root = tk.Tk()
    root.title("Make Digital Object")
    setup_gui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
