import sys
import struct

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font as tkfont

WIN_WIDTH = 1000
WIN_HEIGHT = 600

NODE_TYPES = (
    "INVALID",
    "Message",
    "Branch",
    "Event",
    "Entry",
    "Jump",
)

PARAM_TYPES = (
    "s32",
    "s16, s16",
    "s16, s8, s8",
    "s8, s8, s16",
    "s8, s8, s8, s8",
    "string",
    "s32",
)

BRANCH_TYPES = (
    "unk_branch_00",
    "checkEnergyTank",
    "checkStoryProgress",
    "unk_branch_03",
    "checkGamemode",
    "unk_branch_05",
    "unk_branch_06",
    "unk_branch_07",
    "unk_branch_08",
    "checkDifficulty",
    "unk_branch_0a",
    "unk_branch_0b",
)

BRANCH_CONDITIONS = (
    ("unk0","unk1","unk2"),
    ("less_or_equal","greater"),
    ("less_or_equal","greater"),
    ("never","always"), # condition is always branch 1
    ("story","mission","versus"),
    ("unk0","unk1","unk2"),
    ("unk0","unk1","unk2"),
    ("unk0","unk1","unk2"),
    ("unk0","unk1","unk2"),
    ("normal", "spicy", "ultra_spicy"),
    ("unk0","unk1","unk2"),
    ("unk0","unk1","unk2"),
)

EVENT_TYPES = (
    "unk_event_00",
    "unk_event_01",
    "unk_event_02",
    "unk_event_03",
    "unk_event_04",
    "unk_event_05",
    "unk_event_06",
    "unk_event_07",
    "unk_event_08",
    "unk_event_09",
    "unk_event_0a",
    "unk_event_0b",
    "unk_event_0c",
    "unk_event_0d",
    "unk_event_0e",
    "unk_event_0f",
    "unk_event_10",
    "unk_event_11",
    "unk_event_12",
    "unk_event_13",
    "unk_event_14",
    "unk_event_15",
    "unk_event_16",
    "unk_event_17",
    "unk_event_18",
    "unk_event_19",
    "unk_event_1a",
    "unk_event_1b",
    "unk_event_1c",
    "unk_event_1d",
    "unk_event_1e",
    "setStoryProgress",
    "unlockKoppad",
    "unk_event_21",
    "unk_event_22",
    "unk_event_23",
    "unk_event_23",
    "unk_event_24",
    "unlockKoppadButton",
    "unk_event_26",
    "unk_event_27",
    "unk_event_28",
    "unk_event_29",
    "unk_event_2a",
    "unk_event_2b",
    "unk_event_2c",
    "unk_event_2d",
    "unk_event_2e",
    "unk_event_2f",
    "unk_event_30",
    "unk_event_31",
    "unk_event_32",
    "unk_event_33",
    "unk_event_34",
    "unk_event_35",
    "unk_event_36",
    "unk_event_37",
    "unk_event_38",
    "unk_event_39",
    "unk_event_3a",
    "unk_event_3b",
    "unk_event_3c",
    "unk_event_3d",
    "unk_event_3e",
    "unk_event_3f",
    "unk_event_40",
    "unk_event_41",
    "unk_event_42",
    "unk_event_43",
    "unk_event_44",
    "unk_event_45",
    "unk_event_46",
    "unk_event_47",
    "unk_event_48",
)

FLW3_base = 0x30

endian = "<"

nodes = []
node_count = 0

branch_table = []
branch_table_count = 0

labels = []
label_count = 0
label_dict = dict()

msbf_loaded = False

FLW3_data = None
FEN1_data = None

selected_node = -1

def error(msg: str):
    messagebox.showerror(title="Error",message=msg)

def read_cstring(data: bytes, offset: int) -> str:
    end = data.index(b'\x00', offset)
    return data[offset:end].decode("utf-8")

def setup_window():
    global root
    root = tk.Tk()
    root.title("Pikmin 3 MSBF Tool")

    root.geometry(f'{WIN_WIDTH}x{WIN_HEIGHT}')
    root.resizable(False, False)



    if sys.platform == "win32":
        root.iconbitmap('./assets/icon.ico')
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    else:
        photo = tk.PhotoImage(file='./assets/python_icon.png')
        root.iconphoto(False, photo)
        root.icon_ref = photo

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

    label = ttk.Label(root, text='Selected Flowchart')
    label.place(x=80, y=50)
    global flowchart_combobox
    flowchart_combobox = ttk.Combobox(root, values=("none"), state="readonly")
    flowchart_combobox.current(0)
    flowchart_combobox.bind("<<ComboboxSelected>>", flowchart_combobox_select)
    flowchart_combobox.place(x=65, y=70)

    sep = ttk.Separator(root, orient="horizontal")
    sep.place(x=20, y=110, width=250)

    label = ttk.Label(root, text='Node Editor')
    label.place(x=105, y=135)

    label = ttk.Label(root, text='Parameter Value')
    label.place(x=165, y=185)
    global parameter_value
    parameter_value = ttk.Entry(root)
    parameter_value.place(x=156, y=205, width=110)

    label = ttk.Label(root, text='Parameter Type')
    label.place(x=30, y=185)
    combobox = ttk.Combobox(root, values=("Unavailable"), state="readonly")
    combobox.current(0)
    combobox.place(x=20, y=205, width=110)

    global save_node_button
    save_node_button = ttk.Button(root, text="Save Node", command=save_node_edit)
    save_node_button.place(x=100, y=280)


    global node_table
    node_table = ttk.Treeview(root, columns=("ID", "Info", "Node Type", "Node Data"), show="headings")

    node_table.heading("ID", text="ID")
    node_table.heading("Info", text="Info")
    node_table.heading("Node Type", text="Node Type")
    node_table.heading("Node Data", text="Node Data")

    node_table.column("ID", width=40)
    node_table.column("Info", width=230)
    node_table.column("Node Type", width=85)
    node_table.column("Node Data", width=320)

    node_table.bind("<<TreeviewSelect>>", node_table_select)

    node_table.place(x=290, y=30, width=680, height=520)

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
    global msbf_loaded
    if parse_msbf(data): 
        msbf_loaded = True
    else: 
        msbf_loaded = False
        global flowchart_combobox
        flowchart_combobox.configure(values=("none"))
        flowchart_combobox.current(0)

def save_file():
    path = filedialog.asksaveasfilename(
        title="Save File",
        defaultextension=".msbf",
        filetypes=[("MSBF files", "*.msbf"), ("All files", "*.*")]
    )

    if not path:
        return

    data = export_msbf()
    
    with open(path, "wb") as f:
        f.write(data)
    
    print(f"Saved to {path}")

def flowchart_combobox_select(event):
    if not msbf_loaded: return
    global flowchart_combobox
    name = flowchart_combobox.get()
    node_id = label_dict[name]
    if node_id == None:
        error(f"Couldnt get Label: {name}")
        return
    
    load_from_node(node_id)

def load_from_node(node_id: int):
    global selected_node
    selected_node = -1
    clear_node_table()
    global node_table
    queue = [("", node_id)]
    while True:
        if len(queue) == 0: break
        info, node_id = queue.pop()
        if node_id == 0xffff:
            node_table.insert("", tk.END, values=("-", info, "END", ""))
            continue
        elif node_id == -1:
            node_table.insert("", tk.END, values=("", info, "", ""))
            continue

        node_type, param_type, param_data, node_data = nodes[node_id]
        next_node = struct.unpack(f"{endian}H", node_data[:2])[0]
        queue.append(("", next_node))

        description = ""

        match node_type:
            case 1: # message
                msbt_idx, msg_idx = struct.unpack(f"{endian}2x2H", node_data[:6])
                description = f"MSBT File index: {msbt_idx}, Message Index: {msg_idx}"
                
            case 2: # branch
                queue.pop()
                type, cases, table_idx = struct.unpack(f"{endian}2x3H", node_data)
                description = f"{BRANCH_TYPES[type]}({print_node_params(param_type, param_data)}) cases: {cases}, index: {table_idx}"
                if info != "": info += " | "
                info = info + f"<- branch_{node_id}"
                for i in range(cases):
                    idx = (cases - 1) - i
                    target_node = branch_table[table_idx + idx]
                    merged = False
                    # merge duplicate switch cases
                    for j, item in enumerate(queue):
                        if target_node == item[1]:
                            queue.insert(
                                j + 1,
                                (f"branch_{node_id}: {BRANCH_CONDITIONS[type][idx]}",-1)
                            )
                            merged = True
                            break
                    if not merged: 
                        queue.append((f"branch_{node_id}: {BRANCH_CONDITIONS[type][idx]} ->",target_node))
                    

            case 3: # event
                type = struct.unpack(f"{endian}2xH", node_data[:4])[0]
                description = f"{EVENT_TYPES[type]}({print_node_params(param_type, param_data)})"

            case 4: # entry
                for lbl in labels:
                    if lbl[1] == node_id:
                        info = f"{lbl[0]}:  {info}"

            case 5: # jump
                for lbl in labels:
                    if lbl[1] == next_node:
                        description = f"GOTO: flowchart {lbl[0]}"
                # under the spec, jump should always be used to enter another flowchart
                # but, just incase we have this    
                if description == "": 
                    description = f"GOTO: node #{next_node}"

        node_table.insert(
            "",
            tk.END,
            values=(
                node_id,
                info,
                NODE_TYPES[node_type],
                description
            ),
        )

def clear_node_table():
    global node_table
    for item in node_table.get_children():
        node_table.delete(item)

def print_node_params(type: int, data: bytes) -> str:
    match type:
        case 0:
            p1 = struct.unpack(f"{endian}i", data)[0]
            return f"{p1}"
        case 1:
            p1, p2 = struct.unpack(f"{endian}hh", data)
            return f"{p1},{p2}"
        case 2:
            p1, p2, p3 = struct.unpack(f"{endian}hbb", data)
            return f"{p1},{p2},{p3}"
        case 3:
            p1, p2, p3 = struct.unpack(f"{endian}bbh", data)
            return f"{p1},{p2},{p3}"
        case 4:
            p1, p2, p3, p4 = struct.unpack(f"{endian}4b", data)
            return f"{p1},{p2},{p3},{p4}"
        case 5:
            offset = struct.unpack(f"{endian}I", data)[0]
            return f"\"{read_cstring(FLW3_data,offset)}\""
    # default
    p1 = struct.unpack(f"{endian}i", data)[0]
    return f"{p1}"

def node_table_select(event):
    global node_table
    sel = node_table.item(node_table.selection()[0], "values")[0]

    if sel == "" or sel == "-": select_node(-1)
    else: select_node(int(sel))

def select_node(id: int):
    global selected_node, parameter_value
    selected_node = id
    parameter_value.delete(0, tk.END)
    if id == -1: return

    parameter_value.insert(0, hex(struct.unpack(f"{endian}I",nodes[id][2])[0]))

# actually add all the configs later, only param_data is important right now
def save_node_edit():
    if selected_node == -1: return
    global parameter_value
    val = int(parameter_value.get(),16)

    node_type, param_type, param_data, node_data = nodes[selected_node]
    param_data = struct.pack(f"{endian}I",val)
    nodes[selected_node] = (node_type, param_type, param_data, node_data)

    flowchart_combobox_select(None)

def parse_msbf(data: bytes) -> bool:
    global nodes, node_count, branch_table, branch_table_count
    global labels, label_count, label_dict
    global FLW3_data, FEN1_data
    global endian, msbf_loaded, selected_node
    # clear existing stuff
    nodes = []
    node_count = 0
    branch_table = []
    branch_table_count = 0
    labels = []
    label_count = 0
    label_dict = dict()
    msbf_loaded = False
    FLW3_data = None
    FEN1_data = None
    selected_node = -1

    # validate file type
    magic = data[:0x8]
    if magic != b"MsgFlwBn":
        error("File is not a MSBF!")
        return False

    if data[0x8] == 0xff: endian = "<"
    else: endian = ">"

    if data[0xc] != 0:
        error(f"Expected encoding type 0, instead got type: {data[0xc]}")
        return False

    if data[0xd] != 3:
        error(f"Expected version 3, instead got version: {data[0xd]}")
        return False

    if data[0xe] != 2:
        error(f"Expected number of blocks to be 2, instead got: {data[0xe]}")
        return False

    file_size = struct.unpack_from(f"{endian}I",data,0x12)[0]

    if file_size != len(data):
         error("Filesize mismatch!")
         return False

    FLW3_magic, FLW3_size, node_count, branch_table_count = struct.unpack_from(f"{endian}4sI8xHH", data, 0x20)

    if FLW3_magic != b"FLW3":
        error("Couldn't locate FLW3 block!")
        return False

    # copy all flow nodes into array
    offset = FLW3_base + 0x10
    nodes_end = offset + node_count * 0x10
    while offset < nodes_end:
        nodes.append(struct.unpack_from(f"{endian}BB2x4s8s", data, offset))
        offset += 0x10

    # copy all branch table endries into an array
    bt_size = branch_table_count * 0x2
    bt_end = offset + bt_size
    while offset < bt_end:
        branch_table.append(struct.unpack_from(f"{endian}H", data, offset)[0])
        offset += 0x2
    
    
    FEN1_header = 0x30 + FLW3_size
    # round up to nearest 0x10
    if FEN1_header & 0xf != 0:
        FEN1_header &= 0xfffffff0
        FEN1_header += 0x10

    FEN1_base = FEN1_header + 0x10

    FEN1_magic, FEN1_size, bucket_count = struct.unpack_from(f"{endian}4sI8xI", data, FEN1_header)

    if FEN1_magic != b"FEN1":
        error("Couldn't locate FEN1 block!")
        return False

    
    # later, we need to actually store the buckets so they can be edited
    offset = FEN1_base + 0x4
    bucket_end = FEN1_base + 0x4 + bucket_count * 8 
    while offset < bucket_end:
        label_num, label_offset = struct.unpack_from(f"{endian}2I", data, offset)
        # apparently one bucket can have many labels, but in pik3 ive only seen up to 1 per bucket
        for i in range(label_num):
            label_count += 1
            name_len = data[FEN1_base + label_offset]
            entry = struct.unpack_from(f"{endian}{name_len}sI", data, FEN1_base + label_offset + 1)
            labels.append((entry[0].decode("utf-8"),entry[1]))
            label_offset += name_len + 5

        offset += 0x8

    FLW3_data = data[FLW3_base : FLW3_base + FLW3_size]
    FEN1_data = data[FEN1_base : FEN1_base + FEN1_size]

    label_dict = dict(labels)

    global flowchart_combobox
    label_arr = []
    for i in range(label_count):
        label_arr.append(labels[i][0])

    flowchart_combobox.configure(values=label_arr)
    flowchart_combobox.current(0)
    load_from_node(labels[0][1])

    print("MSBF Loaded!")
    return True

# not fully complete yet
def export_msbf() -> bytes:
    data = bytearray()

    # write header
    data += struct.pack(f"{endian}8sH2x2BH16x", b"MsgFlwBn", 0xfeff, 0, 3, 2)

    # write FLW3 header
    data += struct.pack(f"{endian}4sI8xHH12x", b"FLW3", len(FLW3_data), node_count, branch_table_count)
    # write FLW3 nodes
    for i in range(node_count):
        node_type, param_type, param_data, node_data = nodes[i]
        data += struct.pack(f"{endian}2B2x4s8s", node_type, param_type, param_data, node_data)
    # lazy ass, update later
    the_rest_offs = node_count * 0x10 + 0x10
    the_rest_size = len(FLW3_data) - the_rest_offs
    data += FLW3_data[the_rest_offs:the_rest_offs+the_rest_size]
    # align block to 0x10
    low_nibble = len(data) & 0xf
    if low_nibble != 0:
        data += struct.pack(f"{0x10 - low_nibble}x")

    # write FEN1 header
    data += struct.pack(f"{endian}4sI8x", b"FEN1", len(FEN1_data))
    # also update later
    data += FEN1_data
    # align block to 0x10
    low_nibble = len(data) & 0xf
    if low_nibble != 0:
        data += struct.pack(f"{0x10 - low_nibble}x")

    # write file length to header
    data[0x12:0x16] = struct.pack(f"{endian}I",len(data))

    return bytes(data)

# init
setup_window()