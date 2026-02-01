
import time
import os
import logging
from typing import Generator, Optional

logger = logging.getLogger(__name__)

class LogTailer:
    """
    Utility to tail a file in real-time.
    Designed to work with the Campaign Dashboard to stream events from campaign.json.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._file = None
        self._inode = None
        
    def open(self, seek_end: bool = True) -> bool:
        """
        Open the file for tailing.
        
        Args:
            seek_end: If True, start reading from the current end of the file.
                      If False, start from the beginning.
        """
        if not os.path.exists(self.file_path):
            return False
            
        try:
            self._file = open(self.file_path, 'r', encoding='utf-8')
            
            # Store inode to detect rotation
            try:
                st = os.fstat(self._file.fileno())
                self._inode = st.st_ino
            except:
                pass

            if seek_end:
                self._file.seek(0, 2)
            return True
        except Exception as e:
            logger.error(f"Failed to open log for tailing ({self.file_path}): {e}")
            return False

    def read_lines(self) -> Generator[str, None, None]:
        """
        Yields any new lines available in the file.
        Returns immediately if no new lines (does not block).
        """
        if not self._file:
            return

        while True:
            # Save position in case of partial read
            curr_pos = self._file.tell()
            line = self._file.readline()
            
            if not line:
                self._file.seek(curr_pos) # Reset to before partial line
                break
                
            if line.endswith('\n'):
                yield line
            else:
                # Partial line (write in progress), back off
                self._file.seek(curr_pos)
                break
                
    def check_rotation(self) -> bool:
        """
        Check if the file has been rotated/deleted/recreated.
        Returns True if reopened, False otherwise.
        """
        if not os.path.exists(self.file_path):
            return False
            
        try:
            # Check if inode changed
            new_inode = os.stat(self.file_path).st_ino
            if new_inode != self._inode:
                logger.info(f"File rotation detected for {self.file_path}")
                val = self.reopen()
                return val
        except:
            pass
        return False

    def reopen(self) -> bool:
        """Close and reopen the file from the beginning."""
        self.close()
        return self.open(seek_end=False) # Start from 0 on rotation

    def close(self):
        if self._file:
            try:
                self._file.close()
            except:
                pass
            self._file = None
