import redis
import json
import time
import threading

# Connect to the Redis server
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Function to store data in Redis
def store_data_in_redis(data):
    redis_client.rpush('data_queue', json.dumps(data))
    print("Data added to Redis queue")



# Function to process data from Redis
def process_data_from_redis():
        data = redis_client.lpop('data_queue')
        if data:
            # Deserialize the data
            deserialized_data = json.loads(data)
            # Here, send the data to your database
            print("Processing and sending data to the database:", deserialized_data)
        else:
            print("No data in the queue, waiting...")
        time.sleep(5) 



        
# Running both functions
if __name__ == "__main__":
    # Start the data processing function in a separate thread
    # processor_thread = threading.Thread(target=process_data_from_redis)
    # processor_thread.start()



    try:
        x = 0
        while x <= 7:
            sample_data = {'id': 1, 'value': 'example'}
            store_data_in_redis(sample_data)
            time.sleep(1)  # Wait for 5 seconds before adding more data
            x = x + 1


        process_data_from_redis()

    except KeyboardInterrupt:
        print("Stopped by user")
