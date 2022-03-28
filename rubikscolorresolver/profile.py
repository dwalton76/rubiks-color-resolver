"""
To use this:

from rubikscolorresolver.profile import timed_function

@timed_function
def some_slow_function():
    pass
"""

# standard libraries
import sys

stack_history = {}
profile_stats_time_excluding_children = {}
profile_stats_time_including_children = {}
profile_stats_calls = {}
timed_function_stack = []

if sys.implementation.name == "micropython":
    # third party libraries
    import utime

    def timed_function(f, *args, **kwargs):
        myname = str(f).split(" ")[1]

        def new_func(*args, **kwargs):
            t0 = utime.ticks_us()
            timed_function_stack.append(myname)
            result = f(*args, **kwargs)

            if myname not in profile_stats_time_including_children:
                profile_stats_time_including_children[myname] = 0
                profile_stats_calls[myname] = 0

            t1 = utime.ticks_us()
            delta_us = utime.ticks_diff(t1, t0)
            profile_stats_time_including_children[myname] += delta_us
            profile_stats_calls[myname] += 1

            if len(timed_function_stack) >= 2:
                stack_last_two = tuple(timed_function_stack[-2:])

                if stack_last_two not in stack_history:
                    stack_history[stack_last_two] = 0
                stack_history[stack_last_two] += delta_us

            timed_function_stack.pop()

            return result

        return new_func

else:
    # import time

    def timed_function(f, *args, **kwargs):
        # myname = str(f).split(' ')[1]

        def new_func(*args, **kwargs):
            # t = utime.ticks_us()
            result = f(*args, **kwargs)

            # if myname not in profile_stats_time_including_children:
            #    profile_stats_time_including_children[myname] = 0
            #    profile_stats_calls[myname] = 0

            # profile_stats_time_including_children[myname] += utime.ticks_diff(utime.ticks_us(), t)
            # profile_stats_calls[myname] += 1

            return result

        return new_func


def get_time_to_subtract(function):
    result = 0

    for (stack_last_two, delta) in stack_history.items():
        # if function in entry["stack"] and entry["stack"][-2] == function:
        #    result += entry["delta"]
        if stack_last_two[0] == function:
            result += delta

    return result


def print_profile_data():
    print("                cumulative")
    print("    time(ms)      time(ms)     calls  function")
    print("============  ============  ========  =======================")
    lines = []

    for (function, value) in profile_stats_time_including_children.items():
        profile_stats_time_excluding_children[function] = value

    for function in profile_stats_time_excluding_children.keys():
        profile_stats_time_excluding_children[function] -= get_time_to_subtract(function)

    for function in profile_stats_calls.keys():
        lines.append(
            "{:>12.2f}  {:>12.2f}  {:>8}  {}".format(
                profile_stats_time_excluding_children.get(function) / 1000,
                profile_stats_time_including_children[function] / 1000,
                profile_stats_calls[function],
                function,
            )
        )

    lines = sorted(lines)
    print("\n".join(lines))
