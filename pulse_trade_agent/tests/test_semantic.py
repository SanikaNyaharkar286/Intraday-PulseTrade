from agent.semantic_loader import (
    load_views,
    load_metrics,
    load_intents
)



def test_semantic_files():

    views = load_views()

    metrics = load_metrics()

    intents = load_intents()


    print(
        views
    )

    print(
        metrics
    )

    print(
        intents
    )


test_semantic_files()