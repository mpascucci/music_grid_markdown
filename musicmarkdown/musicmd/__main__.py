import argparse
from .__init__ import Watcher, ThreadedServer, compile_mmd
import logging
import os

if __name__ == "__main__":
    logging.getLogger('musicmd.__init__').setLevel(logging.CRITICAL)
    logger = logging.getLogger(__name__)
    # for key in logging.Logger.manager.loggerDict:
    #     print(key)

    parser = argparse.ArgumentParser(prog="musicmd", description='Compile a mmd script to html')
    parser.add_argument('file', help='The mmd script file that will be compiled')
    parser.add_argument('-o', '--output', help='Name of the output HTML file', default='index.html')

    sp = parser.add_subparsers(title="optional commands", dest="command")
    serve = sp.add_parser('serve', help='Start a live web-server and preview the compiled script')
    watch = sp.add_parser('watch', help='Recompile as file is modified')

    # n = parser.parse_args('script.txt serve'.split())
    n = parser.parse_args()
    # watch.parse_args()
    # print(n)

    if not os.path.exists(n.file):
        print(f"ERROR: file {n.file} not found in the current directory")
        exit(1)

    if n.command == "serve":
        w = Watcher(n.file)
        t = ThreadedServer(w, port=8000)
        t.start()
        w.live_server_addr = f'http://localhost:{t.port}'
        w.start()
        print(f"Server running.\nOpen this address (http://localhost:{t.port}) in a web browser to see your grid")
        try:
            while True:
                input("Kill the process to stop (Ctrl+C)")
        except KeyboardInterrupt:
            t.stop_server() # stop the server
            w.stop = True  # kill the watcher
    elif n.command == "watch":
        w = Watcher(n.file)
        w.start()
        print("Watching modifications to the script file.")
        try:
            while True:
                input("Kill the process to stop (Ctrl+C)")
        except KeyboardInterrupt:
            w.stop = True # kill the watcher
    else:
        compile_mmd(n.file, out_filename=n.output)

