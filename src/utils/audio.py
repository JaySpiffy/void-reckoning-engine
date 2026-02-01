
# [USER REQUEST] AUDIO DISABLED
# This class is now a silent stub.

class AudioManager:
    """
    Silent stub for AudioManager.
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(AudioManager, cls).__new__(cls)
        return cls._instance

    def play_sound(self, frequency, duration):
        pass

    def battle_start(self):
        pass

    def battle_victory(self):
        pass

    def turn_tick(self):
        pass

    def economy_boom(self):
        pass

    def crisis_alert(self):
        pass
