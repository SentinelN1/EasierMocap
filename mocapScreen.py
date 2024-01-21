import json
import subprocess
import threading
import time
from multiprocessing import Process
import ctypes

import cv2

import os
# os.environ["KIVY_NO_CONSOLELOG"] = "1"
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from PyQt5.QtWidgets import QFileDialog, QApplication, QProgressDialog, QLabel, QVBoxLayout, QWidget
from kivy.uix.gridlayout import GridLayout
import sys
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

from client_worker import Client_Worker
from STATIC_DATA import OPTIONS, MODES, RES, WORK


class CustomSpinnerOption(SpinnerOption):
    background_normal = 'кнопки2.png'
    background_down = 'кнопки.png'


class MocapScreenApp(App):
    # Основной контейнер для размещения элементов
    main_layout = BoxLayout(orientation='horizontal', height=Window.height, width=Window.width)

    chosen_internet_mode = "online"
    chosen_model_builder_mode = ""
    chosen_fps = "1.0"
    chosen_keypoints_model = "mp-best"
    chosen_parts = []

    selected_files = []
    chosen_face_hunting = ""

    def build(self):
        # Верхний бокс-лейаут для левой половины экрана
        self.left_layout = BoxLayout(orientation='vertical', height=self.main_layout.height,
                                width=self.main_layout.width * 0.5)

        # Bottom container с кнопкой SUBMIT
        self.bottom_container = BoxLayout(orientation='vertical', height=self.left_layout.height * 0.5,
                                     width=self.left_layout.width)

        # Кнопка SUBMIT
        self.button_transfer_test = Button(
            text='SUBMIT',
            disabled=False,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            pos_hint={'center_x': 0.5, 'bottom': 1},  # Прилегает к нижней границе
            background_normal='кнопки2.png',
                background_down='кнопки.png'
        )
        self.button_transfer_test.bind(on_press=self.test_transfer)

        # Создаем выпадающий список для для режимов
        options = ['online', 'offline']
        self.mode_layout = Spinner(
            text='Выберите мод',
            values=options,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            pos_hint={'center_x': 0.5, 'top': 1},  # Прилегает к верхней границе
            background_normal='кнопки2.png',
            background_down='кнопки.png',
            option_cls=CustomSpinnerOption
        )
        self.mode_layout.bind(text=self.on_mode_layout_select)

        self.selected_files_button = Button(text="Выбрать файлы",
                                            disabled=False,
                                            size_hint_y=None,
                                            size_hint_x=None,
                                            height=self.bottom_container.height * 0.1,
                                            width=self.bottom_container.width * 0.5,
                                            pos_hint={'center_x': 0.5, 'bottom': 1},
                                            on_press=self.doo3,
                                            background_normal='кнопки2.png',
                                            background_down='кнопки.png'
                                            )
        # BoxLayout для лейбла и ScrollView
        self.label_and_scrollview_layout = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(self.bottom_container.width * 0.5, self.bottom_container.height * 0.5),
            pos_hint={'center_x': 0.5, 'bottom': 1},
        )

        # Лейбл с текстом "Выбранные файлы"
        self.label = Label(
            text='Выбранные файлы',
            size_hint=(None, None),
            height=self.bottom_container.height * 0.1,
            width=self.label_and_scrollview_layout.width,
            text_size=(self.label_and_scrollview_layout.width, None),
            halign='center',  # Центрирование текста по горизонтали
            valign='middle'  # Центрирование текста по вертикали
        )
        # Добавляем фон цвета серого
        with self.label.canvas.before:
            Color(1, 1, 1, 1)  # RGBA цвет (серый)
            self.bg_rect = Rectangle(source='кнопки2.png', pos=self.label.pos, size=self.label.size)

        self.label.bind(pos=self.update_bg_rect, size=self.update_bg_rect)


        # ScrollView для отображения выбранных файлов
        self.selected_files_scrollview = ScrollView(
            size_hint_y=None,
            size=(self.label_and_scrollview_layout.width, self.label_and_scrollview_layout.height * 0.5),
        )

        # GridLayout внутри ScrollView
        self.selected_files_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=5,
        )
        self.selected_files_layout.bind(minimum_height=self.selected_files_layout.setter('height'))

        # Добавляем GridLayout в ScrollView
        self.selected_files_scrollview.add_widget(self.selected_files_layout)

        # Добавляем лейбл и ScrollView в BoxLayout
        self.label_and_scrollview_layout.add_widget(self.label)
        self.label_and_scrollview_layout.add_widget(self.selected_files_scrollview)

        # создаем всплывающий список для режима сборки
        options = ['Include', 'Exclude']
        self.build_spinner = Spinner(
            text='Face_hunting',
            values=options,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            pos_hint={'center_x': 0.5, 'top': 1},  # Прилегает к верхней границе
            background_normal='кнопки2.png',
            background_down='кнопки.png',
            option_cls=CustomSpinnerOption
        )

        self.build_spinner.bind(text=self.on_build_spinner_select)

        # Добавляем элементы в bottom_container
        self.bottom_container.add_widget(self.build_spinner)
        self.bottom_container.add_widget(self.mode_layout)
        self.bottom_container.add_widget(self.selected_files_button)
        self.bottom_container.add_widget(self.label_and_scrollview_layout)
        self.bottom_container.add_widget(self.button_transfer_test)

        # Создаем выпадающий список для верхней части левого бокс-лейаута
        options = ['extract_keypoints', 'mocap']
        self.spinner_upper = Spinner(
            text='Выберите опцию',
            values=options,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            background_normal='кнопки2.png',
            background_down='кнопки.png',
            option_cls=CustomSpinnerOption
        )
        self.spinner_upper.bind(text=self.on_spinner_upper_select)

        # Размещаем spinner в верхней части левого бокс-лейаута
        self.upper_layout = AnchorLayout(anchor_x='center', anchor_y='center')
        self.upper_layout.add_widget(self.spinner_upper)

        # Размещаем bottom_container в нижней части левого бокс-лейаута
        self.left_layout.add_widget(self.upper_layout)
        self.left_layout.add_widget(self.bottom_container)




        # Второй вертикальный бокс-лейаут (правая половина экрана)
        self.right_layout = BoxLayout(orientation='vertical', height=self.main_layout.height,
                                 width=self.main_layout.width * 0.5)

        # Второй вертикальный бокс-лейаут (правая половина экрана)
        self.right_keypoints_layout = BoxLayout(orientation='vertical', height=self.main_layout.height,
                                width=self.main_layout.width * 0.5, spacing=10)

        self.keypoints_box = BoxLayout(orientation='vertical')
        self.bottom_box = BoxLayout(orientation='vertical', spacing=5)

        self.keypoints_label = Label(text='Extract Keypoints',
                                     color=get_color_from_hex('#2F7C12')
                                     )
        # Создаем выпадающий список для верхней части левого бокс-лейаута
        options = ["mp-bad",
                   "mp-good",
                   "mp-best"
                   ]
        self.keypoints_spinner = Spinner(
            text='mp-best',
            values=options,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            pos_hint={'center_x': 0.5, 'center_y': 0.5, 'top': 1},
            background_normal='кнопки2.png',
            background_down='кнопки.png',
            option_cls=CustomSpinnerOption
        )
        self.keypoints_spinner.bind(text=self.on_keypoints_spinner_select)
        self.keypoints_box.add_widget(self.keypoints_label)
        self.keypoints_box.add_widget(self.keypoints_spinner)

        # Создаем выпадающий список для верхней части левого бокс-лейаута
        # options = ['JPG', 'JPEG', 'PNG']
        # self.image_spinner = Spinner(
        #     text='JPG',
        #     values=options,
        #     size_hint_y=None,
        #     size_hint_x=None,
        #     height=self.bottom_container.height * 0.1,
        #     width=self.bottom_container.width * 0.5,
        #     pos_hint={'center_x': 0.5, 'center_y': 0.5}
        # )
        # self.image_spinner.bind(text=self.on_image_spinner_select)
        # self.bottom_box.add_widget(self.image_spinner)

        # создаем текстовое поле для ввода пути до easymocap1
        self.path_easymocap_input_1 = TextInput(hint_text='Введите путь до easymocap',
                                                height=self.bottom_container.height * 0.1,
                                                width=self.bottom_container.width * 0.7,
                                                size_hint_y=None,
                                                size_hint_x=None,
                                                font_size=self.bottom_container.height * 0.1 * 0.5,
                                                pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                                )
        # создаем текстовое поле для ввода пути до chosen mode1
        self.path_model_input_1 = TextInput(hint_text='Введите путь до модели',
                                            height=self.bottom_container.height * 0.1,
                                            width=self.bottom_container.width * 0.7,
                                            size_hint_y=None,
                                            size_hint_x=None,
                                            font_size=self.bottom_container.height * 0.1 * 0.5,
                                            pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                            )

        self.bottom_box.add_widget(self.path_easymocap_input_1)
        self.bottom_box.add_widget(self.path_model_input_1)

        self.check_layout = BoxLayout(orientation='vertical',
                                      height=self.right_layout.height * 0.2,
                                      width=self.right_layout.width * 0.4,
                                      spacing=self.right_layout.height * 0.025
                                      )
        # Создаем чекбоксы
        checkbox_options = ['Hand', 'Face', 'Force']
        # Создаем переключатели (ToggleButton)
        self.toggle_buttons = [
            ToggleButton(
                text=option,
                size_hint_y=None,
                size_hint_x=None,
                height=self.check_layout.height * 0.25,
                width=self.check_layout.width * 0.25,
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                background_normal='кнопки2.png',
                background_down='кнопки.png'
            )
            for option in checkbox_options
        ]

        # Добавляем переключатели в bottom_box
        for toggle_button in self.toggle_buttons:
            self.check_layout.add_widget(toggle_button)
            toggle_button.bind(on_press=self.on_toggle_button_press)

        self.bottom_box.add_widget(self.check_layout)


        self.right_keypoints_layout.add_widget(self.keypoints_box)
        self.right_keypoints_layout.add_widget(self.bottom_box)

        self.show_script_button1 = Button(
            text="Show script",
            size_hint_y=None,
            size_hint_x=None,
            height=self.check_layout.height * 0.25,
            width=self.check_layout.width * 0.8,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_normal='кнопки2.png',
            background_down='кнопки.png'
        )
        self.show_script_button1.bind(on_press=self.on_show_script_button1_press)
        # создаем текстовое поле для корректировки финального скрипта
        self.script_input1 = TextInput(hint_text='Конечный script',
                                       height=self.right_layout.height * 0.1,
                                       width=self.right_layout.width * 0.95,
                                       size_hint_y=None,
                                       size_hint_x=None,
                                       pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                       )
        self.right_keypoints_layout.add_widget(self.show_script_button1)
        self.right_keypoints_layout.add_widget(self.script_input1)


        # Второй вертикальный бокс-лейаут (правая половина экрана)
        self.right_mocap_layout = BoxLayout(orientation='vertical',
                                            height=self.main_layout.height,
                                            width=self.main_layout.width * 0.5
                                            )

        self.mocap_box = BoxLayout(orientation='vertical',
                                   height=self.right_mocap_layout.height * 0.5,
                                   width=self.right_mocap_layout.width,
                                   pos_hint={'top': 1}
                                   )


        self.mocap_label = Label(text='mocap screen',
                                 color=get_color_from_hex('#2F7C12')
                                 # pos_hint={'center_x': 0.5, 'center_y': 0.5, 'top': 1}
                                 )
        # Создаем выпадающий список для верхней части левого бокс-лейаута
        options = ["0.25",
                   "0.5",
                   "0.75",
                   "1.0",
                   "1.25",
                   "1.5",
                   "2.0"
                   ]
        self.mocap_spinner = Spinner(
            text='Выбрать ускорние',
            values=options,
            size_hint_y=None,
            size_hint_x=None,
            height=self.bottom_container.height * 0.1,
            width=self.bottom_container.width * 0.5,
            pos_hint={'center_x': 0.5, 'center_y': 0.5, 'top': 1},
            background_normal='кнопки2.png',
            background_down='кнопки.png',
            option_cls=CustomSpinnerOption
        )
        self.mocap_spinner.bind(text=self.on_mocap_spinner_select)

        self.mocap_box.add_widget(self.mocap_label)

        self.path_easymocap_input_2 = TextInput(hint_text='Введите путь до easymocap',
                                                height=self.bottom_container.height * 0.1,
                                                width=self.bottom_container.width * 0.7,
                                                size_hint_y=None,
                                                size_hint_x=None,
                                                font_size=self.bottom_container.height * 0.1 * 0.5,
                                                pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                                )
        # создаем текстовое поле для ввода пути до chosen mode1
        self.path_model_input_2 = TextInput(hint_text='Введите путь до модели',
                                            height=self.bottom_container.height * 0.1,
                                            width=self.bottom_container.width * 0.7,
                                            size_hint_y=None,
                                            size_hint_x=None,
                                            font_size=self.bottom_container.height * 0.1 * 0.5,
                                            pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                            )

        self.mocap_box.add_widget(self.mocap_spinner)

        self.mocap_box.add_widget(self.path_easymocap_input_2)
        self.mocap_box.add_widget(self.path_model_input_2)

        self.right_mocap_layout.add_widget(self.mocap_box)

        self.mocap_bottom_box = BoxLayout(orientation='vertical',
                                   height=self.right_mocap_layout.height * 0.5,
                                   width=self.right_mocap_layout.width,
                                   pos_hint={'top': 1}
                                   )

        self.show_script_button2 = Button(
            text="Show script",
            size_hint_y=None,
            size_hint_x=None,
            height=self.check_layout.height * 0.25,
            width=self.check_layout.width * 0.8,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_normal='кнопки2.png',
            background_down='кнопки.png'
        )
        self.show_script_button2.bind(on_press=self.on_show_script_button2_press)
        # создаем текстовое поле для корректировки финального скрипта
        self.script_input2 = TextInput(hint_text='Конечный script',
                                       height=self.right_layout.height * 0.1,
                                       width=self.right_layout.width * 0.95,
                                       size_hint_y=None,
                                       size_hint_x=None,
                                       pos_hint={'center_x': 0.5, 'center_y': 0.5}
                                       )

        self.mocap_bottom_box.add_widget(self.show_script_button2)
        self.mocap_bottom_box.add_widget(self.script_input2)
        self.right_mocap_layout.add_widget(self.mocap_bottom_box)



        # Добавляем левый и правый бокс-лейауты в основной контейнер
        self.main_layout.add_widget(self.left_layout)
        self.main_layout.add_widget(self.right_layout)

        # Добавляем обработчик изменения размеров окна
        Window.bind(on_resize=self.on_window_resize)

        # Устанавливаем фоновое изображение
        with self.main_layout.canvas.before:
            self.bgbg = Rectangle(source='фон.png', pos=self.main_layout.pos,
                                  size=self.main_layout.size)

            # Замените 'новый_значок.ico' на путь к вашему новому значку
        self.set_window_icon('значок.png')


        return self.main_layout

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
        self.main_layout.size = (width, height)

        self.bgbg.size = self.main_layout.size

        # Обновляем размеры левого бокс-лейаута
        self.left_layout.size = (self.main_layout.width * 0.5, self.main_layout.height)

        # Обновляем размеры правого бокс-лейаута
        self.right_layout.size = (width * 0.5, height)

        # Обновляем размеры выпадающего списка в режиме "extract_keypoints"
        self.keypoints_spinner.width = self.bottom_container.width * 0.5
        self.keypoints_spinner.height = self.bottom_container.height * 0.1
        self.keypoints_spinner.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры ScrollView для выбранных файлов
        self.selected_files_scrollview.size = (self.label_and_scrollview_layout.width,
                                               self.label_and_scrollview_layout.height * 0.5)

        # Обновляем размеры лейбла "Выбранные файлы"
        self.label.width = self.bottom_container.width * 0.5
        self.label.height = self.bottom_container.height * 0.1

        # Устанавливаем параметр text_size для лейбла "Выбранные файлы"
        self.label.font_size = self.bottom_container.height * 0.1 * 0.5
        self.bg_rect.size = self.label.size

        # Обновляем размеры кнопки SUBMIT
        self.button_transfer_test.width = self.bottom_container.width * 0.5
        self.button_transfer_test.height = self.bottom_container.height * 0.1
        self.button_transfer_test.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры выпадающего списка в верхней части левого бокс-лейаута
        self.mode_layout.width = self.bottom_container.width * 0.5
        self.mode_layout.height = self.bottom_container.height * 0.1
        self.mode_layout.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры выпадающего списка
        self.build_spinner.width = self.bottom_container.width * 0.5
        self.build_spinner.height = self.bottom_container.height * 0.1
        self.build_spinner.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры кнопки "Выбрать файлы"
        self.selected_files_button.width = self.bottom_container.width * 0.5
        self.selected_files_button.height = self.bottom_container.height * 0.1
        self.selected_files_button.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры выпадающего списка в режиме "mocap"
        self.mocap_spinner.width = self.bottom_container.width * 0.5
        self.mocap_spinner.height = self.bottom_container.height * 0.1
        self.mocap_spinner.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры кнопки "Show script" (1)
        self.show_script_button1.width = self.check_layout.width * 0.3
        self.show_script_button1.height = self.check_layout.height * 0.15
        self.show_script_button1.font_size = self.check_layout.height * 0.25 * 0.25

        # Обновляем размеры текстового поля для скрипта (1)
        self.script_input1.width = self.right_layout.width * 0.95
        self.script_input1.height = self.right_layout.height * 0.1

        # Обновляем размеры кнопки "Show script" (2)
        self.show_script_button2.width = self.check_layout.width * 0.3
        self.show_script_button2.height = self.check_layout.height * 0.15
        self.show_script_button2.font_size = self.check_layout.height * 0.25 * 0.25

        # Обновляем размеры текстового поля для скрипта (2)
        self.script_input2.width = self.right_layout.width * 0.95
        self.script_input2.height = self.right_layout.height * 0.1

        self.bottom_container.width = self.left_layout.width
        self.bottom_container.height = self.left_layout.height * 0.5


        # Обновляем размеры контейнера для лейбла и ScrollView
        self.label_and_scrollview_layout.size = (self.bottom_container.width * 0.5, self.bottom_container.height * 0.5)


        # Обновляем размеры GridLayout внутри ScrollView
        self.selected_files_layout.width = self.selected_files_scrollview.width

        # Обновляем размеры элементов для правой части интерфейса
        self.right_keypoints_layout.size = (self.main_layout.width * 0.5, self.main_layout.height)

        # Обновляем размеры выпадающего списка "Выберите опцию"
        self.spinner_upper.width = self.bottom_container.width * 0.5
        self.spinner_upper.height = self.bottom_container.height * 0.1
        self.spinner_upper.font_size = self.bottom_container.height * 0.1 * 0.5


        # Обновляем размеры выпадающего списка "Extract Keypoints"
        self.keypoints_box.width = self.bottom_container.width * 0.5
        self.keypoints_box.height = self.bottom_container.height * 0.2

        # Обновляем размеры контейнера для выпадающего списка
        self.upper_layout.size = (self.bottom_container.width * 0.5, self.bottom_container.height * 0.1)

        # Обновляем размеры контейнера для чекбоксов
        self.check_layout.width = self.right_layout.width * 0.4
        self.check_layout.height = self.right_layout.height * 0.2

        # Обновляем размеры лейбла "Extract Keypoints"
        self.keypoints_label.width = self.bottom_container.width * 0.5
        self.keypoints_label.height = self.bottom_container.height * 0.1
        self.keypoints_label.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры текстового поля для пути до easymocap1
        self.path_easymocap_input_1.width = self.bottom_container.height * 0.9
        self.path_easymocap_input_1.height = self.bottom_container.height * 0.1
        self.path_easymocap_input_1.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры текстового поля для пути до модели1
        self.path_model_input_1.width = self.bottom_container.height * 0.9
        self.path_model_input_1.height = self.bottom_container.height * 0.1
        self.path_model_input_1.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры элементов для правой части интерфейса - Mocap
        self.right_mocap_layout.size = (self.main_layout.width * 0.5, self.main_layout.height)

        # Обновляем размеры выпадающего списка "mocap screen"
        self.mocap_box.width = self.right_mocap_layout.height * 0.5
        self.mocap_box.height = self.right_mocap_layout.width

        # Обновляем размеры выпадающего списка "mocap screen"
        self.mocap_bottom_box.width = self.right_mocap_layout.height * 0.5
        self.mocap_bottom_box.height = self.right_mocap_layout.width

        # Обновляем размеры лейбла "mocap screen"
        self.mocap_label.width = self.bottom_container.width * 0.5
        self.mocap_label.height = self.bottom_container.height * 0.1
        self.mocap_label.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры текстового поля для пути до easymocap2
        self.path_easymocap_input_2.width = self.bottom_container.height * 0.9
        self.path_easymocap_input_2.height = self.bottom_container.height * 0.1
        self.path_easymocap_input_2.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры текстового поля для пути до модели2
        self.path_model_input_2.width = self.bottom_container.height * 0.9
        self.path_model_input_2.height = self.bottom_container.height * 0.1
        self.path_model_input_2.font_size = self.bottom_container.height * 0.1 * 0.5

        # Обновляем размеры контейнера bottom_box
        self.bottom_box.width = self.right_layout.width
        self.bottom_box.height = self.right_layout.height * 0.3

        # Обновляем размеры чекбоксов
        for toggle_button in self.toggle_buttons:
            toggle_button.width = self.check_layout.width * 0.25
            toggle_button.height = self.check_layout.height * 0.25
            toggle_button.font_size = self.check_layout.height * 0.25 * 0.4




    def on_show_script_button1_press(self, instance):
        self.script_input1.text = self.get_script()

    def on_show_script_button2_press(self, instance):
        self.script_input2.text = self.get_script()

    def get_script(self):
        script_line = ""

        if self.chosen_model_builder_mode == "extract_keypoints":
            script_line += "python apps/preprocess/extract_keypoints.py 0_input/vky"
            script_line += " --mode "
            if self.chosen_keypoints_model == "mp-best":
                script_line += "mp-best"
            elif self.chosen_keypoints_model == "mp-good":
                script_line += "mp-good"
            elif self.chosen_keypoints_model == "mp-bad":
                script_line += "mp-bad"

            # оставили только три наших способа запуска (их же добавить в визуал)

            if 'Hand' in self.chosen_parts:
                script_line += " --hand"
            if 'Face' in self.chosen_parts:
                script_line += " --face"
            if 'Force' in self.chosen_parts:
                script_line += " --force"

        if self.chosen_model_builder_mode == "mocap":
            if self.chosen_fps == "0.25":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 8"
            elif self.chosen_fps == "0.5":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 15"
            elif self.chosen_fps == "0.75":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 23"
            elif self.chosen_fps == "1.0":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 30"
            elif self.chosen_fps == "1.25":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 38"
            elif self.chosen_fps == "1.5":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 45"
            elif self.chosen_fps == "2.0":
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 60"
            else:
                script_line += "python apps/demo/mocap.py 0_input/vky --work internet --fps 30"

        print(script_line)

        return script_line

    def send_and_wait_until_done(self):

        # video_path1 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T1.mp4'
        # video_path2 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T2.mp4'
        # video_path3 = r'C:\\Users\\msmkl\\PycharmProjects\\Motion-Capture\\UI\\videos\\T3.mp4'

        dict = {}
        dict["extract_keypoints"] = self.script_input1.text
        dict["mocap"] = self.script_input2.text

        print(dict)

        DATA = {
            'names': self.selected_files,
            # 'names': ['C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_1.mp4', 'C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_T1.mp4'],
            'internet_mode': self.chosen_internet_mode,
            'meta': {
                'face_hunting': 'YES' if self.chosen_face_hunting == 'Include' else "NO",
                'script_line': dict
            }
        }

        print('SELECTED FILES:', self.selected_files)

        # video_path = r'C:\Users\msmkl\PycharmProjects\Motion-Capture\UI\videos\TEST_VIDEO.mp4'
        # instructions = {'action': 'process_video', 'parameters': {'threshold': 0.5}}
        server_host = '213.171.10.222'  # Замените на IP-адрес вашего сервера
        server_port = 12345  # Замените на порт вашего сервера

        # client_worker = Client_Worker()
        # client_worker.submit(DATA, server_host, server_port)
        json_file_path = "DATA.json"

        # Сохранение словаря в JSON
        with open(json_file_path, 'w') as json_file:
            json.dump(DATA, json_file)

        if DATA['internet_mode'] == 'online':
            subprocess.run(['python', 'transfer.py'], check=True)

        elif DATA['internet_mode'] == 'offline':
            # exctract keypoints command
            script_exctract_keypoints = self.script_input1.text

            if script_exctract_keypoints != '':
                path_to_easymocap_exctract_keypoints = self.path_easymocap_input_1.text
                path_to_model_exctract_keypoints = self.path_model_input_1.text

                command_exctract_keypoints = f'python {path_to_easymocap_exctract_keypoints}/{script_exctract_keypoints}'
                subprocess.run(command_exctract_keypoints)

            # mocap command
            script_mocap = self.script_input2.text

            if script_mocap != '':
                path_to_easymocap_mocap = self.path_easymocap_input_2.text
                path_to_model_mocap = self.path_model_input_2.text

                command_mocap = f'python {path_to_easymocap_mocap}/{script_exctract_keypoints}'
                subprocess.run(command_mocap)

        else:
            print('Choose mode (online / offline)')
            return

        # process = Process(target=client_worker.submit, args=(DATA, '213.171.10.222', 12345))
        # process.start()
        # process.join()
        time.sleep(3)

        self.button_transfer_test.disabled = False

    def update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    def test_transfer(self, instance):
        self.button_transfer_test.disabled = True
        thread = threading.Thread(target=self.send_and_wait_until_done)
        thread.daemon = True
        thread.start()

    def on_mode_layout_select(self, spinner, text):
        # Обновляем значение переменной chosen_mode при выборе опции в спинере
        self.chosen_internet_mode = text
        print(f"Выбран интернет-режим: {self.chosen_internet_mode}")

    def on_build_spinner_select(self, spinner, text):
        self.chosen_face_hunting = text
        print(f"Выбран режим сборки: {self.chosen_face_hunting}")

    def on_spinner_upper_select(self, spinner, text):
        self.chosen_model_builder_mode = text
        print(f"Выбран режим сборки модели: {self.chosen_model_builder_mode}")

        if text == 'extract_keypoints':
            self.main_layout.children[0].clear_widgets()  # Очищаем виджеты второго лейаута
            self.main_layout.children[0].add_widget(self.right_keypoints_layout)  # Добавляем keypoints_layout
        elif text == 'mocap':
            self.main_layout.children[0].clear_widgets()  # Очищаем виджеты второго лейаута
            self.main_layout.children[0].add_widget(self.right_mocap_layout)  # Добавляем mocap_layout

    def on_mocap_spinner_select(self, spinner, text):
        self.chosen_fps = text
        print(f"Выбрано ускорение для Internet: {self.chosen_fps}")

    def on_keypoints_spinner_select(self, spinner, text):
        self.chosen_keypoints_model = text
        print(f"Выбрана модель для keypoints: {self.chosen_keypoints_model}")

    def on_toggle_button_press(self, toggle_button):
        part_name = toggle_button.text
        if toggle_button.state == 'down':
            # Если кнопка выбрана, добавляем часть в список
            if part_name not in self.chosen_parts:
                self.chosen_parts.append(part_name)
        else:
            # Если кнопка отменена, удаляем часть из списка
            if part_name in self.chosen_parts:
                self.chosen_parts.remove(part_name)

        # Выводим текущий список в консоль (можете заменить на свою логику)
        print("Chosen Parts:", self.chosen_parts)

    def doo3(self, instance):
        th3 = threading.Thread(target=self.open_file_dialog,
                               args=([r'CLIENT_storage']))
        th3.daemon = True
        th3.start()

    def open_file_dialog(self, args):
        app = QApplication(sys.argv)
        dialog = QFileDialog()
        initial_directory = args[0]
        dialog.setDirectory(initial_directory)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        if dialog.exec_():
            self.selected_files = dialog.selectedFiles()

            Clock.schedule_once(lambda dt: self.update_selected_files_layout())

    def update_selected_files_layout(self):
        # Очищаем текущее содержимое
        self.selected_files_layout.clear_widgets()

        # Добавляем каждый файл в GridLayout
        for file_path in self.selected_files:
            file_label = Label(
                text=file_path,
                color=get_color_from_hex('#2F7C12'),
                size_hint_y=None,
                height=self.bottom_container.height * 0.1,
                width=self.selected_files_scrollview.width,
                text_size=(self.selected_files_scrollview.width, None),
                halign='left',
                valign='middle',
                shorten=True,  # Обрезаем текст, если он не помещается
                markup=True  # Позволяет использовать разметку для управления переносами строк
            )
            self.selected_files_layout.add_widget(file_label)


if __name__ == '__main__':
    MocapScreenApp().run()
