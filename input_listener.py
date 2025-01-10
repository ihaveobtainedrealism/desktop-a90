import keyboard
import ctypes
import ctypes.wintypes as wintypes
import threading

pressed_keys = set()
moved_mouse_delta = (0, 0)

listen_mouse = False


def on_key_press(event):
    key_name = event.name.lower().replace("'", "single_quote")

    if event.event_type == "down" and key_name not in pressed_keys:
        pressed_keys.add(key_name)

    elif event.event_type == "up" and key_name in pressed_keys:
        pressed_keys.remove(key_name)

keyboard.hook(on_key_press)


# getting mouse delta by reading raw mouse movement input
# i did not write this...

wintypes.LRESULT = ctypes.c_long

HICON = wintypes.HANDLE
HCURSOR = wintypes.HANDLE
HINSTANCE = wintypes.HANDLE
WNDPROC = ctypes.WINFUNCTYPE(
    wintypes.LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)

RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
WM_INPUT = 0x00FF
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

class RAWINPUTDEVICE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWMOUSE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWINPUT(ctypes.Structure):
    class U(ctypes.Union):
        _pack_ = 1
        _fields_ = [
            ("mouse", RAWMOUSE),
        ]

    _pack_ = 1
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", U),
    ]


def register_raw_input(window_handle):
    device = RAWINPUTDEVICE()
    device.usUsagePage = 0x01
    device.usUsage = 0x02  # Mouse
    device.dwFlags = RIDEV_INPUTSINK
    device.hwndTarget = window_handle

    if not ctypes.windll.user32.RegisterRawInputDevices(ctypes.byref(device), 1, ctypes.sizeof(device)):
        raise ctypes.WinError()


def handle_raw_input(lparam):
    global moved_mouse_delta

    buffer_size = wintypes.UINT()
    result = ctypes.windll.user32.GetRawInputData(
        lparam, RID_INPUT, None, ctypes.byref(buffer_size), ctypes.sizeof(RAWINPUTHEADER)
    )
    if result < 0:
        raise ctypes.WinError()
    buffer = ctypes.create_string_buffer(buffer_size.value)
    result = ctypes.windll.user32.GetRawInputData(
        lparam, RID_INPUT, buffer, ctypes.byref(buffer_size), ctypes.sizeof(RAWINPUTHEADER)
    )
    if result != buffer_size.value:
        raise ctypes.WinError()

    raw = ctypes.cast(buffer, ctypes.POINTER(RAWINPUT)).contents

    if raw.header.dwType == RIM_TYPEMOUSE:
        mouse_data = raw.data.mouse

        if not mouse_data.usFlags & 0x01:
            scale_factor = 1 / 85536
            norm_x = round(mouse_data.lLastX * scale_factor)
            norm_y = round(mouse_data.lLastY * scale_factor)

            clamp_threshold = 1000
            if abs(norm_x) > clamp_threshold or abs(norm_y) > clamp_threshold:
                norm_x = max(min(norm_x, clamp_threshold), -clamp_threshold)
                norm_y = max(min(norm_y, clamp_threshold), -clamp_threshold)

            if listen_mouse:  # while listening, add any occurring mouse delta to the tuple
                moved_mouse_delta = (moved_mouse_delta[0] + norm_x, moved_mouse_delta[1] + norm_y)


def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:
        handle_raw_input(lparam)

    return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, ctypes.cast(lparam, ctypes.c_void_p))


def message_loop():
    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", wintypes.INT),
            ("cbWndExtra", wintypes.INT),
            ("hInstance", HINSTANCE),
            ("hIcon", HICON),
            ("hCursor", HCURSOR),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    wnd_proc_ptr = WNDPROC(wnd_proc)

    h_instance = ctypes.windll.kernel32.GetModuleHandleW(None)
    window_class = WNDCLASS()
    window_class.style = CS_HREDRAW | CS_VREDRAW
    window_class.lpfnWndProc = wnd_proc_ptr
    window_class.hInstance = h_instance
    window_class.lpszClassName = "RawInputWindow"

    if not ctypes.windll.user32.RegisterClassW(ctypes.byref(window_class)):
        raise ctypes.WinError()

    hwnd = ctypes.windll.user32.CreateWindowExW(
        0,
        "RawInputWindow",
        "Raw Input Window",
        0,
        0, 0, 0, 0,
        None,
        None,
        h_instance,
        None
    )

    register_raw_input(hwnd)

    while True:
        msg = wintypes.MSG()
        if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))


# my code again!!

def is_any_key_pressed():
    if pressed_keys != set():
        return pressed_keys

    return False


def start_mouse_listen():
    global listen_mouse

    listen_mouse = True

def get_mouse_listen_results():
    global listen_mouse
    global moved_mouse_delta

    listen_mouse = False
    delta = moved_mouse_delta

    moved_mouse_delta = (0, 0)

    return delta


message_loop_thread = threading.Thread(target=message_loop, daemon=True)
message_loop_thread.start()
