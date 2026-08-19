from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "soleroa/movie-review-classifier"  #  nombre que le pusiste en HF Hub

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

def analizar_sentiment(texto: str):
    """
    Analiza el sentiment de un texto (review) y devuelve 'Positivo' o 'Negativo'.
    """
    inputs = tokenizer(texto, return_tensors="pt", truncation=True, padding=True, max_length=256)
    outputs = model(**inputs)
    prediction = outputs.logits.argmax(-1).item()
    return "Positivo" if prediction == 1 else "Negativo"


if __name__ == "__main__":
    ejemplo = "This movie was absolutely fantastic, one of Nolan's best works"
    print(analizar_sentiment(ejemplo))