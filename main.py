import threading
import time
import ctypes

import cv2



from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window

from client_worker import Client_Worker





# Builder.load_string('''
# <MyCameraApp>:
#     orientation: 'vertical'
#     padding: 20
#
#     BoxLayout:
#         orientation: 'horizontal'
#         pos: 0, 0
#         size_hint_y: None
#         height: 40
#
#         Label:
#             text: 'Cameras: '
#             size_hint_x: None
#             width: 100
#
#         ScrollView:
#             pos: 100, 0
#             size_hint_x: None
#             width: 200
#
#             BoxLayout:
#                 orientation: 'vertical'
#                 spacing: 10
#                 size_hint_y: None
#                 height: self.minimum_height
#
#                 Button:
#                     text: 'Camera1'
#                     size_hint_y: None
#                     height: 40
#                     width: 200
#
#                 Button:
#                     text: 'Camera2'
#                     size_hint_y: None
#                     height: 40
#                     width: 200
#
#                 Button:
#                     text: 'Camera3'
#                     size_hint_y: None
#                     height: 40
#                     width: 200
#
#                 Button:
#                     text: 'Camera4'
#                     size_hint_y: None
#                     height: 40
#                     width: 200
#
#                 Button:
#                     text: 'Camera5'
#                     size_hint_y: None
#                     height: 40
#                     width: 200
#
#     BoxLayout:
#         orientation: 'vertical'
#         pos: 0, 0
#         size_hint_x: None
#         width: 200
#
#         Label:
#             text: 'Available cams'
#             size_hint_x: None
#             width: 200
#
#         ScrollView:
#             pos: 0, 0
#             size_hint: (None, 1)
#             width: 200
#
#             BoxLayout:
#                 orientation: 'vertical'
#                 spacing: 10
#                 size_hint_y: None
#                 height: self.minimum_height
#
#                 TextInput:
#                     hint_text: 'Введите номер камеры'
#                     size_hint_x: None
#                     width: 200
#
#                 Button:
#                     text: 'Найти камеры'
#                     size_hint_x: None
#                     width: 200
#                     on_press: root.on_find_cams_click()
#
#                 Button:
#                     text: 'Добавить'
#                     size_hint_x: None
#                     width: 200
#                     on_press: root.on_confirm_click(text_input_1)
#
#                 Button:
#                     text: 'Удалить'
#                     size_hint_x: None
#                     width: 200
#                     on_press: root.on_confirm_to_delete_click(text_input_1)
# ''')


class CameraScreenApp(App):
    '''
    Класс UI
    Отвечает за весь интерфейс, использует в себе Client-Worker
    '''


    """ !! ATTENTION TO ATTRIBUTES !! """

    MAX_NUMBER_OF_CAMERAS = 10
    MAX_NUMBER_OF_IP_CAMERAS = 10

    # Кодек для записи видео в формате MP4
    FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
    FRAMES_PER_SECOND = 30.0  # Количество кадров в секунду
    RESOLUTION = (640, 480)  # Разрешение видео



    DEMONS = []
    CAM_DICT = {}
    CAM_IP_DICT = {}

    CAM_DICT_ON_AIR = {}
    CAM_IP_DICT_ON_AIR = {}

    NUMBER_OF_AVAILABLE_CAMERAS = 0
    NUMBER_OF_AVAILABLE_IP_CAMERAS = 0

    VIDEO_WRITERS = {}
    VIDEO_WRITERS_IP = {}


    events_to_turn_on = [threading.Event() for i in range(MAX_NUMBER_OF_CAMERAS)]
    events_to_start_recording = [threading.Event() for i in range(MAX_NUMBER_OF_CAMERAS)]
    events_to_stop_recording = [threading.Event() for i in range(MAX_NUMBER_OF_CAMERAS)]
    events_to_turn_off = [threading.Event() for i in range(MAX_NUMBER_OF_CAMERAS)]

    events_to_turn_on_ip = {}
    events_to_start_recording_ip = {}
    events_to_stop_recording_ip = {}
    events_to_turn_off_ip = {}


    # Основной контейнер для размещения элементов
    layout = BoxLayout(orientation='vertical', height=Window.height, width=Window.width,padding=20)
    # Создаем ScrollView
    scroll_view = ScrollView(size_hint=(None, 1), width=200, height=Window.height * 0.5)
    inner_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=500)
    available_cams = []

    cams_box = BoxLayout(orientation='vertical', spacing=10, size_hint_x=None,
                         size_hint_y=None, width=Window.width * 0.5, height=Window.height * 0.5)
    def build(self):



        button_container = BoxLayout(orientation='vertical', size_hint=(None, None), size=(200, 150),
                                     pos_hint={'right': 1, 'top': 1})

         # Создаем три кнопки
        self.button1 = Button(text='ON', background_normal='кнопки2.png',
            background_down='кнопки.png')
        self.button2 = Button(text='RECORD', disabled=True, background_normal='кнопки2.png',
            background_down='кнопки.png')
        self.button3 = Button(text='STOP RECORD', disabled=True, background_normal='кнопки2.png',
            background_down='кнопки.png')
        self.button4 = Button(text='OFF', disabled=True, background_normal='кнопки2.png',
            background_down='кнопки.png')

        # self.button_transfer_test = Button(text='SEND TEST_VIDEO', disabled=False)

        # Привязываем обработчики событий к кнопкам
        self.button1.bind(on_press=self.on_button1_click)
        self.button2.bind(on_press=self.on_button2_click)
        self.button3.bind(on_press=self.on_button3_click)
        self.button4.bind(on_press=self.on_button4_click)
        # self.button_transfer_test.bind(on_press=self.test_transfer)

        button_container.add_widget(self.button1)
        button_container.add_widget(self.button2)
        button_container.add_widget(self.button3)
        button_container.add_widget(self.button4)
        # button_container.add_widget(self.button_transfer_test)



        # Контейнер для текстового поля и кнопки подтверждения
        text_input_container = BoxLayout(orientation='vertical', size_hint=(None, None),
                                         width=Window.width * 0.2, height=Window.height * 0.2,
                                         pos_hint={'left': 1, 'top': 1})

        # Создаем текстовое поле
        text_input_1 = TextInput(hint_text='Введите rtsp адрес')

        # Кнопка подтверждения

        find_cams_button = Button(text='Найти камеры', background_normal='кнопки2.png',
            background_down='кнопки.png')
        confirm_button = Button(text='Добавить', background_normal='кнопки2.png',
            background_down='кнопки.png')
        confirm_to_delete = Button(text='Удалить', background_normal='кнопки2.png',
            background_down='кнопки.png')

        find_cams_button.bind(on_press=lambda instance: self.on_find_cams_click())
        confirm_button.bind(on_press=lambda instance: self.on_confirm_click(text_input_1))
        confirm_to_delete.bind(on_press=lambda instance: self.on_confirm_to_delete_click(text_input_1))

        text_input_container.add_widget(text_input_1)
        text_input_container.add_widget(find_cams_button)
        text_input_container.add_widget(confirm_button)
        text_input_container.add_widget(confirm_to_delete)




        self.inner_layout.bind(minimum_height=self.inner_layout.setter('height'))


        # Создаем кнопки для камер
        for camera in self.available_cams:
            button = Button(text=camera, size_hint_y=None, height=40, width=200)
            self.inner_layout.add_widget(button)

        # Добавляем в ScrollView содержимое
        self.scroll_view.add_widget(self.inner_layout)

        # Создаем лейбл "Available cams"
        label = Label(text='Available cams', size_hint_x=None, width=200, color=get_color_from_hex('#2F7C12'))
        # self.cams_box.add_widget(label)
        # self.cams_box.add_widget(self.scroll_view)

        # Создаем бокс для объединения text_input_container и cams_box
        combined_box = BoxLayout(orientation='vertical', spacing=5, size_hint=(None, None),
                                 size=(Window.width * 0.5, Window.height), pos_hint={'left': 1, 'bottom': 1})
        # Добавляем text_input_container и cams_box в объединенный бокс
        combined_box.add_widget(label)
        combined_box.add_widget(self.scroll_view)
        combined_box.add_widget(text_input_container)

        anchor_layout2 = AnchorLayout(anchor_x='right', anchor_y='bottom')
        anchor_layout2.add_widget(button_container)

        self.layout.add_widget(combined_box)
        self.layout.add_widget(anchor_layout2)

        # Добавляем обработчик изменения размеров окна
        Window.bind(on_resize=self.on_window_resize)

        # Устанавливаем фоновое изображение
        with self.layout.canvas.before:
            self.bgbg = Rectangle(source='img_1.png', pos=self.layout.pos,
                                  size=self.layout.size)

            # Замените 'новый_значок.ico' на путь к вашему новому значку
        self.set_window_icon('значок.png')

        return self.layout

    def set_window_icon(self, icon_path):
        if hasattr(ctypes.windll, 'kernel32'):
            ctypes.windll.kernel32.SetConsoleTitleW("My Kivy App")  # Устанавливаем заголовок консоли для ctypes
            ctypes.windll.kernel32.SetConsoleIcon(
                ctypes.windll.shell32.ShellExecuteW(0, "c_char_p", "pythonw", "c_char_p", 0,
                                                    0))  # Устанавливаем значок для окна
            ctypes.windll.kernel32.SetConsoleTitleW("My Kivy App")  # Восстанавливаем заголовок консоли
        self.icon = icon_path


    def on_window_resize(self, window, width, height):
        # Обновляем размеры основного контейнера
        self.layout.size = (width, height)

        self.bgbg.size = self.layout.size

        return self.layout

    def on_button1_click(self, instance):
        if self.NUMBER_OF_AVAILABLE_CAMERAS > 0 or self.NUMBER_OF_AVAILABLE_IP_CAMERAS > 0:

            '''👇👇👇 IMPLEMENTATION OF CLIENT_WORKER IS HERE 👇👇👇'''
            for i in self.CAM_DICT:
                if i not in self.CAM_DICT_ON_AIR:
                    self.CAM_DICT_ON_AIR[i] = 1
                    client_worker = Client_Worker()
                    thread = threading.Thread(target=client_worker.display_camera_stream, args=(
                        i, f"Camera_{i}", self.FOURCC, self.FRAMES_PER_SECOND, self.RESOLUTION, self.VIDEO_WRITERS,
                        self.events_to_turn_on, self.events_to_start_recording, self.events_to_stop_recording,
                        self.events_to_turn_off))
                    thread.daemon = True
                    thread.start()
                    self.DEMONS.append(thread)
                    print(self.CAM_DICT_ON_AIR)

            for ip in self.CAM_IP_DICT:
                if ip not in self.CAM_IP_DICT_ON_AIR:
                    self.CAM_IP_DICT_ON_AIR[ip] = 1
                    client_worker = Client_Worker()
                    thread = threading.Thread(target=client_worker.display_camera_stream,
                                              args=(
                                                  ip, f"Camera_{ip}", self.FOURCC, self.FRAMES_PER_SECOND, self.RESOLUTION,
                                                  self.VIDEO_WRITERS_IP,
                                                  self.events_to_turn_on_ip, self.events_to_start_recording_ip,
                                                  self.events_to_stop_recording_ip,
                                                  self.events_to_turn_off_ip
                                              )
                                              )
                    thread.daemon = True
                    thread.start()
                    self.DEMONS.append(thread)
                    print(self.CAM_DICT_ON_AIR)
                    print(self.CAM_IP_DICT_ON_AIR)

            self.button2.disabled = False
            self.button3.disabled = True
            self.button4.disabled = False

            print(self.DEMONS)
            print('ON')
            print(self.DEMONS)

    def on_button2_click(self, instance):
        if self.NUMBER_OF_AVAILABLE_CAMERAS > 0:
            for i in self.CAM_DICT:
                self.events_to_start_recording[i].set()

            self.button3.disabled = False
            self.button2.disabled = True
            self.button4.disabled = True

        if self.NUMBER_OF_AVAILABLE_IP_CAMERAS > 0:
            for ip in self.CAM_IP_DICT:
                self.events_to_start_recording_ip[ip].set()


            self.button3.disabled = False
            self.button2.disabled = True
            self.button4.disabled = True

            print('RECORD')

    def on_button3_click(self, instance):
        if self.NUMBER_OF_AVAILABLE_CAMERAS > 0:
            for i in self.CAM_DICT:
                self.events_to_stop_recording[i].set()

            self.button3.disabled = True
            self.button2.disabled = False
            self.button4.disabled = False

        if self.NUMBER_OF_AVAILABLE_IP_CAMERAS > 0:
            for ip in self.CAM_IP_DICT:
                self.events_to_stop_recording_ip[ip].set()

            self.button3.disabled = True
            self.button2.disabled = False
            self.button4.disabled = False
            print('STOP')

    def on_button4_click(self, instance):
        if self.NUMBER_OF_AVAILABLE_IP_CAMERAS > 0:
            for ip in self.CAM_IP_DICT:
                self.events_to_turn_off_ip[ip].set()
                self.CAM_IP_DICT_ON_AIR.pop(ip, None)

            self.button3.disabled = True
            self.button2.disabled = True
            self.button4.disabled = True

        if self.NUMBER_OF_AVAILABLE_CAMERAS > 0:
            for i in self.CAM_DICT:
                self.events_to_turn_off[i].set()
                self.CAM_DICT_ON_AIR.pop(i, None)

            self.button3.disabled = True
            self.button2.disabled = True
            self.button4.disabled = True

            print(self.CAM_DICT)
            print(self.CAM_IP_DICT)
            print(self.CAM_DICT_ON_AIR)
            print(self.CAM_IP_DICT_ON_AIR)

            print('OFF')



    def on_find_cams_click(self):
        client_worker = Client_Worker()

        inner_cameras = client_worker.get_list_of_all_available_inner_cameras()
        print(inner_cameras)
        for cam in inner_cameras:
            if cam[0] not in self.CAM_DICT:
                if not self.button_exists_with_text(cam[1]):
                    self.CAM_DICT[int(cam[0])] = cam[1]
                    self.NUMBER_OF_AVAILABLE_CAMERAS += 1
                    button_grid = GridLayout(cols=2, spacing=10, size_hint=(None, None))
                    button_grid.bind(minimum_height=button_grid.setter('height'))

                    button1 = Button(text=cam[1], size_hint=(None, None), height=25, width=150, background_normal='кнопки2.png',
            background_down='кнопки.png')
                    button1.shorten = True
                    button1.text_size = (button1.width, button1.height)
                    button2 = Button(text='Yes', size_hint=(None, None), height=25, width=40, background_normal='кнопки2.png',
            background_down='кнопки.png')
                    button2.bind(on_press=self.toggle_button_text)

                    button_grid.add_widget(button1)
                    button_grid.add_widget(button2)

                    self.inner_layout.add_widget(button_grid)
                    self.available_cams.append(cam[1])

        print("Updated CAM_DICT:", self.CAM_DICT)
        print(self.available_cams)

    def on_confirm_click(self, text_input_1):
        entered_text = text_input_1.text
        print(f'Введенный текст: {entered_text}')
        text_input_1.text = ''  # Очистить текстовое поле

        w = Client_Worker()
        is_url, ip_port = w.url_to_ip_port(entered_text)
        if not is_url:
            try:
                sub_index_list = [index for index, element in enumerate(w.get_list_of_all_available_inner_cameras()) if element[1] == entered_text]

                if len(sub_index_list) == 0:
                    pass
                else:
                    sub_index = sub_index_list[0]
                    idx = w.get_list_of_all_available_inner_cameras()[sub_index][0]
                    if int(idx) not in self.CAM_DICT:
                        if not self.button_exists_with_text(entered_text):
                            self.NUMBER_OF_AVAILABLE_CAMERAS += 1

                            self.CAM_DICT[int(idx)] = entered_text

                            button_grid = GridLayout(cols=2, spacing=10, size_hint=(None, None))
                            button_grid.bind(minimum_height=button_grid.setter('height'))

                            button1 = Button(text=entered_text, size_hint=(None, None), height=25, width=150, background_normal='кнопки2.png',
            background_down='кнопки.png')
                            button1.text_size= (button1.width, button1.height)
                            button2 = Button(text='Yes', size_hint=(None, None), height=25, width=40, background_normal='кнопки2.png',
            background_down='кнопки.png')
                            button2.bind(on_press=self.toggle_button_text)

                            button_grid.add_widget(button1)
                            button_grid.add_widget(button2)

                            self.inner_layout.add_widget(button_grid)
                            self.available_cams.append(entered_text)

                        print(self.available_cams)
                        print(self.CAM_DICT)

            except:
                pass


        else:
            try:
                url = entered_text
                if url not in self.CAM_IP_DICT:
                    if not self.button_exists_with_text(url):
                        self.NUMBER_OF_AVAILABLE_IP_CAMERAS += 1

                        self.CAM_IP_DICT[url] = 1

                        self.events_to_turn_on_ip[url] = threading.Event()
                        self.events_to_start_recording_ip[url] = threading.Event()
                        self.events_to_stop_recording_ip[url] = threading.Event()
                        self.events_to_turn_off_ip[url] = threading.Event()

                        button_grid = GridLayout(cols=2, spacing=10, size_hint=(None, None))
                        button_grid.bind(minimum_height=button_grid.setter('height'))

                        button1 = Button(text=url, size_hint=(None, None), height=25, width=150, shorten=True, background_normal='кнопки2.png',
            background_down='кнопки.png')
                        button1.text_size = (button1.width, button1.height)
                        button2 = Button(text='Yes', size_hint=(None, None), height=25, width=40, background_normal='кнопки2.png',
            background_down='кнопки.png')
                        button2.bind(on_press=self.toggle_button_text)

                        button_grid.add_widget(button1)
                        button_grid.add_widget(button2)

                        self.inner_layout.add_widget(button_grid)
                        self.available_cams.append(url)

                    print(self.available_cams)
                    print(self.CAM_IP_DICT)

            except:
                pass

    def on_confirm_to_delete_click(self, text_input_2):
        try:
            w = Client_Worker()
            entered_text = text_input_2.text
            print(f'Введенный текст: {entered_text}')
            text_input_2.text = ''  # Очистить текстовое поле

            is_url, ip_port = w.url_to_ip_port(entered_text)

            if is_url:
                url = entered_text
                if url in self.CAM_IP_DICT:
                    if url not in self.CAM_IP_DICT_ON_AIR:
                        self.NUMBER_OF_AVAILABLE_IP_CAMERAS -= 1
                        self.CAM_IP_DICT.pop(url, None)
                        print(self.CAM_IP_DICT)
                        print(self.CAM_IP_DICT_ON_AIR)


                        for child in self.inner_layout.children:
                            if isinstance(child, GridLayout):
                                # Проверяем, есть ли в BoxLayout дочерние элементы и первая кнопка
                                if len(child.children) >= 1 and isinstance(child.children[1], Button):
                                    button_text = child.children[1].text
                                    if button_text == url:
                                        # Нашли соответствующий BoxLayout, удаляем его
                                        self.inner_layout.remove_widget(child)
                        if entered_text in self.available_cams:
                            self.available_cams.remove(entered_text)

            else:

                sub_index = [index for index, element in enumerate(w.get_list_of_all_available_inner_cameras()) if
                             element[1] == entered_text][0]
                idx = w.get_list_of_all_available_inner_cameras()[sub_index][0]

                if int(idx) in self.CAM_DICT:
                    if int(idx) not in self.CAM_DICT_ON_AIR:
                        self.NUMBER_OF_AVAILABLE_CAMERAS -= 1
                        self.CAM_DICT.pop((int(idx)), None)
                        print(self.CAM_DICT)
                        print(self.CAM_DICT_ON_AIR)

                        for child in self.inner_layout.children:
                            if isinstance(child, GridLayout):
                                # Проверяем, есть ли в BoxLayout дочерние элементы и первая кнопка
                                if len(child.children) >= 1 and isinstance(child.children[1], Button):
                                    button_text = child.children[1].text
                                    if button_text == entered_text:
                                        # Нашли соответствующий BoxLayout, удаляем его
                                        self.inner_layout.remove_widget(child)
                        if entered_text in self.available_cams:
                            self.available_cams.remove(entered_text)


        except:
            pass

    def toggle_button_text(self, instance):
        try:
            w = Client_Worker()
            camera_name = instance.parent.children[1].text
            is_url, ip_port = w.url_to_ip_port(camera_name)

            if instance.text == 'Yes':
                if is_url:
                    if camera_name not in self.CAM_IP_DICT_ON_AIR and camera_name in self.CAM_IP_DICT:
                        self.CAM_IP_DICT.pop(camera_name, None)
                        self.NUMBER_OF_AVAILABLE_IP_CAMERAS -= 1
                        instance.text = 'No'
                        self.available_cams.remove(camera_name)

                else:
                    sub_index = [index for index, element in enumerate(w.get_list_of_all_available_inner_cameras()) if
                                 element[1] == camera_name][0]
                    idx = w.get_list_of_all_available_inner_cameras()[sub_index][0]

                    if int(idx) not in self.CAM_DICT_ON_AIR and int(idx) in self.CAM_DICT:
                        self.CAM_DICT.pop(int(idx), None)
                        self.NUMBER_OF_AVAILABLE_CAMERAS -= 1

                        instance.text = 'No'
                        self.available_cams.remove(camera_name)



            else:
                if is_url:
                    if camera_name not in self.CAM_IP_DICT_ON_AIR and camera_name not in self.CAM_IP_DICT:
                        self.CAM_IP_DICT[camera_name] = 1
                        self.NUMBER_OF_AVAILABLE_IP_CAMERAS += 1
                        instance.text = 'Yes'
                        self.available_cams.append(camera_name)
                else:
                    sub_index = [index for index, element in enumerate(w.get_list_of_all_available_inner_cameras()) if
                                 element[1] == camera_name][0]
                    idx = w.get_list_of_all_available_inner_cameras()[sub_index][0]

                    if int(idx) not in self.CAM_DICT_ON_AIR and int(idx) not in self.CAM_DICT:
                        self.CAM_DICT[int(idx)] = camera_name
                        self.NUMBER_OF_AVAILABLE_CAMERAS += 1

                        instance.text = 'Yes'
                        self.available_cams.append(camera_name)


        except:
            pass

        print(self.available_cams)
        print(self.CAM_DICT)
        print(self.CAM_IP_DICT)

    def button_exists_with_text(self, text):
        # Проверяем, есть ли уже кнопка с указанным текстом в inner_layout
        for widget in self.inner_layout.children:
            if isinstance(widget, GridLayout):
                # Перебираем все GridLayout внутри inner_layout
                for button in widget.children:
                    if isinstance(button, Button) and button.text == text:
                        return True
        return False

if __name__ == '__main__':

    CameraScreenApp().run()