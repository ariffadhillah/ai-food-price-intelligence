from app.ai.context_hash import generate_context_hash


def main():
    context_one = {
        "context_metadata": {
            "context_type": "national_food_price_analysis",
            "context_version": "1.0.0",
            "generated_at": "2026-07-21T10:00:00+00:00",
            "country": "Indonesia",
        },
        "market_statistics": {
            "high_risk_count": 5,
            "national_average_score": 18.4,
        },
    }

    context_two = {
        "context_metadata": {
            "context_type": "national_food_price_analysis",
            "context_version": "1.0.0",
            "generated_at": "2026-07-21T11:30:00+00:00",
            "country": "Indonesia",
        },
        "market_statistics": {
            "high_risk_count": 5,
            "national_average_score": 18.4,
        },
    }

    context_three = {
        "context_metadata": {
            "context_type": "national_food_price_analysis",
            "context_version": "1.0.0",
            "generated_at": "2026-07-21T11:30:00+00:00",
            "country": "Indonesia",
        },
        "market_statistics": {
            "high_risk_count": 6,
            "national_average_score": 18.4,
        },
    }

    hash_one = generate_context_hash(context_one)
    hash_two = generate_context_hash(context_two)
    hash_three = generate_context_hash(context_three)

    print(f"Hash one:   {hash_one}")
    print(f"Hash two:   {hash_two}")
    print(f"Hash three: {hash_three}")
    print()
    print(f"Context 1 == Context 2: {hash_one == hash_two}")
    print(f"Context 1 == Context 3: {hash_one == hash_three}")

    assert hash_one == hash_two
    assert hash_one != hash_three

    print()
    print("Context hash test berhasil.")


if __name__ == "__main__":
    main()