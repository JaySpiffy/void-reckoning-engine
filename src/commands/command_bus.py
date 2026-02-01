from typing import List, Optional
from src.commands.base_command import Command

class CommandBus:
    """Central command dispatcher with undo/redo support."""
    
    def __init__(self):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
    
    def execute(self, command: Command) -> bool:
        if not command.can_execute():
            return False
        
        try:
            command.execute()
            self._undo_stack.append(command)
            self._redo_stack.clear()
            return True
        except Exception as e:
            print(f"Command execution failed: {e}")
            return False
    
    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        
        command = self._undo_stack.pop()
        try:
            command.undo()
            self._redo_stack.append(command)
            return True
        except Exception as e:
            print(f"Command undo failed: {e}")
            return False
    
    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        
        command = self._redo_stack.pop()
        try:
            command.execute()
            self._undo_stack.append(command)
            return True
        except Exception as e:
            print(f"Command redo failed: {e}")
            return False
