import struct

from src.common import *

FLW3_base = 0x30

nodes = []
node_count = 0

branch_table = []
branch_table_count = 0

labels = []
label_count = 0

FLW3_data = None
FEN1_data = None

def parse(data: bytes) -> bool:
    global nodes, node_count, branch_table, branch_table_count
    global labels, label_count, label_dict
    global FLW3_data, FEN1_data
    global endian
    
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

    print("MSBF Loaded!")
    return True

# not fully complete yet
def export() -> bytes:
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

def clear():
    global nodes, node_count, branch_table, branch_table_count
    global labels, label_count
    global FLW3_data, FEN1_data
    global endian

    nodes = []
    node_count = 0
    branch_table = []
    branch_table_count = 0
    labels = []
    label_count = 0
    FLW3_data = None
    FEN1_data = None

    