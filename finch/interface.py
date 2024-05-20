import enum
import time

import cv2
from screeninfo import get_monitors

from finch.shared_state import State

WINDOW_NAME = "drarwing_continuous"
MIN_FRAME_DURATION = 1 / 60  # This parameter allows limiting of the framerate, as this would go quite wild otherwise.


class ShowType(enum.Enum):
    NORMAL = enum.auto()
    DIFF = enum.auto()
    ORIGINAL = enum.auto()


def get_window_size(use_full_monitor: bool = False) -> tuple[int, int]:
    if use_full_monitor:
        monitors = get_monitors()
        if len(monitors) == 0:
            raise RuntimeError("No connected monitor found")

        primary_monitors = [monitor for monitor in monitors if monitor.is_primary]
        if len(primary_monitors) > 0:
            monitor = primary_monitors[0]
        else:
            # No primary monitor, lets just grab another
            monitor = monitors[0]

        return (monitor.width, monitor.height)
    else:
        _, _, x, y = cv2.getWindowImageRect(WINDOW_NAME)
    return (x, y)


def _window_exists(window_name: str):
    try:
        return cv2.getWindowProperty(window_name, 0) >= 0
    except cv2.error:
        return False


def render_thread(shared_state: State, fullscreen: bool = True):
    if fullscreen:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
        cv2.namedWindow(WINDOW_NAME)

    debug = False
    show = ShowType.NORMAL

    last_frame = time.time()
    last_frame_duration = -1.0
    while not shared_state.flag_stop and _window_exists(WINDOW_NAME):
        if shared_state.image_available:
            assert shared_state.specimen is not None
            assert shared_state.brush is not None
            match show:
                case ShowType.NORMAL:
                    main_image = shared_state.specimen.cached_image
                case ShowType.DIFF:
                    main_image = cv2.cvtColor(shared_state.specimen.diff_image, cv2.COLOR_GRAY2BGR)
                case ShowType.ORIGINAL:
                    main_image = shared_state.target_image
                case _:
                    raise NotImplementedError

            if debug or shared_state.lock_image:
                main_image = main_image.copy()
                if debug:
                    main_image = cv2.putText(
                        main_image,
                        f"{shared_state.img_path}-{shared_state.brush.name} "
                        f"{shared_state.update_time_microseconds} us, {shared_state.score} score "
                        f'{round(1 / last_frame_duration) if last_frame_duration > 0 else "inf"} fps',
                        (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        1,
                        cv2.LINE_AA,
                    )
                    if shared_state.lock_image:
                        main_image = cv2.putText(
                            main_image, "LOCKED", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA
                        )

            cv2.imshow(WINDOW_NAME, main_image)

            key = cv2.waitKey(1)
            if key > -1:
                match key:
                    case 100:
                        show = ShowType.DIFF  # "d"
                    case 105:
                        debug = not debug  # "i"
                    case 108:
                        shared_state.lock_image = not shared_state.lock_image  # "l"
                    case 109:
                        show = ShowType.NORMAL  # "m"
                    case 110:
                        shared_state.flag_next_image = True  # "n"
                    case 111:
                        show = ShowType.ORIGINAL  # "o"
                    case 27:
                        break  # ESC
                    case _:
                        pass  # Any other key is ignored

        now = time.time()
        last_frame_duration = now - last_frame
        last_frame = now
        if last_frame_duration < MIN_FRAME_DURATION:
            time.sleep(MIN_FRAME_DURATION - last_frame_duration)

    shared_state.flag_stop = True
