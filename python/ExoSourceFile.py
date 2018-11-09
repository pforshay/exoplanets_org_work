from ExoPlanet import ExoParameter, ExoPlanet
import os
import simplejson as json
import datetime


class ExoSourceFile(object):

    dir = "../pln_sources/"

    def __init__(self, data=None, planet=None, ref=None, url=None):

        self.parameters = {}
        self.planet = planet
        self.ref = ref
        self.url = url

        if data:
            self.read_from_pln(data)

    def as_dict(self):

        now = datetime.datetime.now()
        loc = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        d = {}
        d["PLANET"] = self.planet
        d["REFERENCE"] = self.ref
        d["ADS_LINK"] = self.url
        d["LAST_UPDATE"] = now.strftime("%Y-%m-%d %H:%M {0}".format(loc))
        d["DATA"] = self.parameters

        return d

    def read_from_dict(self, data_dict):
        pass

    def read_from_json(self, json_file):

        with open(json_file) as text:
            json_load = json.loads(text)

    def read_from_pln(self, pln_file):

        self.planet_obj = ExoPlanet(path=pln_file)
        for attr in self.planet_obj.attributes:
            exo_param = getattr(self.planet_obj, attr)
            if not exo_param.is_default():
                self.parameters[exo_param.parameter] = exo_param.values_dict()

    def write_source_file(self):

        path = "".join([self.dir, self.planet, "/"])
        filename = "_".join([self.planet, self.ref.replace(" ", "_")])
        filename = "".join([path, filename, ".source"])

        if not os.path.exists(path):
            os.makedirs(path)

        with open(filename, 'w') as json_file:
            json_file.write(json.dumps(self.as_dict(),
                                       # sort_keys=True,
                                       indent=4 * ' '
                                       ))


def __test__():
    t = ExoSourceFile('myp', 'Peter 2018', 'http.com')
    t.read_from_pln("../finished_pln/24 Boo b.pln")
    t.write_source_file()


if __name__ == "__main__":
    __test__()
