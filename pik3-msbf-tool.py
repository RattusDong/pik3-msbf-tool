import sys
import struct
import json

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from src.constants import *
from src.node_table import NodeTable
from src.common import *
import src.msbf as msbf
import src.editor as editor


label_dict = dict()

def setup_window():

    global dark_mode
    root = tk.Tk()
    root.title("Pikmin 3 MSBF Tool")

    root.geometry(f'{WIN_WIDTH}x{WIN_HEIGHT}')
    root.minsize(600, 300)

    root.columnconfigure(0,weight=2)
    root.columnconfigure(1,weight=3)

    root.rowconfigure(0, weight=2)
    root.rowconfigure(1, weight=7)


    style = ttk.Style()
    style.configure("Treeview.Heading", font=("TkFixedFont", 10, "bold"))
    style.configure("TLabelframe.Label", font=("TkFixedFont", 10, "bold"))

    if sys.platform == "win32":
        root.iconbitmap('./assets/icon.ico')
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    else:
        photo = tk.PhotoImage(file='./assets/icon.png')
        root.iconphoto(False, photo)
        root.icon_ref = photo
        if sys.platform == "darwin":
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            if result.stdout.strip() == "Dark": dark_mode = True

    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)

    if sys.platform == "darwin":
        file_menu.add_command(label="Open", command=open_file, accelerator="Cmd+O")
        file_menu.add_command(label="Save", command=save_file, accelerator="Cmd+S")
        root.bind("<Command-o>", lambda e: open_file())
        root.bind("<Command-s>", lambda e: save_file())
    else:
        file_menu.add_command(label="Open", command=open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=save_file, accelerator="Ctrl+S")
        root.bind("<Control-o>", lambda e: open_file())
        root.bind("<Control-s>", lambda e: save_file())

    menubar.add_cascade(label="File", menu=file_menu)
    root.config(menu=menubar)


    # frame row 0 col 0
    frame = ttk.Labelframe(root, text="Flowcharts", labelanchor="n")

    global flowchart_list
    flowchart_list = tk.Listbox(frame, height=6, selectmode=tk.SINGLE)
    flowchart_list.bind('<<ListboxSelect>>', flowchart_list_select)
    flowchart_list.pack(padx=6, pady=6, expand=True, fill=tk.BOTH, side=tk.LEFT)

    frame.grid(column=0, row=0, padx=12, pady=12, sticky="nsew")

    # frame row 1 col 0
    frame_node_edit = ttk.Labelframe(root, text="Node Editor", labelanchor="n")

    frame_node_edit.columnconfigure(0,weight=1)
    frame_node_edit.columnconfigure(1,weight=1)

    frame_node_edit.rowconfigure(0,weight=2)
    frame_node_edit.rowconfigure(1,weight=2)
    frame_node_edit.rowconfigure(2,weight=2)
    frame_node_edit.rowconfigure(3,weight=1)

    # node editor row 0 col 0
    frame = ttk.Frame(frame_node_edit)

    label = ttk.Label(frame, text="Node Type")
    label.pack(pady=8)
    global node_type_combobox
    node_type_combobox = ttk.Combobox(frame, values=NODE_TYPES, state="readonly")
    node_type_combobox.current(0)
    node_type_combobox.pack()

    frame.grid(row=0,column=0, padx=4, pady=16, sticky="nsew")

    # node editor row 0 col 1
    frame = ttk.Frame(frame_node_edit)

    label = ttk.Label(frame, text="Parameter Value")
    label.pack(pady=8)
    global parameter_value_entry
    parameter_value_entry = ttk.Entry(frame)
    parameter_value_entry.pack()

    frame.grid(row=0, column=1, padx=4, pady=16, sticky="nsew")

    # node editor row 1 col 0
    frame = ttk.Frame(frame_node_edit)

    label = ttk.Label(frame, text="Next Node")
    label.pack(pady=8)
    global next_node_entry
    next_node_entry = ttk.Entry(frame)
    next_node_entry.pack()

    frame.grid(row=1, column=0, columnspan=2, padx=4, pady=16, sticky="nsew")

    # node editor row 3 col 0-1
    button = ttk.Button(frame_node_edit, text="Save Node", command=save_node_edit)
    button.grid(row=3, column=0, columnspan=2, padx=4, pady=4, sticky="nsew")

    frame_node_edit.grid(row=1, column=0, padx=12, pady=12, sticky="nsew")

    # row 0-4 col 1
    global node_table
    node_table = NodeTable(root, columns=("ID", "Info", "Node Type", "Node Data"), show="headings")

    node_table.heading("ID", text="ID")
    node_table.heading("Info", text="Info")
    node_table.heading("Node Type", text="Node Type")
    node_table.heading("Node Data", text="Node Data")

    node_table.column("ID", width=50, stretch=False)
    node_table.column("Info", width=130, stretch=True, anchor="e")
    node_table.column("Node Type", width=90, stretch=False, anchor="center")
    node_table.column("Node Data", width=160, stretch=True)

    if dark_mode: # i hate mac os
        node_table.tag_configure("even", background="#252525")
        node_table.tag_configure("odd", background="#1e1e1e")
    else:
        node_table.tag_configure("even", background="#f8f8f8")
        node_table.tag_configure("odd", background="#ffffff")

    node_table.bind("<<TreeviewSelect>>", node_table_select)

    node_table.grid(column=1, row=0, rowspan=2, sticky="nsew", padx=12, pady=12)

    root.mainloop()

def open_file():
    path = filedialog.askopenfilename(
        title="Open File",
        filetypes=[("MSBF files", "*.msbf"), ("All files", "*.*")]
    )
    if not path:
        return

    with open(path, "rb") as f:
        data = f.read()

    if len(data) == 0:
        error("Failed to read file")
        return
    
    global flowchart_list, label_dict
    node_table.clear()
    flowchart_list.configure(listvariable=tk.Variable(value=("")))
    label_dict = dict()
    editor.clear()

    if msbf.parse(data): 
        editor.msbf_loaded = True
        
        label_dict = dict(msbf.labels)

        label_arr = []
        for i in range(msbf.label_count):
            label_arr.append(msbf.labels[i][0])

        flowchart_list.configure(listvariable=tk.Variable(value=label_arr))
        
def save_file():
    if editor.msbf_loaded == False: return
    path = filedialog.asksaveasfilename(
        title="Save File",
        defaultextension=".msbf",
        filetypes=[("MSBF files", "*.msbf"), ("All files", "*.*")]
    )

    if not path:
        return

    data = msbf.export()
    
    with open(path, "wb") as f:
        f.write(data)
    
    print(f"Saved to {path}")

def flowchart_list_select(event):
    global node_table

    if not editor.msbf_loaded: return

    global flowchart_list
    sel = flowchart_list.curselection()
    if not sel: return

    name = flowchart_list.get(sel[0])
    node_id = label_dict[name]
    if node_id == None:
        editor.selected_flowchart = -1
        error(f"Couldnt get Label: {name}")
        return
    
    editor.selected_flowchart = node_id
    node_table.load_flowchart(node_id)
 

def node_table_select(event):
    global node_table
    sel = node_table.selection()
    if not sel:
        select_node(-1)
        return

    node_str = node_table.item(node_table.selection()[0], "values")[0]

    if node_str == "" or node_str == "-": 
        select_node(-1)
    else: 
        try:
            node_id = int(node_str)
            select_node(node_id)
        except:
            error("table node id is not a valid")

def select_node(node_id: int):
    global parameter_value_entry
    global node_type_combobox, next_node_entry
    endian = msbf.endian
    nodes = msbf.nodes

    editor.selected_node = node_id
    parameter_value_entry.delete(0, tk.END)
    next_node_entry.delete(0, tk.END)
    if node_id == -1: return


    parameter_value_entry.insert(0, hex(struct.unpack(f"{endian}I",nodes[node_id][2])[0]))
    node_type_combobox.current(nodes[node_id][0])
    next_node_entry.insert(0, struct.unpack(f"{endian}H",nodes[node_id][3][:2])[0])

def save_node_edit():
    selected_node = editor.selected_node

    if selected_node == -1: return
    global parameter_value_entry, node_table
    global node_type_combobox, next_node_entry
    endian = msbf.endian
    try:
        val = int(parameter_value_entry.get(),16)
    except:
        error("parameter value is not a valid hexadicimal integer")
        return

    node_type, param_type, param_data, node_data = msbf.nodes[selected_node]
    param_data = struct.pack(f"{endian}I",val)

    node_type = NODE_TYPES.index(node_type_combobox.get())
    if node_type == 0:
        error("node type is called \"INVALID\" for a reason, you dummy")
        return

    # pack node data
    next_node, node_data_1, node_data_2, node_data_3 = struct.unpack(f"{endian}4H",node_data)
    try:
        next_node = int(next_node_entry.get()) 
        node_data = struct.pack(f"{endian}4H", next_node, node_data_1, node_data_2, node_data_3)
    except:
        error("next node is not a valid int")
        return

    msbf.nodes[selected_node] = (node_type, param_type, param_data, node_data)

    # refresh table
    node_table.load_flowchart(editor.selected_flowchart)

    # all this is to keep the current node selected when we save our edit
    for item in node_table.get_children():
        node_id = node_table.item(item, "values")[0]
        if node_id == str(selected_node):
            node_table.selection_set(item)
            node_table.see(item)
            break

# init
setup_window()