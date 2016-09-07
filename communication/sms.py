from communication.communication import Communication

class SMS(Communication):
    def __init__(self):
        pass

    def send(self, record):
        print(record)

    def get(self, to=None, date_sent=None):
        print('SMS.get')