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
