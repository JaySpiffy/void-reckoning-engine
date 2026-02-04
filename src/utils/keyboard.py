import os
import sys

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty
    import select

def get_key() -> str | None:
    """
    Non-blocking check for a single key press.
    Returns the character pressed, or None if no key was pressed.
    """
    if os.name == 'nt':
        if msvcrt.kbhit():
            # handle possible multi-byte or special keys (though we mostly care about single chars)
            char = msvcrt.getch()
            # If it's a special key (like arrow keys), msvcrt.getch() returns 0 or 0xe0
            if char in (b'\x00', b'\xe0'):
                msvcrt.getch() # swallow the second part
                return None
            try:
                return char.decode('ascii').lower()
            except UnicodeDecodeError:
                return None
        return None
    else:
        # Save current terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            # Use select to check if stdin has data
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                return char.lower()
            return None
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
