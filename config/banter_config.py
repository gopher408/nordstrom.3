import os

class BanterConfig:
    def __init__(self, partner, grammer_file):
        currentLocation = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(currentLocation, '..')
        self.partner = partner
        if partner:
            tmpPath = os.path.join(self.path, 'partner', partner)
            if os.path.isdir(tmpPath):
                self.path = os.path.join(self.path, 'partner', partner)

        self.grammer_file = grammer_file

    def get_partner(self):
        return self.partner

    def get_grammer_file(self, grammer_file):
        self.grammer_file = grammer_file

    def get_grammer_file(self):
        print 'BanterConfig.grammer_file:' + os.path.join(self.path, self.grammer_file)
        return os.path.join(self.path, self.grammer_file)

    def get_words_file(self, file_name):
        self.file_name = file_name

    def get_words_file(self):
        print 'BanterConfig.get_words_file:' + os.path.join(self.path, 'words.txt')
        return os.path.join(self.path, 'words.txt')
