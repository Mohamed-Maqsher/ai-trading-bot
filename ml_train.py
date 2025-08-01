import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import joblib

df = yf.download("AAPL", period="60d", interval="1h")
df["prev_close1"] = df["Close"].shift(1)
df["prev_close2"] = df["Close"].shift(2)
df["prev_close3"] = df["Close"].shift(3)
df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
df.dropna(inplace=True)

X = df[["prev_close1", "prev_close2", "prev_close3"]]
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = RandomForestClassifier()
model.fit(X_train, y_train)

accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model accuracy: {round(accuracy * 100, 2)}%")

joblib.dump(model, "ml_models/aapl_rf_model.pkl")
