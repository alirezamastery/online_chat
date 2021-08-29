import json
from pprint import pprint
import websocket
import uuid
from threading import Thread


try:
    import thread
except ImportError:
    import _thread as thread
import time


n = 0


def monitor():
    global n
    while True:
        time.sleep(1)
        print(n, 'reqs/scr')
        n = 0


def on_message(ws, message):
    # pprint(message)
    pass


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    def run(*args):
        global n
        while True:
            ws.send(json.dumps({
                'msg_body': str(n),
            }))
            n += 1

    thread.start_new_thread(run, ())


Thread(target=monitor).start()

if __name__ == "__main__":
    ADDRESS = 'ws://127.0.0.1:8000/ws/benchmark_sync/'
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(ADDRESS,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()
