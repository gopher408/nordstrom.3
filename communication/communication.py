from abc import ABCMeta, abstractmethod

class Communication:
    def __init__(self):
        pass

    @abstractmethod
    def send(self, record):
        print(str(record['speaker']) + ' > ' + (str(record['message']) if 'message' in record and record['message'] else ''))
        return None

    @abstractmethod
    def get(self, to=None, date_sent=None):
        print('dddd')
        return None