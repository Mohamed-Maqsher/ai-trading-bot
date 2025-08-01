import yfinance as yf
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
import joblib

df = yf.download("AAPL", period="60d", interval="1h")[['Close']]
scaler = MinMaxScaler()
scaled = scaler.fit_transform(df)

X, y = [], []
for i in range(50, len(scaled)):
    X.append(scaled[i-50:i, 0])
    y.append(1 if scaled[i, 0] > scaled[i-1, 0] else 0)

X, y = np.array(X), np.array(y)
X = X.reshape((X.shape[0], X.shape[1], 1))

model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(LSTM(50))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X, y, epochs=10, batch_size=32)

model.save('ml_models/aapl_lstm_model.h5')
joblib.dump(scaler, 'ml_models/aapl_lstm_scaler.pkl')
