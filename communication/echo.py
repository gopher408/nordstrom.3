from communication import Communication


class Echo(Communication):
    def __init__(self):
        pass

    def send(self, record):
        print(str(record['speaker']) + ' > ' + (str(record['message']) if 'message' in record and record['message'] else ''))
        return None

    def get(self, to=None, date_sent=None):
        print('Print.get')