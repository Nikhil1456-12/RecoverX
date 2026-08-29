from app.ml.predict import predict_recovery_probability, predict_batch

class MLRecoveryModel:
    def __init__(self):
        pass

    def predict(self, context: dict) -> float:
        return predict_recovery_probability(context)

    def predict_batch(self, contexts: list[dict]) -> list[float]:
        return predict_batch(contexts)
        
def train_model():
    from app.ml.train import train
    train()
