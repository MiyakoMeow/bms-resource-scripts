import webbrowser
from enum import Enum

from options.base import Option


class BMSEvent(Enum):
    BOFTT = 20
    LetsBMSEdit3 = 103

    def list_url(self) -> str:
        if self == BMSEvent.BOFTT:
            return "https://manbow.nothing.sh/event/event.cgi?action=sp&event=146"
        elif self == BMSEvent.LetsBMSEdit3:
            return "https://venue.bmssearch.net/letsbmsedit3"
        else:
            return "https://manbow.nothing.sh/event/event.cgi?action=sp&event=146"

    def work_info_url(self, work_num: int) -> str:
        if self == BMSEvent.BOFTT:
            return f"https://manbow.nothing.sh/event/event.cgi?action=More_def&num={work_num}&event=146"
        elif self == BMSEvent.LetsBMSEdit3:
            return f"https://venue.bmssearch.net/letsbmsedit3/{work_num}"
        else:
            return f"https://manbow.nothing.sh/event/event.cgi?action=More_def&num={work_num}&event=146"


def jump_to_work_info():
    # Select Event
    print("Select BMS Event:")
    for event in BMSEvent:
        print(f" {event.value} -> {event.name}")
    event_value_selection = input("Input event value (Default: BOFTT):")
    if len(event_value_selection) == 0:
        event_value_selection = "20"
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
        nums_1 = num_str.split()
        nums = []
        for num_1 in nums_1:
            for num in num_1.split(","):
                if len(num) == 0:
                    continue
                nums.append(int(num))
        if len(nums) > 2:
            for num in nums:
                id = int(num)
                webbrowser.open_new_tab(event.work_info_url(id))
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


OPTIONS: list[Option] = [Option(name="BMS活动：跳转至作品目录", func=jump_to_work_info)]


if __name__ == "__main__":
    jump_to_work_info()
