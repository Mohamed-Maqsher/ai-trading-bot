import numpy as np
import yfinance as yf
import tensorflow as tf
import joblib

def predict_lstm():
    try:
        df = yf.download("AAPL", period="3d", interval="1h")[['Close']]
        scaler = joblib.load('ml_models/aapl_lstm_scaler.pkl')
        model = tf.keras.models.load_model('ml_models/aapl_lstm_model.h5')
        last_50 = df[-50:].values.reshape(-1, 1)
        scaled = scaler.transform(last_50)
        X = np.reshape(scaled, (1, 50, 1))
        prediction = model.predict(X)[0][0]
        return prediction
    except:
        return 0.5
