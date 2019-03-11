import socket, select, queue
import sys
import traceback


def server(log_buffer=sys.stderr):
    # set an address for our server
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # log that we are building a server
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(5)
    inputs = [sock]
    outputs = []
    message_queues = {}

    try:
        # the outer loop controls the creation of new connection sockets. The
        # sock will handle each incoming connection one at a time.
        while inputs:
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs)
            for s in readable:
                if s is sock:
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    message_queues[connection] = queue.Queue()
                else:
                    data = s.recv(16)
                    if data:
                        message_queues[s].put(data)
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        del message_queues[s]

            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    outputs.remove(s)
                else:
                    s.sendall(next_msg)

            for s in exceptional:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]
        # while True:
        #     print('waiting for a connection', file=log_buffer)
        #     conn, addr = sock.accept()
        #     try:
        #         print('connection - {0}:{1}'.format(*addr), file=log_buffer)

        #         # the inner loop will receive messages sent by the client in
        #         # buffers.  When a complete message has been received, the
        #         # loop will exit
        #         while True:
        #             data = conn.recv(16)
        #             print('received "{0}"'.format(data.decode('utf8')))
        #             conn.sendall(data)
        #             print('sent "{0}"'.format(data.decode('utf8')))
        #             if len(data) < 16:
        #                 break

        #     except Exception as e:
        #         traceback.print_exc()
        #         sys.exit(1)
        #     finally:
        #         conn.close()
        #         print(
        #             'echo complete, client connection closed', file=log_buffer
        #         )

    except KeyboardInterrupt:
        sock.close()
        print('quitting echo server', file=log_buffer)


if __name__ == '__main__':
    server()
    sys.exit(0)
