from client_worker import Client_Worker
import json

# instructions = {'action': 'process_video', 'parameters': {'threshold': 0.5}}
# DATA = {
#         'names': ['C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_1.mp4', 'C:/Users/msmkl/PycharmProjects/Motion-Capture/producktion/CLIENT_storage/CHANGED_T1.mp4'],
#         'internet_mode': 'online',
#         'meta': instructions
#     }


with open('DATA.json', 'r') as json_file:
    DATA = json.load(json_file)


with open('BIG_LOG.txt', 'a') as json_file:
    # Преобразование словаря в строку в формате JSON
    data_string = json.dumps(DATA)
    # Запись строки в конец файла
    json_file.write(data_string + '\n')

print('DATA from SUBPROCESS:', DATA)
try:
    w = Client_Worker()
    w.submit(DATA, '213.171.10.222', 12345)
    
except:
    pass