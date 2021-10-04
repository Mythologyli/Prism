import json

from prism import Prism


if __name__ == '__main__':
    config = json.load(open('./prism_config.json', 'r', encoding='utf-8'))

    prism = Prism(config)
    prism.run()
