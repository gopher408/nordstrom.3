from communication import Communication

class Chat(Communication):
    def __init__(self):
        self.response = None
        pass

    def send(self, record):
        print(str(record['speaker']) + ' > ' + (str(record['message']) if 'message' in record and record['message'] else ''))
        self.response = record

    def get(self, to=None, date_sent=None):
        print('Chat.get')

    def get_response(self):
        return self.response;