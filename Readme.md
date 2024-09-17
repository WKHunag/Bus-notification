# Bus Notification System

This is an asynchronous bus arrival notification system written in Python. It utilizes the asyncio and aiohttp libraries to fetch real-time bus data from the TDX (Transportation Data eXchange) platform for Taipei City buses. The system allows users to subscribe to specific bus routes, sub-routes, directions, and target stops, providing timely notifications when the bus is approaching.

## Features

- **Real-Time Bus Information**: Fetches real-time estimated time of arrival (ETA) data for Taipei City buses from the TDX API.
- **User** Subscriptions: Supports user subscriptions to specific bus routes, sub-routes, directions, and target stops.
- **Asynchronous** Processing: Utilizes asyncio and aiohttp for efficient handling of multiple network requests.
- **Notifications**: Sends notifications to users when the bus is 3 to 5 minutes away from the target stop (currently implemented as console output; can be extended to SMS, email, etc.).

## Prerequisites

- **Python 3.7+**
- **aiohttp** library
- **asyncio** library
- **requests** library (used for obtaining the access token)

## Obtaining TDX API Credentials
1. Register an account on the TDX platform:
    - Visit the TDX Platform and sign up for an account.
2. Apply for an Application:
    - In the developer dashboard, create a new application to obtain your Client ID and Client Secret.
3. Configure your credentials:
    - Create a configs.py file in the project directory with the following content:
    ```python
        client_id = 'your_client_id'
        client_key = 'your_client_secret'
    ```

### Usage
1. Run the main program:
    ```bash 
        python BusNotificationAsync.py
    ```
2. Subscribe to bus routes:
In the main() function, use the subscribe_user() method to add user subscriptions:
   ```python
        notification_system.subscribe_user("user1", "672", "672", 0, "博仁醫院")
        notification_system.subscribe_user("user2", "藍29", "藍29", 1, "福星公園")
   ```
