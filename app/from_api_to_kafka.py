from kafka import KafkaProducer
import json
import requests


def get_random_user_data(num_users=1):
    url = f"https://randomuser.me/api/?results={num_users}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['results']
    else:
        raise Exception(f"Failed to get data: {response.status_code}")


def json_serializer(data):
    return json.dumps(data).encode('utf-8')


if __name__ == "__main__":
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=json_serializer
    )

    users_data = get_random_user_data(10)

    for user_data in users_data:
        user_info = {
            "full_name": f"{user_data['name']['first']} {user_data['name']['last']}",
            "gender": user_data['gender'],
            "country": user_data['location']['country'],
            "city": user_data['location']['city'],
            "address": f"{user_data['location']['street']['number']}, {user_data['location']['street']['name']}",
            "email": user_data['email']
        }

        producer.send('users', user_info)
        print(f"Sent user: {user_info['full_name']}")

    producer.flush()
    producer.close()
