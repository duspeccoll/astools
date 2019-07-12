import tkinter as tk
from tkinter import ttk


class MainFrame(ttk.Frame):
    def __init__(self, master):
        super(MainFrame, self).__init__(master)
        self.file_listbox = FileListbox(self)
        self.file_listbox.grid(column=0, row=0)
        file_info_frame = FileInfoFrame(self)
        file_info_frame.grid(column=0, row=1, sticky="W")
        item_listbox = tk.Listbox(self)
        item_listbox.grid(column=1, row=0)


class FileInfoFrame(ttk.Frame):
    def __init__(self, master):
        super(FileInfoFrame, self).__init__(master)
        self.file_path_entry = FilePathEntry(self)
        self.file_path_entry.grid(column=0, row=0, sticky="W")
        self.kaltura_id_entry = KalturaIDEntry(self)
        self.kaltura_id_entry.grid(column=0, row=1, sticky="W")
        self.add_button = AddButton(self)
        self.add_button.grid(column=1, row=0, sticky="SW")
        self.process_button = ProcessButton(self)
        self.process_button.grid(column=1, row=1, sticky="SW")


class FilePathEntry(ttk.Frame):
    def __init__(self, master):
        super(FilePathEntry, self).__init__(master)
        self.label = tk.Label(self, text="File Path")
        self.label.grid(column=0, row=0, sticky="W")
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky="W")


class KalturaIDEntry(ttk.Frame):
    def __init__(self, master):
        super(KalturaIDEntry, self).__init__(master)
        self.label = tk.Label(self, text="Kaltura ID (Optional)")
        self.label.grid(column=0, row=0, sticky='W')
        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=1, sticky='W')


class AddButton(tk.Button):
    def __init__(self, master):
        super(AddButton, self).__init__(master, text="Add")


class RemoveButton(tk.Button):
    def __init__(self, master):
        super(RemoveButton, self).__init__(master, text="Remove")


class ProcessButton(tk.Button):
    def __init__(self, master):
        super(ProcessButton, self).__init__(master, text="Process")


class FileListbox(ttk.Treeview):
    def __init__(self, master):
        super(FileListbox, self).__init__(master, columns=("File Path", "Kaltura ID"))


def setup_gui(root):
    main_frame = MainFrame(root)
    main_frame.grid()


def main():
    root = tk.Tk()
    root.title("Make Digital Object")
    setup_gui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
