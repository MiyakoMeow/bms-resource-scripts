import webbrowser
from enum import Enum

from options import Option


class BMSEvent(Enum):
    BOFTT = 20
    BOF21 = 21
    LetsBMSEdit3 = 103

    def list_url(self) -> str:
        match self:
            case BMSEvent.BOFTT:
                return "https://manbow.nothing.sh/event/event.cgi?action=sp&event=146"
            case BMSEvent.BOF21:
                return "https://manbow.nothing.sh/event/event.cgi?action=sp&event=149"
            case BMSEvent.LetsBMSEdit3:
                return "https://venue.bmssearch.net/letsbmsedit3"

    def work_info_url(self, work_num: int) -> str:
        match self:
            case BMSEvent.BOFTT:
                return f"https://manbow.nothing.sh/event/event.cgi?action=More_def&num={work_num}&event=146"
            case BMSEvent.BOF21:
                return f"https://manbow.nothing.sh/event/event.cgi?action=More_def&num={work_num}&event=149"
            case BMSEvent.LetsBMSEdit3:
                return f"https://venue.bmssearch.net/letsbmsedit3/{work_num}"


def jump_to_work_info() -> None:
    # Select Event
    print("Select BMS Event:")
    for event in BMSEvent:
        print(f" {event.value} -> {event.name}")
    event_value_selection = input("Input event value (Default: BOFTT):")
    if len(event_value_selection) == 0:
        event_value_selection = str(BMSEvent.BOFTT.value)
    event = BMSEvent(int(event_value_selection))
    print(f" -> Selected Event: {event.name}")

    # Input Id
    print(' !: Input "1": jump to work id 1. (Normal)')
    print(' !: Input "2 5": jump to work id 2, 3, 4 and 5. (Special: Range)')
    print(' !: Input "2 5 6": jump to work id 2, 5 and 6. (Normal)')
    print(" !: Press Ctrl+C to Quit.")
    tips = "Input id (default: Jump to List):"

    while True:
        num_str = input(tips).strip().replace("[", "").replace("]", "")
        nums: list[int] = []
        for token in num_str.replace(",", " ").split():
            if len(token) == 0:
                continue
            nums.append(int(token))
        if len(nums) > 2:
            for num_val in nums:
                webbrowser.open_new_tab(event.work_info_url(num_val))
        elif len(nums) == 2:
            start, end = int(nums[0]), int(nums[1])
            if start > end:
                start, end = end, start
            for id in range(start, end + 1):
                webbrowser.open_new_tab(event.work_info_url(id))

        elif len(num_str) > 0:
            if num_str.isdigit():
                print(f"Open no.{num_str}")
                id = int(num_str)
                webbrowser.open_new_tab(event.work_info_url(id))
            else:
                print("Please input vaild number.")
        else:
            print("Open BMS List.")
            webbrowser.open_new_tab(event.list_url())


OPTIONS: list[Option] = [Option(name="BMS活动：跳转至作品信息页", func=jump_to_work_info)]


if __name__ == "__main__":
    jump_to_work_info()
