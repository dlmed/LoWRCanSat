import socket
import threading
import time
import random
import subprocess
#from mpu6050 import mpu6050
# from bmp280 import BMP280
# from smbus import SMBus
# import RPi.GPIO as GPIO


class Server:
    def __init__(self, port, host):
        print("Inicializando servidor...")

        self.clientes = list()
        self.host = host
        self.port = port
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start_sending_data = False
        self.bind_and_listen()
        self.accept_connections()

    def bind_and_listen(self):
        self.socket_server.bind((self.host, self.port))
        self.socket_server.listen()
        print(f"Servidor escuchando en {self.host}:{self.port}...")

    def accept_connections(self):
        thread = threading.Thread(target=self.accept_connections_thread)
        thread.start()

    def accept_connections_thread(self):
        print("Servidor aceptando conexiones...")

        while True:
            client_socket, _ = self.socket_server.accept()
            self.clientes.append(client_socket)
            listening_client_thread = threading.Thread(
                target=self.listen_client_thread,
                args=(client_socket, ),
                daemon=True)
            listening_client_thread.start()

    @staticmethod
    def send(value, sock):
        stringified_value = str(value)
        msg_bytes = stringified_value.encode()
        msg_length = len(msg_bytes).to_bytes(4, byteorder='big')
        sock.send(msg_length + msg_bytes)

    def listen_client_thread(self, client_socket):
        print("Servidor conectado a un nuevo cliente...")
        cliente_conectado = True

        while cliente_conectado:
            try:
                response_bytes_length = client_socket.recv(4)
                response_length = int.from_bytes(
                    response_bytes_length, byteorder='big')
                response = bytearray()

                while len(response) < response_length:
                    read_length = min(4096, response_length - len(response))
                    response.extend(client_socket.recv(read_length))

                received = response.decode()

                if received != "":
                    response = self.handle_command(received, client_socket)
                    self.send(response, client_socket)
            except ConnectionResetError:
                print('El cliente se ha desconectado')
                cliente_conectado = False

    def handle_command(self, received, client_socket):
        print("Comando recibido:", received)
        # Este método debería ejecutar la acción y enviar una respuesta.
        if received == 'd0':
            self.start_sending_data = False
        elif received == 'd1':
            self.start_sending_data = True
        elif received[0] == 'c':
            if received[1:].isnumeric:
                segs = int(received[1:])
                self.start_camera(segs)
        return "Acción asociada a " + received
    
    def repl(self, msg):
        if self.start_sending_data:
            try:
                self.send(msg, self.clientes[-1])
            except:
                self.start_sending_data = False
    
    def start_camera(self, time): # time in seconds
        # record and stream: https://www.youtube.com/watch?v=00UQzBFGbvs
        # code from: https://github.com/arembedded/RasPi-Cam-Record-Stream
        # cam-rec-strm.sh modified to run just once and not every x secs
        subprocess.call('make clean', shell=True)
        subprocess.call('make all', shell=True)
        command = f'./cam-rec-strm.sh {time}'
        # the command is quite de same as the one above, check cam-rec-strm.sh
        subprocess.call(command, shell=True)

class ReaderSender(threading.Thread):
    def __init__(self, server, gpio_pin, mpu_address, send_rate, dec_height):
        super().__init__()
        self.server = server
        self.gpio_pin = gpio_pin
        self.mpu_address = mpu_address
        self.send_rate = send_rate
        self.dec_height = dec_height
        self.calibrate_sensors()
    
    def calibrate_sensors(self):
        '''
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpio_pin, GPIO.OUT) # set pin 7 as output (GPIO4)
        GPIO.output(self.gpio_pin, GPIO.LOW)
        
        # initializing and calibrating sensors
        # mpu6050_sensor = mpu6050(self.mpu_address) # enter sensor address
        bus = SMBus(1)
        self.bmp280_sensor = BMP280(i2c_dev=bus)

        # the baseline for relative altitude
        baseline_values = []
        baseline_size = 100
        for _ in range(baseline_size):
            pressure = self.bmp280_sensor.get_pressure()
            baseline_values.append(pressure)
            time.sleep(0.01)
        self.baseline = sum(baseline_values[:-25]) / len(baseline_values[:-25])
        '''
        pass
    
    def start(self):
        while True:
            '''
            altitude = self.bmp280_sensor.get_altitude(qnh=self.baseline) # in meters
            if altitude > self.dec_height:
                GPIO.output(self.gpio_pin, GPIO.HIGH) # set pin 7 to HIGH
                print('SE ENVIA SEÑAL') # send signal to move servo
            
            temperature = self.bmp280_sensor.get_temperature() # in °C
            pressure = self.bmp280_sensor.get_pressure() # in hPa
            '''
            # accel_data = mpu6050_sensor.get_accel_data() # in g
            # ax = accel_data['x']
            # ay = accel_data['y']
            # az = accel_data['z']
            # gyro_data = mpu6050_sensor.get_gyro_data() # in °/sec
            # gx = gyro_data['x']
            # gy = gyro_data['y']
            # gz = gyro_data['z']
            # sensors_data = f'{altitude:06.2f};{temperature:05.2f};{pressure:09.4f};' + \
            #     f'{ax:05.2f};{ay:05.2f};{az:05.2f};{gx:05.2f};{gy:05.2f};{gz:05.2f}'
            '''
            sensors_data = f'{altitude:06.2f};{temperature:05.2f};{pressure:09.4f};' + \
                '00.00;00.00;00.00;00.00;00.00;00.00'
            '''
            
            sensors_data = f'{random.random():05.3f};{random.random():05.3f}' + \
                ';00.00;00.00;00.00;00.00;00.00;00.00;00.00'

            print(f'sensors: {sensors_data}')
            if self.server.clientes:
                self.server.repl(sensors_data)
            time.sleep(self.send_rate) # based on BMP180 and MPU6050 datasheets                     # ADJUST


if __name__ == "__main__":
    port = 8080
    host = socket.gethostname()

    server = Server(port, host)
    reader_sender = ReaderSender(server, 7, 0x68, 0.01, 30)
    reader_sender.start()