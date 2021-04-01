import configparser

from jinja2 import Environment, FileSystemLoader


if __name__ in "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")
    templateLoader = FileSystemLoader(searchpath="./")
    env = Environment(loader=templateLoader)
    template = env.get_template("template.ovf")
    output = template.render(**config["default"])
    print({**config["default"]})

    with open("image.ovf", "w") as f:
        f.write(output)
