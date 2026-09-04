import yaml
import os


BASE_PATH = "semantic_layer"


def load_yaml(filename):

    path = os.path.join(
        BASE_PATH,
        filename
    )

    with open(path,"r") as file:

        return yaml.safe_load(file)



def load_views():

    return load_yaml(
        "views.yaml"
    )


def load_metrics():

    return load_yaml(
        "metrics.yaml"
    )


def load_intents():

    return load_yaml(
        "intents.yaml"
    )