import yaml


def read_pln(path):
    pln_dict = {}
    with open(path, 'r') as f:
        for line in f:
            line_split = [x.strip() for x in line.split(' ', 1)]
            if line_split[0].startswith('#'):
                if line_split[1].startswith('='):
                    continue
                else:
                    parent = line_split[1]
                    pln_dict[parent] = []
            else:
                keyword_value_pair = [x.strip()
                                      for x in line.split(' ', 1)
                                      ]
                num = len(keyword_value_pair)
                if num == 0:
                    continue
                keyword = keyword_value_pair[0]
                pln_dict[parent].append(keyword)
    # print(pln_dict)
    return pln_dict


def save_as_yaml(pln_dict):
    with open("pln_template.yaml", 'w') as yamlfile:
        yaml.dump(pln_dict, yamlfile, default_flow_style=False)


def load_from_yaml():
    with open("pln_template.yaml", 'r') as template:
        as_dict = yaml.load(template)
    print(as_dict)


if __name__ == "__main__":
    load_from_yaml()
