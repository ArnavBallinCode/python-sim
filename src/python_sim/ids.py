class IdGenerator:
    def __init__(self, seed: int = 0):
        self.seed = seed
        self.count = 0

    def new(self, prefix: str) -> str:
        self.count += 1
        return f"{prefix}_{self.seed:08x}_{self.count:06d}"
