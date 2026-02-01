import inspect
from src.utils.logging import GameLogger

print("Attributes of GameLogger:")
print(f"__init__: {GameLogger.__init__}")
print(f"__new__: {GameLogger.__new__}")
print(f"Signature: {inspect.signature(GameLogger)}")

try:
    l = GameLogger(log_dir="test", console_verbose=False)
    print("Instantiation success")
except Exception as e:
    print(f"Instantiation failed: {e}")
