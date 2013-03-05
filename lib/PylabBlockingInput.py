import time
import threading


class BlockingInputHelperThread(threading.Thread):
    """ A helper thread inside which the blocking function will be run.
    """

    def __init__(self, blocking_function):
        self.blocking_function = blocking_function
        threading.Thread.__init__(self)

        self.exception = None

    def run(self):

        try:
            self.returnvalue = self.blocking_function()
        except Exception as e:
            self.exception = e



class BlockingInput(object):
    """ Class that creates a callable object to run a blocking function
        (in a seperate thread) without freezing the figure.
    """


    def __init__(self, blocking_func, fig=None):

        if fig is None:
            from pylab import gcf
            self.fig = gcf()
        else:
            self.fig = fig

        self.blocking_func = blocking_func


    def __call__(self):
        """ Run the blocking function in a seperate thread while the main
            thread updates the figure. Returns the return value of
            the original blocking function. Any exception from the original
            blocking function will be also raised.
        """


        # Ensure that the figure is shown
        self.fig.show()

        thr = BlockingInputHelperThread(self.blocking_func)
        thr.start()

        while thr.isAlive():
            self.fig.canvas.flush_events()
            time.sleep(0.01)

        if thr.exception:
            raise thr.exception
        else:
            return thr.returnvalue
