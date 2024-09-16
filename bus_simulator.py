import json
import random
from datetime import datetime, timedelta


def load_route_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract route info from the first item
    route_info = {
        "RouteUID": data[0]["RouteUID"],
        "RouteID": data[0]["RouteID"],
        "RouteName": data[0]["RouteName"]
    }

    # Extract unique stops while preserving order
    stops = []
    seen_stop_uids = set()
    for item in data:
        if item["StopUID"] not in seen_stop_uids:
            stops.append({
                "StopUID": item["StopUID"],
                "StopID": item["StopID"],
                "StopName": item["StopName"]
            })
            seen_stop_uids.add(item["StopUID"])

    return route_info, stops


def simulate_bus_info(route_info, stops):
    current_time = datetime.now()

    bus_info = []
    cumulative_time = 0

    for stop in stops:
        estimate_time = random.randint(60, 300)  # 1 to 5 minutes between stops
        cumulative_time += estimate_time

        stop_info = {
            **stop,  # Include all stop information
            **route_info,  # Include route information
            "Direction": 1,
            "EstimateTime": cumulative_time,
            "StopStatus": random.choices([0, 1, 2, 3], weights=[0.85, 0.05, 0.05, 0.05])[0],
            "SrcUpdateTime": (current_time - timedelta(seconds=random.randint(0, 60))).strftime(
                "%Y-%m-%dT%H:%M:%S+08:00"),
            "UpdateTime": current_time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        }

        bus_info.append(stop_info)

    return bus_info


# Example usage
if __name__ == "__main__":
    file_path = 'TDX API Response.json'  # Update this to the actual path of your JSON file
    route_info, stops = load_route_data(file_path)
    simulated_data = simulate_bus_info(route_info, stops)

    for stop in simulated_data:
        print(f"Stop: {stop['StopName']['En']}, Estimated Time: {stop['EstimateTime']} seconds")