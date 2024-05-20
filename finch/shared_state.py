from dataclasses import dataclass

from finch.brush import BrushSet
from finch.primitive_types import Image
from finch.specimen import Specimen


@dataclass
class State:
    img_path: str
    brush: BrushSet

    target_image: Image
    specimen: Specimen

    score: int = 99999999

    image_available: bool = False
    update_time_microseconds: int = 0

    lock_image: bool = False

    flag_stop: bool = False
    flag_next_image: bool = False
