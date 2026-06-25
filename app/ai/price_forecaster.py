import pandas as pd
from sklearn.linear_model import LinearRegression
from app.database.db import engine


def forecast_price(commodity_name, province_name, periods=3):
    query = """
        SELECT price_date, commodity_name, province_name, price
        FROM commodity_prices
        WHERE commodity_name = %(commodity_name)s
        AND province_name = %(province_name)s
        ORDER BY price_date
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "commodity_name": commodity_name,
            "province_name": province_name,
        },
    )

    if len(df) < 3:
        return None

    df["price_date"] = pd.to_datetime(df["price_date"])
    df["month_index"] = range(len(df))

    X = df[["month_index"]]
    y = df["price"]

    model = LinearRegression()
    model.fit(X, y)

    future_rows = []

    last_date = df["price_date"].max()
    last_index = df["month_index"].max()

    for i in range(1, periods + 1):
        future_index = last_index + i
        future_date = last_date + pd.DateOffset(months=i)

        future_df = pd.DataFrame(
            {
                "month_index": [future_index]
            }
        )

        predicted_price = model.predict(future_df)[0]

        future_rows.append(
            {
                "forecast_date": future_date.date(),
                "commodity_name": commodity_name,
                "province_name": province_name,
                "predicted_price": round(predicted_price, 2),
            }
        )

    return pd.DataFrame(future_rows)


def main():
    result = forecast_price(
        commodity_name="Cabai Merah",
        province_name="Sulawesi Tenggara",
        periods=3,
    )

    if result is None:
        print("Not enough data for forecasting.")
    else:
        print(result)


if __name__ == "__main__":
    main()