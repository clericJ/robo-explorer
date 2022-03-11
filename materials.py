from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class Material:
    name: str
    resource: str
    strength: int

# limestone, basalt, aluminum, iron, titan
