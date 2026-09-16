from tkinter import messagebox

dark_mode = False

def error(msg: str):
    messagebox.showerror(title="Error",message=msg)

def read_cstring(data: bytes, offset: int) -> str:
    end = data.index(b'\x00', offset)
    return data[offset:end].decode("utf-8")