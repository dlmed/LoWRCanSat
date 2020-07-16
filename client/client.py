import socket
import threading

import csv
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation


class Client:
    def __init__(self, port, host, lock_csv, send_period):
        print("Inicializando cliente...")

        self.host = host
        self.port = port
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock_csv = lock_csv
        self.field_names = ['t', 'altd', 'temp', 'pres', 'accx', 'accy', 'accz', 'gyrx', 'gyry', 'gyrz']
        self.contador_csv = 0
        self.t = 0.0
        self.send_period = send_period
        self.plotting = False
        self.csv_path = 'data_0.csv'

        try:
            self.connect_to_server()
            self.listen()
            self.repl()
        except ConnectionError:
            print("Conexión terminada.")
            self.socket_client.close()
            exit()

    def connect_to_server(self):
        self.socket_client.connect((self.host, self.port))
        print("Cliente conectado exitosamente al servidor.")

    def listen(self):
        thread = threading.Thread(target=self.listen_thread, daemon=True)
        thread.start()

    def send(self, msg):
        msg_bytes = msg.encode()
        msg_length = len(msg_bytes).to_bytes(4, byteorder='big')
        self.socket_client.sendall(msg_length + msg_bytes)

    def listen_thread(self):
        while True:
            try:
                response_bytes_length = self.socket_client.recv(4)
                response_length = int.from_bytes(
                    response_bytes_length, byteorder='big')
                response = bytearray()

                while len(response) < response_length:
                    read_length = min(4096, response_length - len(response))
                    response.extend(self.socket_client.recv(read_length))

                received = response.decode()
                print(f"{received}\n>>> ", end='')

                if received != "":
                    self.handle_command(received)
            except ConnectionResetError:
                print('El servidor se ha desconectado')
                print("Conexión terminada.")
                self.socket_client.close()
                exit()
    
    def handle_command(self, received):
        if received[:2] != 'Ac':
            self.write_into_csv(round(self.t, 3), received)
            self.t += self.send_period

    def repl(self):
        thread = threading.Thread(target=self.repl_thread)
        thread.start()

    def repl_thread(self):        
        print("------ Consola ------\n>>> ", end='')
        while True:
            msg = input()
            if msg == 'd1':
                self.new_csv()
                if not self.plotting:
                    #self.plot_data()
                    self.plotting = True
            self.send(msg)
    
    def new_csv(self):
        self.t = 0.0
        self.csv_path = f'data_{self.contador_csv}.csv'
        with open(self.csv_path, 'w') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=self.field_names)
            csv_writer.writeheader()

        self.contador_csv += 1

    def write_into_csv(self, t, data):
        # data en formato '0.0;0.0;0.0'
        with self.lock_csv:
            altd, temp, pres, accx, accy, accz, gyrx, gyry, gyrz = map(float, data.strip().split(';'))
            with open(self.csv_path, 'a') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=self.field_names)
                info = {
                    self.field_names[0]: t,
                    self.field_names[1]: altd,
                    self.field_names[2]: temp,
                    self.field_names[3]: pres,
                    self.field_names[4]: accx,
                    self.field_names[5]: accy,
                    self.field_names[6]: accz,
                    self.field_names[7]: gyrx,
                    self.field_names[8]: gyry,
                    self.field_names[9]: gyrz
                }
                csv_writer.writerow(info)
    
    def plot_data(self):
        thread = threading.Thread(target=self.plot_data_thread)
        thread.start()

    def plot_data_thread(self):
        ani = FuncAnimation(plt.gcf(), self.animate, interval=self.send_period*1000)
        plt.tight_layout()
        plt.show()

    def animate(self, i):
        with self.lock_csv:
            SECS_SHOWN = 4 # secs
            PERIOD = self.send_period
            data = pd.read_csv(self.csv_path)
            t = data['t']
            altd = data['altd']
            temp = data['temp']
            pres = data['pres']
            accx = data['accx']
            accy = data['accy']
            accz = data['accz']
            gyrx = data['gyrx']
            gyry = data['gyry']
            gyrz = data['gyrz']

            plt.cla()
            window = int(SECS_SHOWN / PERIOD)
            if len(t) <= window:
                plt.plot(t, altd, label='Altitude')
                plt.plot(t, temp, label='Temperature')
                plt.plot(t, pres, label='Pressure')
                plt.plot(t, accx, label='Accelerometer X')
                plt.plot(t, accy, label='Accelerometer Y')
                plt.plot(t, accz, label='Accelerometer Z')
                plt.plot(t, gyrx, label='Gyroscope X')
                plt.plot(t, gyry, label='Gyroscope Y')
                plt.plot(t, gyrz, label='Gyroscope Z')
            else:
                plt.plot(t[-window:], altd[-window:], label='Altitude')
                plt.plot(t[-window:], temp[-window:], label='Temperature')
                plt.plot(t[-window:], pres[-window:], label='Pressure')
                plt.plot(t[-window:], accx[-window:], label='Accelerometer X')
                plt.plot(t[-window:], accy[-window:], label='Accelerometer Y')
                plt.plot(t[-window:], accz[-window:], label='Accelerometer Z')
                plt.plot(t[-window:], gyrx[-window:], label='Gyroscope X')
                plt.plot(t[-window:], gyry[-window:], label='Gyroscope Y')
                plt.plot(t[-window:], gyrz[-window:], label='Gyroscope Z')
            plt.legend(loc='upper left')
            plt.tight_layout()


if __name__ == "__main__":
    port = 8080
    host = socket.gethostname()

    lock_csv = threading.Lock()
    client = Client(port, host, lock_csv, 0.01)