import src.msbf as msbf

msbf_loaded = False
selected_node = -1
selected_flowchart = -1

def clear():
    global msbf_loaded, selected_node, selected_flowchart
    msbf_loaded = False
    selected_node = -1
    selected_flowchart = -1
    msbf.clear()