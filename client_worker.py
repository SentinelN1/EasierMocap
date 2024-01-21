# CREATED BY RED
import pickle
import socket
import threading
import time
from multiprocessing import Process

import cv2
import pysftp
from pygrabber.dshow_graph import FilterGraph
import os
import json
from datetime import datetime
import subprocess
import platform
import re
import time
import ipaddress

class Client_Worker():
    def __init__(self):
        self.internet_connection = False
        self.dependencies_for_EM = []
        self.inner_cameras = []
        self.ip_cameras = []
        self.ID = 0
        self.names = []
        self.NUMBER_OF_FILES = len(self.names)

    def check_internet_connection(self):
        '''
            Update inet_connection status of a client
        '''
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=4)
            self.internet_connection = True
        except OSError:
            self.internet_connection = False

    def get_list_of_all_available_inner_cameras(self):
        '''
        Get list of available cams
        :return: list of pairs (id, name)
        '''
        graph = FilterGraph()
        return list(enumerate(graph.get_input_devices()))

    def recieve_data_from_server(self, server_host, server_port, save_path='received_videos'):
        os.makedirs(save_path, exist_ok=True)

        # Создаем сокет
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_host, server_port))
        server_socket.listen(1)

        print(f"Server listening on {server_host}:{server_port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")

            try:
                # Получаем и декодируем JSON-строку с метаданными
                json_data = conn.recv(4096).decode()
                data = json.loads(json_data)

                # Извлекаем видео, инструкции и имя файла из данных
                video_name = data['video_name']
                annotations = data['annotations']

                # Создаем файл для сохранения видео
                save_file_path = os.path.join(save_path, video_name)
                with open(save_file_path, 'wb') as file:
                    # Принимаем блоки видеофайла и записываем их в файл
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        file.write(data)

                '''here add function to notify client about successful receiving'''

            finally:
                conn.close()

    def send_data(self, video_path, instructions, server_host, server_port):
        '''
        Transfering video to server
        :param video_path:
        :param instructions:
        :param server_host:
        :param server_port:
        :return:
        '''
        with open(video_path, 'rb') as file:
            # Создаем сокет
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_host, server_port))

            try:
                # Формируем данные для отправки (видео и инструкции) в формате JSON
                data_to_send = {
                    'video_name': os.path.basename(video_path),
                    'instructions': instructions,
                }
                json_data = json.dumps(data_to_send)

                # Отправляем JSON-строку с метаданными
                client_socket.send(json_data.encode())

                # Отправляем видеофайл в блоках
                while True:
                    data = file.read(1024)  # Читаем 1024 байта данных
                    if not data:
                        break
                    client_socket.send(data)

            finally:
                # Закрываем сокет после отправки данных
                client_socket.close()
                print('closed')

    def display_camera_stream(self,
                              stream_source,
                              window_name,
                              FOURCC,
                              FRAMES_PER_SECOND,
                              RESOLUTION,
                              VIDEO_WRITERS,
                              events_to_turn_on,
                              events_to_start_recording,
                              events_to_stop_recording,
                              events_to_turn_off
                              ):

        # global VIDEO_WRITERS
        print('CAMERA ', stream_source, ' IS AWAKEN NOW')

        try:
            is_url, ip = self.url_to_ip(stream_source)

            camera = cv2.VideoCapture()

            if is_url:
                timeout_ms = 5000
                camera = cv2.VideoCapture(stream_source,
                                          apiPreference=cv2.CAP_FFMPEG,
                                          params=[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms])
            else:
                camera = cv2.VideoCapture(stream_source)

            if not camera.isOpened():
                print(f"Connection to {stream_source} failed")
                raise ConnectionError


            if is_url:
                window_name = ip
        except:
            return

        while not events_to_turn_off[stream_source].is_set():

            while not events_to_start_recording[stream_source].is_set():

                ret, frame = camera.read()
                cv2.imshow(window_name, frame)

                if cv2.waitKey(1) == ord('q'):
                    break

                if events_to_turn_off[stream_source].is_set():
                    events_to_turn_off[stream_source].clear()
                    camera.release()
                    cv2.destroyWindow(window_name)
                    return

            events_to_start_recording[stream_source].clear()
            print(f"Camera {stream_source} started recording")


            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            frame_width = camera.get(3)
            frame_height = camera.get(4)
            frame_rate = camera.get(5)
            resolution = (int(frame_width), int(frame_height))

            VIDEO_WRITERS[stream_source] = cv2.VideoWriter(
                f'CLIENT_storage/{window_name}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4',
                fourcc,
                frame_rate,
                resolution)

            while not events_to_stop_recording[stream_source].is_set():

                ret, frame = camera.read()

                if ret:
                    cv2.imshow(window_name, frame)
                    VIDEO_WRITERS[stream_source].write(frame)
                if cv2.waitKey(1) == ord('q'):
                    VIDEO_WRITERS[stream_source].release()
                    break

            events_to_stop_recording[stream_source].clear()
            VIDEO_WRITERS[stream_source].release()

        events_to_turn_off[stream_source].clear()
        camera.release()
        cv2.destroyWindow(window_name)
        return

    def install_required_dependencies_for_EasyMocap(self):
        try:
            command = ''
            os = platform.system()
            if os == 'Windows':
                command += 'python'
            elif os in ['Linux', 'Darwin']:
                command += 'python3'
            command += ' -m pip install -r easymocap_requirements.txt'
            subprocess.run(command, check=True)

            print("Successfully installed all EasyMocap requirements.")

        except subprocess.CalledProcessError as err:
            print(f'An error occurred: {err}')

    def check_correct_ip_address(self, address):
        try:
            ipaddress.ip_address(address)
            return True
        except:
            return False

    def check_correct_port(self, port):
        try:
            tmp = int(port)
            if tmp < 0 or tmp >= 2 ** 16:
                raise ValueError
            print(f"Port: {port}")
            return True

        except ValueError:
            print(f"{port} is an invalid port number.")
            return False

    def check_correct_ip_port(self, ip_port):
        try:
            lst = ip_port.split(":")
            if len(lst) != 2:
                raise ValueError
            (ip, port) = lst
            return self.check_correct_ip_address(ip) and self.check_correct_port(port)
        except:
            return False

    def url_to_ip(self, url):
        try:
            ip_pattern = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
            ip = re.findall(ip_pattern, url)[0]
            if not self.check_correct_ip_address(ip):
                raise ValueError
            return (True, ip)

        except:
            print("Couldn't extract ip from url")
            return (False, url)

    def url_to_ip_port(self, url):
        try:
            pattern = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}')
            ip_port = re.findall(pattern, url)[0]
            if not self.check_correct_ip_port(ip_port):
                raise ValueError

            return (True, ip_port)

        except:
            print("Couldn't extract ip:port from url")
            return (False, url)

    def check_camera_connection(self, source, timeout_seconds=5):
        try:
            capture = cv2.VideoCapture(
                source,
                apiPreference=cv2.CAP_FFMPEG,
                params=[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_seconds * 1000]
            )

            if not capture.isOpened():
                raise ConnectionError

            print(f"Successfully connection to {source}")
            return True

        except:
            print(f"Failed connection to {source}")
            return False










    '''if u see this line that means everything fine with data-transfer :)'''


    def transfer_video_via_sftp(self, local_path, remote_path, hostname, username, password, port=22):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # Отключаем проверку ключей хоста

            # Устанавливаем соединение с сервером SFTP
            with pysftp.Connection(
                    host=hostname,
                    username=username,
                    password=password,
                    port=port,
                    cnopts=cnopts
            ) as sftp:
                print(f"Connected to {hostname}")

                # Передаем видеофайл
                sftp.put(local_path, remote_path)

                print("File transfer successful")

        except Exception as e:
            print(f"Error: {e}")

    def download_file_via_sftp(self, remote_path, local_path, hostname, username, password, port=22):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # Отключаем проверку ключей хоста

            # Устанавливаем соединение с сервером SFTP
            with pysftp.Connection(
                    host=hostname,
                    username=username,
                    password=password,
                    port=port,
                    cnopts=cnopts
            ) as sftp:
                print(f"Connected to {hostname}")

                # Загружаем файл с сервера
                sftp.get(remote_path, local_path)

                print(f"File downloaded to {local_path}")

        except Exception as e:
            print(f"Error: {e}")

    def send_preordered_receipt(self, files, meta, server_host, server_port):
        print('here!')
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_host, server_port))
        print('here!')
        new_files = []
        for name in files:
            extracted_name = os.path.basename(name)
            new_files.append(extracted_name)

        data_to_send = {
            'names': new_files,
            'meta': meta
        }
        pkl_data = pickle.dumps(data_to_send)
        conn.sendall(pkl_data)

        self.ID = int(conn.recv(1024).decode('utf-8'))

        conn.close()

    def send_video(self, name, server_host, server_port):
        '''send video from CLIENT to SERVER'''

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_host, server_port))

        data_to_send = {
            'name': os.path.basename(name),
            'id': self.ID
        }

        print(data_to_send)

        pkl_data = pickle.dumps(data_to_send)
        conn.sendall(pkl_data)

        try:

            # with open(name, 'rb') as file:
            #     while True:
            #         data = file.read(1024)
            #
            #         if not data:
            #             conn.sendall(b'stop')
            #             break
            #         conn.sendall(data)

            self.transfer_video_via_sftp(name, '/root/PROJECT_1462/SERVER/SERVER_storage/' + os.path.basename(name),
                                         '213.171.10.222', 'root', 'sk47K_Em8B5XVB', 22)

            data_to_send = {
                'resp': 'YES'
            }

            print(data_to_send)

            pkl_data = pickle.dumps(data_to_send)
            conn.sendall(pkl_data)

        except:
            pass

        conn.close()

    def get_NUMBER_OF_FILES(self, meta):
        '''return and set NUMBER OF FILES for current meta
        '''

        # change

        return 1

    def punch_container(self, server_host, server_port):
        '''check readiness of pipeline'''

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((server_host, server_port))

        data_to_send = {
            'id': self.ID
        }
        pkl_data = pickle.dumps(data_to_send)

        conn.sendall(pkl_data)

        time.sleep(5)

        pkl_data = conn.recv(4096)
        data = pickle.loads(pkl_data)
        resp = data['resp']

        print('PUNCH!')
        print('response from defender: ', resp)

        # if resp == self.get_NUMBER_OF_FILES(self.META):
        if resp == self.N:
            conn.close()
            print('getting data back...')

            names = data['names']
            print('number of files: ', resp)
            print('names of files: ', names)

            # return True
            for name in names:
                # self.get_video_back(self.ID, name, server_host, server_port)
                self.download_file_via_sftp('/root/PROJECT_1462/SERVER/SERVER_storage/' + os.path.basename(name),
                                            r'CLIENT_storage/' + os.path.basename(
                                                name), '213.171.10.222', 'root', 'sk47K_Em8B5XVB', 22)


                print('FILE SUCCESSFULY DOWNLOADED ')
                time.sleep(4)

            return True

        else:
            # return False
            conn.close()
            return False

    def get_video_back(self, id, name, server_host, server_port):
        '''recieve data from SERVER to CLIENT'''
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((server_host, 1337))

            conn.send(os.path.basename(name).encode('utf-8'))

            with open('CLIENT_storage/' + os.path.basename(name), 'wb') as file:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    file.write(data)

            print(f'recieved:  {os.path.basename(name)}')

        except:
            pass

        finally:
            conn.close()

    def punch_wrapper(self, server_host, server_port):
        while True:
            OK = self.punch_container(server_host, server_port)

            if OK:
                print('i catch\'em all !!')
                break

            else:
                print('waitin response')
                time.sleep(5)
                continue

    def submit(self, DATA, server_host, server_port):

        self.META = DATA['meta']
        # N = self.get_NUMBER_OF_FILES(DATA['meta'])
        if DATA['meta']['face_hunting'] == 'NO':
            self.N = 2 * len(DATA['names'])
        else:
            self.N = len(DATA['names'])
        print('sending receipt')
        print(DATA['names'], DATA['meta'], server_host, server_port)
        self.send_preordered_receipt(DATA['names'], DATA['meta'], server_host, server_port)

        print(self.ID)

        # for name in DATA['names']:
        #     self.send_video(name, server_host, 1336)
        #     time.sleep(6)

        for name in DATA['names']:
            # self.transfer_video_via_sftp(name, '/root/PROJECT_1462/SERVER/SERVER_storage/'+os.path.basename(name), '213.171.10.222', 'root', 'sk47K_Em8B5XVB', 22)
            self.send_video(name, server_host, 1336)
            time.sleep(6)

        self.punch_wrapper(server_host, 1462)






if __name__ == "__main__":
    client_worker = Client_Worker()

    # client_worker.check_correct_ip_address("192.168.0.0")
    # client_worker.check_correct_port("df2g3h45jk")
    # client_worker.check_correct_ip_port("192.168:22hbh:8080")
    # ip_port = client_worker.url_to_ip_port("rtsp://172.20.10.4:8080/h264_pcm.sdp")
    # print(ip_port)

    # lst = client_worker.get_list_of_all_available_inner_cameras()
    # print(lst)

    # w1 = Client_Worker()

    # print(w1.internet_connection)
    # w1.check_internet_connection()
    # print(w1.internet_connection)

    # w1.get_list_of_all_available_inner_cameras()
    # print(w1.inner_cameras)

    video_path1 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T1.mp4'
    video_path2 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T2.mp4'
    video_path3 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T3.mp4'

    instructions = {'action': 'process_video', 'parameters': {'threshold': 0.5}}
    # server_host = '127.0.0.1'  # Замените на IP-адрес вашего сервера
    # server_port = 12345  # Замените на порт вашего сервера

    # w1.send_data(video_path, instructions, server_host, server_port)

    w = Client_Worker()

    DATA = {
        'names': ['C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_1.mp4', 'C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_T1.mp4'],
        'internet_mode': 'online',
        'meta': instructions
    }

    # w.submit(DATA, '213.171.10.222', 12345)



    # subprocess.run(['python', '-c', f'from client_worker import submit; submit({DATA}, {"213.171.10.222"}, {12345})'])
    #
    # serialized_instance = pickle.dumps(w)
    # subprocess.run(['python', '-c',
    #                 f'import pickle; my_instance = pickle.loads({serialized_instance}); my_instance.submit({DATA}, {"213.171.10.222"}, {12345});'])

    process = Process(target=w.submit, args=(DATA, '213.171.10.222', 12345))

    # Запускаем процесс
    process.start()

    # Ждем завершения процесса
    process.join()

    print("Main process continues...")