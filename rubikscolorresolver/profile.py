import sys


profile_stats_time = {}
profile_stats_calls = {}


if sys.implementation.name == "micropython":
    import utime

    def timed_function(f, *args, **kwargs):
        myname = str(f).split(' ')[1]

        def new_func(*args, **kwargs):
            t = utime.ticks_us()
            result = f(*args, **kwargs)

            if myname not in profile_stats_time:
                profile_stats_time[myname] = 0
                profile_stats_calls[myname] = 0

            profile_stats_time[myname] += utime.ticks_diff(utime.ticks_us(), t)
            profile_stats_calls[myname] += 1

            return result

        return new_func

else:
    #import time

    def timed_function(f, *args, **kwargs):
        #myname = str(f).split(' ')[1]

        def new_func(*args, **kwargs):
            #t = utime.ticks_us()
            result = f(*args, **kwargs)

            #if myname not in profile_stats_time:
            #    profile_stats_time[myname] = 0
            #    profile_stats_calls[myname] = 0

            #profile_stats_time[myname] += utime.ticks_diff(utime.ticks_us(), t)
            #profile_stats_calls[myname] += 1

            return result

        return new_func


def print_profile_data():
    print("time(ms)     calls  function")
    print("========  ========  =======================")
    lines = []
    for function in profile_stats_calls.keys():
        lines.append("{:>8.2f}  {:>8}  {}".format(profile_stats_time[function] / 1000, profile_stats_calls[function], function))

    lines = sorted(lines)
    print("\n".join(lines))

