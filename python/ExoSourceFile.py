import json


class ExoSourceFile(object):

    def __init__(planet, ref, url, data=None):

        self.parameters = []
        self.planet = planet
        self.ref = ref
        self.url = url

    def read_from_dict(data_dict):

    def read_from_json(json_file):

        with open(json_file) as text:
            json_load = json.loads(text)
