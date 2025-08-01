import joblib
import yfinance as yf
import pandas as pd

def predict_next_move():
    try:
        model = joblib.load("ml_models/aapl_rf_model.pkl")
        df = yf.download("AAPL", period="1d", interval="1h")
        if len(df) < 3:
            return None
        last = df.tail(3)["Close"].values
        X_new = pd.DataFrame([{
            "prev_close1": last[-3],
            "prev_close2": last[-2],
            "prev_close3": last[-1],
        }])
        return model.predict(X_new)[0]
    except:
        return None
