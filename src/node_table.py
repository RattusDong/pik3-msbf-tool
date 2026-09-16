import struct

import tkinter as tk
from tkinter import ttk

from src.constants import *
from src.common import *
import src.msbf as msbf

class NodeTable(ttk.Treeview):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
                         
    def load_flowchart(self, node_id: int):
        endian = msbf.endian
        self.clear()
        queue = [("", node_id)]
        row_num = 0
        while True:
            if len(queue) == 0: break
            if row_num >= MAX_NODES: break
            # alternate row colour to make more readable
            row_tag = "even"
            if row_num & 0x1 != 0: row_tag = "odd"
            row_num += 1
            
            info, node_id = queue.pop()
            if node_id == 0xffff:
                self.insert("", tk.END, values=("-", info, "-END-", ""), tags=(row_tag))
                continue
            elif node_id == -1:
                self.insert("", tk.END, values=("", info, "", ""), tags=(row_tag))
                continue

            node_type, param_type, param_data, node_data = msbf.nodes[node_id]
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
                    info = info + f"branch_{node_id} <-"
                    for i in range(cases):
                        idx = (cases - 1) - i
                        target_node = msbf.branch_table[table_idx + idx]
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
                    for lbl in msbf.labels:
                        if lbl[1] == node_id:
                            info = f"{info} Flowchart \"{lbl[0]}\"->"

                case 5: # jump
                    for lbl in msbf.labels:
                        if lbl[1] == next_node:
                            description = f"GOTO: flowchart {lbl[0]}"
                    # under the spec, jump should always be used to enter another flowchart
                    # but, just incase we have this    
                    if description == "": 
                        description = f"GOTO: node #{next_node}"

            self.insert(
                "",
                tk.END,
                values=(
                    node_id,
                    info,
                    NODE_TYPES[node_type],
                    description
                ),
                tags=(row_tag)
            )

    def clear(self):
        for item in self.get_children():
            self.delete(item)

def print_node_params(type: int, data: bytes) -> str:
    endian = msbf.endian
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
            # make it actually have a string table to read from maybe?
            offset = struct.unpack(f"{endian}I", data)[0]
            return f"\"{read_cstring(msbf.FLW3_data,offset)}\""
    # default
    p1 = struct.unpack(f"{endian}i", data)[0]
    return f"{p1}"

