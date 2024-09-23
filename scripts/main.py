#! venv/bin/ python3.10

import configparser
import os
import sys
from datetime import datetime

import requests
from PyQt5.QtCore import QRectF, QSize, Qt, QTimer
from PyQt5.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QMovie,
                         QPainter, QPainterPath, QPalette, QPixmap)
from PyQt5.QtWidgets import (QApplication, QDialog, QFormLayout, QFrame,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QScrollArea, QSizePolicy, QSpinBox,
                             QVBoxLayout, QWidget)


def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and PyInstaller """
    try:
        # PyInstaller creates a temporary folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


config = configparser.ConfigParser()
config_path = resource_path('config/config.ini')
config.read(config_path)


class AnimatedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie = None

    def setMovie(self, movie):
        self.movie = movie
        super().setMovie(movie)
        self.movie.frameChanged.connect(self.update_frame)

    def update_frame(self):
        frame = self.movie.currentPixmap()
        if not frame.isNull():
            # Scale the frame to the size of the label, maintaining aspect ratio
            scaled_frame = frame.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_frame)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.movie and self.movie.state() == QMovie.Running:
            self.update_frame()


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.config = configparser.ConfigParser()
        config_path = resource_path('config/config.ini')
        self.config.read(config_path)

        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        # API Key
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(
            self.config.get('openweathermap', 'api_key'))
        layout.addRow('API Key:', self.api_key_input)

        # Default City
        self.city_input = QLineEdit(self)
        self.city_input.setText(self.config.get(
            'default_city', 'city_location', fallback='London, UK'))
        layout.addRow('Default City:', self.city_input)

        # Update Interval
        self.update_interval_input = QSpinBox(self)
        self.update_interval_input.setRange(
            60, 86400)  # Between 1 minute and 24 hours
        self.update_interval_input.setValue(self.config.getint(
            'refresh', 'update_interval', fallback=600))
        layout.addRow('Update Interval (seconds):', self.update_interval_input)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def save_settings(self):
        # Update the config object
        self.config.set('openweathermap', 'api_key', self.api_key_input.text())
        self.config.set('default_city', 'city_location',
                        self.city_input.text())
        self.config.set('refresh', 'update_interval', str(
            self.update_interval_input.value()))

        # Write changes to the config.ini file
        config_path = resource_path('config/config.ini')

        with open(config_path, 'w') as configfile:
            self.config.write(configfile)

        # Inform the user
        QMessageBox.information(self, 'Settings', 'Settings have been saved.')
        self.accept()


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.current_city = None
        self.first_load = True
        self._debugging = False
        self.initUI()

        # Set up the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_weather)
        # Convert seconds to milliseconds
        self.timer.start(self.update_interval * 1000)

    def load_config(self):
        self.config = configparser.ConfigParser()
        config_path = resource_path('config/config.ini')
        self.config.read(config_path)
        self.api_key = self.config.get('openweathermap', 'api_key')
        self.city_location = self.config.get(
            'default_city', 'city_location', fallback='London, UK')
        self.update_interval = self.config.getint(
            'refresh', 'update_interval', fallback=600)  # In seconds

    def initUI(self):
        self.setWindowTitle('Weather App')

        # Set gradient background
        self.updateGradientBackground()

        # Input field for the city name
        self.city_input = QLineEdit(self)
        self.city_input.setPlaceholderText('Enter city name')
        self.city_input.setFont(QFont('Arial', 14))
        self.city_input.setStyleSheet(
            "padding: 5px; border: 1px solid #ccc; border-radius: 5px;")
        self.city_input.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Button to trigger weather fetching
        self.get_weather_btn = QPushButton('', self)
        self.get_weather_btn.clicked.connect(self.show_weather)
        self.get_weather_btn.setFixedSize(40, 40)
        self.get_weather_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )

        # Set the search icon
        search_icon = QIcon(resource_path('icons/research.png'))
        self.get_weather_btn.setIcon(search_icon)
        self.get_weather_btn.setIconSize(QSize(24, 24))

        # Button to open settings
        self.settings_btn = QPushButton('', self)
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FFA500;
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
            """
        )

        # Set the settings icon
        # You need to have a settings icon in the icons folder
        settings_icon = QIcon(resource_path('icons/settings.png'))
        self.settings_btn.setIcon(settings_icon)
        self.settings_btn.setIconSize(QSize(24, 24))

        # Label to display the weather information
        self.weather_info = QLabel('', self)
        self.weather_info.setFont(QFont('Arial', 12))
        self.weather_info.setStyleSheet("color: white;")
        self.weather_info.setAlignment(Qt.AlignCenter)

        # Label to display the weather icon
        self.icon_label = QLabel('', self)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # Create a horizontal layout for the input field and buttons
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.city_input)
        search_layout.addWidget(self.get_weather_btn)
        search_layout.addWidget(self.settings_btn)
        search_layout.setSpacing(10)
        search_layout.setContentsMargins(10, 10, 10, 0)

        # Hourly forecast layout
        self.hourly_layout = QHBoxLayout()
        self.hourly_layout.setSpacing(10)

        # Create a frame for hourly forecast
        self.hourly_frame = QFrame()
        self.hourly_frame.setLayout(self.hourly_layout)
        self.hourly_frame.setStyleSheet("")

        # Scroll area for hourly forecast
        self.hourly_scroll_area = QScrollArea()
        self.hourly_scroll_area.setWidgetResizable(True)
        self.hourly_scroll_area.setWidget(self.hourly_frame)
        self.hourly_scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        self.hourly_scroll_area.viewport().setStyleSheet("background: transparent;")
        self.hourly_scroll_area.setFixedHeight(150)

        # Daily forecast layout
        self.forecast_layout = QHBoxLayout()
        self.forecast_layout.setSpacing(10)

        # Create a frame for daily forecast
        self.forecast_frame = QFrame()
        self.forecast_frame.setLayout(self.forecast_layout)
        self.forecast_frame.setStyleSheet("")

        # Scroll area for daily forecast
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.forecast_frame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        self.scroll_area.setFixedHeight(150)

        # Layout setup
        layout = QVBoxLayout()
        layout.addLayout(search_layout)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.weather_info)

        next5hours_label = QLabel("<b>Next 5 Hours:</b>", self)
        next5hours_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(next5hours_label)
        layout.addWidget(self.hourly_scroll_area)

        next5days_label = QLabel("<b>Next 5 Days:</b>", self)
        next5days_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(next5days_label)

        layout.addWidget(self.scroll_area)
        layout.setContentsMargins(10, 0, 10, 10)

        self.setLayout(layout)
        self.resize(500, 700)
        self.show()

        # Load weather data on startup
        self.show_weather()

    def updateGradientBackground(self):
        # Set gradient background
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor('#2196F3'))  # Start color (blue)
        gradient.setColorAt(1.0, QColor('#4CAF50'))  # End color (green)
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGradientBackground()

    def show_weather(self):
        if self._debugging:
            print(f"{self.api_key}")
            # self._debugging = False

        if self.first_load:
            self.first_load = False
            self.current_city = self.city_location
        else:
            city = self.city_input.text()
            if city:
                self.current_city = city

        city = self.current_city

        if city:
            # Get coordinates of the city
            geo_url = (
                f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={self.api_key}'
            )
            geo_response = requests.get(geo_url)
            if geo_response.status_code == 200 and geo_response.json():
                geo_data = geo_response.json()[0]
                lat = geo_data['lat']
                lon = geo_data['lon']

                # Fetch current weather data
                weather_url = (
                    f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric'
                )
                weather_response = requests.get(weather_url)
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    temp = weather_data['main']['temp']
                    description = weather_data['weather'][0]['description']
                    icon_code = weather_data['weather'][0]['icon']
                    humidity = weather_data['main']['humidity']
                    wind_speed = weather_data['wind']['speed']

                    # Fetch the weather icon
                    icon_url = f'http://openweathermap.org/img/wn/{icon_code}@2x.png'
                    icon_response = requests.get(icon_url)
                    pixmap = QPixmap()
                    pixmap.loadFromData(icon_response.content)
                    self.icon_label.setPixmap(pixmap)

                    # Format the weather details
                    weather_details = (
                        f"<b>Temperature:</b> {int(temp)}°C<br>"
                        f"<b>Description:</b> {description.title()}<br>"
                        f"<b>Humidity:</b> {humidity}%<br>"
                        f"<b>Wind Speed:</b> {wind_speed} m/s"
                    )
                    self.weather_info.setText(weather_details)

                    # Fetch 5-day forecast data
                    forecast_url = (
                        f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric'
                    )
                    if self._debugging:
                        print(f"Forecast URL: {forecast_url}")  # Debugging

                    forecast_response = requests.get(forecast_url)

                    if self._debugging:
                        # Debugging
                        print(
                            f"Forecast Response Status Code: {forecast_response.status_code}")
                        # Debugging
                        print(
                            f"Forecast Response Text: {forecast_response.text}")

                    if forecast_response.status_code == 200:
                        forecast_data = forecast_response.json()
                        forecast_list = forecast_data['list']

                        # Clear previous hourly forecast widgets
                        for i in reversed(range(self.hourly_layout.count())):
                            widget_to_remove = self.hourly_layout.itemAt(
                                i).widget()
                            self.hourly_layout.removeWidget(widget_to_remove)
                            widget_to_remove.setParent(None)

                        # Display forecasts for the next 5 hours
                        self.display_hourly_forecast(forecast_list)

                        # Process daily forecasts
                        daily_data = {}
                        for entry in forecast_list:
                            date_text = entry['dt_txt']
                            date = date_text.split(' ')[0]

                            if date not in daily_data:
                                daily_data[date] = {
                                    'temps': [],
                                    'icon': entry['weather'][0]['icon'],
                                    'weather': entry['weather'][0]['description'],
                                }

                            daily_data[date]['temps'].append(
                                entry['main']['temp'])

                        # Clear previous daily forecast widgets
                        for i in reversed(range(self.forecast_layout.count())):
                            widget_to_remove = self.forecast_layout.itemAt(
                                i).widget()
                            self.forecast_layout.removeWidget(widget_to_remove)
                            widget_to_remove.setParent(None)

                        # Display forecasts for up to 5 days
                        for date, data in list(daily_data.items())[:5]:
                            avg_temp = int(
                                sum(data['temps']) / len(data['temps']))
                            icon_code = data['icon']
                            description = data['weather']
                            self.add_forecast_widget(
                                date, avg_temp, icon_code, description)
                    else:
                        error_message = forecast_response.json().get('message', 'Unknown error')
                        self.weather_info.setText(
                            f'Error fetching forecast data: {error_message}')

                        if self._debugging:
                            print(
                                f"Error fetching forecast data: {error_message}")
                else:
                    self.weather_info.setText('Error fetching weather data.')
                    self.icon_label.clear()
            else:
                self.weather_info.setText('City not found. Please try again.')
                self.icon_label.clear()
        else:
            self.weather_info.setText('Please enter a city name.')
            self.icon_label.clear()

    def refresh_weather(self):
        if hasattr(self, 'current_city') and self.current_city:
            self.show_weather()

    def display_hourly_forecast(self, forecast_list):
        # Get current time
        now = datetime.now()

        # Find entries for the next 5 hours
        hourly_forecasts = []
        for entry in forecast_list:
            forecast_time = datetime.strptime(
                entry['dt_txt'], '%Y-%m-%d %H:%M:%S')
            if forecast_time > now and len(hourly_forecasts) < 5:
                hourly_forecasts.append(entry)

        for entry in hourly_forecasts:
            self.add_hourly_forecast_widget(entry)

    def add_hourly_forecast_widget(self, entry):
        # Extract data
        forecast_time = datetime.strptime(entry['dt_txt'], '%Y-%m-%d %H:%M:%S')
        time_str = forecast_time.strftime('%H:%M')

        temp = int(entry['main']['temp'])
        icon_code = entry['weather'][0]['icon']

        # Fetch the weather icon
        icon_url = f'http://openweathermap.org/img/wn/{icon_code}.png'
        icon_response = requests.get(icon_url)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_response.content)
        pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)

        # Create labels
        time_label = QLabel(time_str)
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setFont(QFont('Arial', 10))
        time_label.setStyleSheet("color: white;")

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        temp_label = QLabel(f"{temp}°C")
        temp_label.setAlignment(Qt.AlignCenter)
        temp_label.setFont(QFont('Arial', 10))
        temp_label.setStyleSheet("color: white;")

        # Create a vertical layout for the hourly forecast
        v_layout = QVBoxLayout()
        v_layout.addWidget(time_label)
        v_layout.addWidget(icon_label)
        v_layout.addWidget(temp_label)

        # Create a frame for the hourly forecast
        hour_frame = QFrame()
        hour_frame.setLayout(v_layout)
        hour_frame.setFixedWidth(70)
        hour_frame.setStyleSheet("")

        self.hourly_layout.addWidget(hour_frame)

    def add_forecast_widget(self, date_str, temp, icon_code, description):
        # Parse the date string
        date = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = date.strftime('%A')

        # Fetch the weather icon
        icon_url = f'http://openweathermap.org/img/wn/{icon_code}.png'
        icon_response = requests.get(icon_url)
        pixmap = QPixmap()
        pixmap.loadFromData(icon_response.content)
        pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)

        # Create labels
        day_label = QLabel(day_name)
        day_label.setAlignment(Qt.AlignCenter)
        day_label.setFont(QFont('Arial', 10))
        day_label.setStyleSheet("color: white;")

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        temp_label = QLabel(f"{temp}°C")
        temp_label.setAlignment(Qt.AlignCenter)
        temp_label.setFont(QFont('Arial', 10))
        temp_label.setStyleSheet("color: white;")

        # Create a vertical layout for the day's forecast
        v_layout = QVBoxLayout()
        v_layout.addWidget(day_label)
        v_layout.addWidget(icon_label)
        v_layout.addWidget(temp_label)

        # Create a frame for the day's forecast
        day_frame = QFrame()
        day_frame.setLayout(v_layout)
        day_frame.setFixedWidth(80)
        day_frame.setStyleSheet("")

        self.forecast_layout.addWidget(day_frame)

    def open_settings(self):
        settings_window = SettingsWindow(self)
        if settings_window.exec_():
            # Reload configurations
            self.load_config()
            # Restart the timer with the new interval
            self.timer.stop()
            self.timer.start(self.update_interval * 1000)
            # Refresh the weather data
            self.first_load = True  # Force reload of default city
            self.show_weather()

    def paintEvent(self, event):
        # Overriding paintEvent to handle transparency
        path = QPainterPath()
        rect_f = QRectF(self.rect())
        path.addRoundedRect(rect_f, 10.0, 10.0)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(path)
        super().paintEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    sys.exit(app.exec_())
