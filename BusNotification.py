import time
from bus_simulator import load_route_data, simulate_bus_info


class BusNotificationSystem:
    def __init__(self):
        self.routes = {}
        self.user_subscriptions = {}

    def add_route(self, route_name, file_path):
        route_info, stops = load_route_data(file_path)
        self.routes[route_name] = {
            'route_info': route_info,
            'stops': stops
        }

    def subscribe_user(self, user_id, route_name, target_stop):
        if route_name not in self.routes:
            raise ValueError(f"Route {route_name} not found")

        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = []

        self.user_subscriptions[user_id].append({
            'route_name': route_name,
            'target_stop': target_stop
        })

    def check_and_notify(self):
        for route_name, route_data in self.routes.items():
            bus_info = simulate_bus_info(route_data['route_info'], route_data['stops'])

            for user_id, subscriptions in self.user_subscriptions.items():
                for subscription in subscriptions:
                    if subscription['route_name'] == route_name:
                        self._check_bus_position(user_id, bus_info, subscription['target_stop'])

    def _check_bus_position(self, user_id, bus_info, target_stop):
        target_index = next((i for i, stop in enumerate(bus_info) if stop['StopName']['Zh_tw'] == target_stop), None)
        if target_index is None:
            return

        for i in range(max(0, target_index - 5), target_index - 2):
            if bus_info[i]['StopStatus'] == 0:  # Bus is approaching this stop
                stops_away = target_index - i
                self._send_notification(user_id, target_stop, stops_away)
                break

    def _send_notification(self, user_id, target_stop, stops_away):
        print(f"Notification for User {user_id}: The bus is {stops_away} stops away from {target_stop}")


# Example usage
if __name__ == "__main__":
    notification_system = BusNotificationSystem()

    # Add routes
    notification_system.add_route("672", "TDX API Response.json")
    # Add more routes as needed

    # Subscribe users
    notification_system.subscribe_user("user1", "672", "博仁醫院")
    notification_system.subscribe_user("user2", "672", "捷運景平站")
    # Add more subscriptions as needed

    # Simulate checking for buses every 60 seconds
    try:
        while True:
            notification_system.check_and_notify()
            time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping the notification system...")