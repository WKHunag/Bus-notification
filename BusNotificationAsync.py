import json
import asyncio
from collections import defaultdict
from datetime import datetime
import aiohttp
import os
import time
from configs import client_id, client_key
from auth_TDX import AsyncTDXAuth


class AsyncBusNotificationSystem:
    def __init__(self, app_id, app_key):
        self.routes = {}
        self.session = None
        self.cache = {}
        self.cache_time = {}
        self.auth = AsyncTDXAuth(app_id, app_key)

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        await self.load_all_routes()

    async def close(self):
        if self.session:
            await self.session.close()

    async def load_all_routes(self):
        all_routes_url = 'https://tdx.transportdata.tw/api/basic/v2/Bus/Route/City/Taipei?$format=JSON'
        access_token = await self.auth.get_access_token()
        headers = {
            'authorization': f'Bearer {access_token}',
            'Accept-Encoding': 'gzip'
        }
        async with self.session.get(all_routes_url, headers=headers) as response:
            if response.status == 200:
                routes_data = await response.json()
                for route in routes_data:
                    route_name = route['RouteName']['Zh_tw']
                    self.routes[route_name] = {
                        'RouteUID': route['RouteUID'],
                        'RouteID': route['RouteID'],
                        'DepartureStopNameZh': route.get('DepartureStopNameZh', ''),
                        'DestinationStopNameZh': route.get('DestinationStopNameZh', ''),
                        'SubRoutes': {
                            (sub_route['SubRouteName']['Zh_tw'], sub_route['Direction']): sub_route
                            for sub_route in route['SubRoutes']
                        }
                    }
                print(f"Loaded {len(self.routes)} routes with their sub-routes.")
            else:
                error_text = await response.text()
                print(f"Error loading routes: {response.status}, {error_text}")

    def save_user_preferences(self, user_id, preferences):
        file_name = f"{user_id}_preferences.json"
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(preferences, file, ensure_ascii=False, indent=2)

    def load_user_preferences(self, user_id):
        file_name = f"{user_id}_preferences.json"
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        return []

    def subscribe_user(self, user_id, route_name, sub_route_name, direction, target_stop):
        if route_name not in self.routes:
            raise ValueError(f"Route {route_name} not found")

        key = (sub_route_name, direction)
        if key not in self.routes[route_name]['SubRoutes']:
            raise ValueError(f"Sub-route {sub_route_name} with direction {direction} not found in route {route_name}")

        preferences = self.load_user_preferences(user_id)
        preferences.append({
            'route_name': route_name,
            'sub_route_name': sub_route_name,
            'direction': direction,
            'target_stop': target_stop
        })
        self.save_user_preferences(user_id, preferences)

    async def get_bus_info(self, route_name, sub_route_name, direction):
        cache_key = f"{route_name}_{sub_route_name}_{direction}"
        current_time = datetime.now()

        if cache_key in self.cache and (current_time - self.cache_time[cache_key]).total_seconds() < 60:
            return self.cache[cache_key]

        access_token = await self.auth.get_access_token()
        headers = {
            'authorization': f'Bearer {access_token}',
            'Accept-Encoding': 'gzip'
        }

        url = f'https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/' \
              f'Taipei/{sub_route_name}?$format=JSON&$filter=Direction eq {direction}'

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                data = [item for item in data if item['RouteName']['Zh_tw'] == sub_route_name]
                self.cache[cache_key] = data
                self.cache_time[cache_key] = current_time
                return data
            else:
                error_text = await response.text()
                print(
                    f"Error fetching data for route {route_name}, sub-route {sub_route_name}, direction {direction}: {response.status}, {error_text}")
                return None

    async def check_routes(self):
        all_preferences = self.get_all_preferences()
        unique_routes = set(
            (pref['route_name'], pref['sub_route_name'], pref['direction'])
            for prefs in all_preferences.values() for pref in prefs
        )

        for route_name, sub_route_name, direction in unique_routes:
            bus_info = await self.get_bus_info(route_name, sub_route_name, direction)
            if bus_info:
                relevant_users = [
                    user_id for user_id, prefs in all_preferences.items()
                    if any(
                        p['route_name'] == route_name and
                        p['sub_route_name'] == sub_route_name and
                        p['direction'] == direction
                        for p in prefs
                    )
                ]
                for user_id in relevant_users:
                    await self.check_user_route(user_id, route_name, sub_route_name, direction, bus_info)

    async def check_user_route(self, user_id, route_name, sub_route_name, direction, bus_info):
        preferences = self.load_user_preferences(user_id)
        for preference in preferences:
            if (preference['route_name'] == route_name and
                    preference['sub_route_name'] == sub_route_name and
                    preference['direction'] == direction):
                await self._check_bus_position(
                    user_id,
                    bus_info,
                    preference['target_stop'],
                    route_name,
                    sub_route_name,
                    direction
                )

    async def _check_bus_position(self, user_id, bus_info, target_stop, route_name, sub_route_name, direction):
        target_stop_info = next((stop for stop in bus_info if stop['StopName']['Zh_tw'] == target_stop), None)
        if target_stop_info is None:
            return

        estimate_time = target_stop_info.get('EstimateTime')
        if estimate_time is not None:
            minutes = estimate_time // 60  # Convert seconds to minutes
            if 3 <= minutes <= 10:
                await self._send_notification(user_id, target_stop, minutes, route_name, sub_route_name, direction)

    async def _send_notification(self, user_id, target_stop, minutes, route_name, sub_route_name, direction):
        terminal_stop = self.routes[route_name]['DepartureStopNameZh'] if direction == 1 \
            else self.routes[route_name]['DestinationStopNameZh']
        print(
            f"Notification for User {user_id}: "
            f"The bus on route {sub_route_name}(to {terminal_stop}) will arrive at {target_stop} in {minutes} minutes."
        )
        # Implement actual notification logic here

    def get_all_user_ids(self):
        return [file.split('_')[0] for file in os.listdir('.') if file.endswith('_preferences.json')]

    def get_all_preferences(self):
        all_preferences = defaultdict(list)
        for user_id in self.get_all_user_ids():
            all_preferences[user_id] = self.load_user_preferences(user_id)
        return all_preferences

    def list_all_routes(self):
        for route_name, route_info in self.routes.items():
            print(
                f"Route: {route_name}, From: {route_info['DepartureStopNameZh']} To: {route_info['DestinationStopNameZh']}")
            for (sub_route_name, direction), sub_route_info in route_info['SubRoutes'].items():
                print(f"  Sub-route: {sub_route_name}, Direction: {direction}")


async def main():
    notification_system = AsyncBusNotificationSystem(client_id, client_key)
    await notification_system.initialize()

    # List all available routes and sub-routes
    # notification_system.list_all_routes()

    # Example of subscribing users to different routes with sub-routes and directions
    try:
        notification_system.subscribe_user("user1", "672", "672", 1, "博仁醫院")
        notification_system.subscribe_user("user2", "藍29", "藍29", 0, "福星公園")
    except ValueError as e:
        print(f"Subscription error: {e}")

    try:
        while True:
            await notification_system.check_routes()
            await asyncio.sleep(60)  # Check every 60 seconds
    except KeyboardInterrupt:
        print("Stopping the notification system...")
    finally:
        await notification_system.close()


if __name__ == "__main__":
    asyncio.run(main())
