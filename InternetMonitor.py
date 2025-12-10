from Database import Database
from Reporting import Reporting
import speedtest
import os, subprocess, re, configparser, time, threading, datetime, io
from plyer import notification
from TCPMessenger import TCPMessenger
class InternetMonitor:
    def __init__(self, db_name="internet_monitor.db", config_file="monitor.ini"):
        self.reporting = Reporting(db_name)
        self.db = Database(db_name)
        self.config_file = config_file
        self.db.setup_db()
        self.config = self.load_config()
        if __debug__:
            self.messenger = TCPMessenger(self.config.get('TCPDebugSettings', 'host'), self.config.getint('TCPDebugSettings', 'port'))
        else:
            self.messenger = TCPMessenger(self.config.get('TCPSettings', 'host'), self.config.getint('TCPSettings', 'port'))
        self.last_status = None
        self.running = False
        self.running_thread = None

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.config = config
        else:
            self.create_config(config)
        return config

    def create_config(self, config):
        config['Settings'] = {
            'ping_host': '8.8.8.8',
            'ping_count': '10',
            'interval_minutes': '10'
            }
        config['Thresholds'] = {
            'high_latency_ms': '200',
            'packet_loss_percent': '10',
            'low_download_mbps': '50'
        }
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"Error creating config file: {e}")

    def send_notification(self, title, message, timeout=10):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Internet Monitor",
                timeout=timeout
            )
        except Exception as e:
            print(f"Error sending notification: {e}")

    def ping_test(self):
        host = self.config.get('Settings', 'ping_host')
        count = self.config.get('Settings', 'ping_count')
        
        try:
            output = subprocess.run(
                ["ping", "-n", count, host], 
                capture_output=True, 
                text=True,
                timeout=60
            ).stdout

            latency_match = re.search(r'Average = (\d+)ms', output)
            loss_match = re.search(r'\((\d+)% loss\)', output)
            
            latency = float(latency_match.group(1)) if latency_match else None
            packet_loss = float(loss_match.group(1)) if loss_match else 10
            return latency, packet_loss

        except Exception as e:
            print(f"Error in ping_test: {e}")
            return None, 100
        
    def speed_test(self, simple_test=False):
        try:
            st = speedtest.Speedtest(secure=True)
            download_speed = st.download() / 1_000_000
            upload_speed = st.upload() / 1_000_000
            return download_speed, upload_speed
        except Exception as e:
            print(f"Error in speed_test: {e}")
            return None, None
        
    def start_test(self, simple_test=False, for_telegram=False):
        builder = io.StringIO()
        if not for_telegram:
            builder.write(datetime.datetime.now().strftime("\n[%Y-%m-%d %H:%M:%S] - Starting internet test\n"))
        latency, packet_loss = self.ping_test()
        builder.write("Speed Test:\n")
        download, upload = self.speed_test()
        if download is not None:
            builder.write(f" Download: {download:.2f} Mbps\n Upload: {upload:.2f} Mbps\n")
        
        builder.write(f" Latency: {latency}ms\n Packet Loss: {packet_loss}%\n")
        status = 'online' if latency is not None and packet_loss < 100 else 'offline'

        if not simple_test:            
            self.db.insert_log(latency, packet_loss, download, upload, status)
        
        high_latency = self.config.getint('Thresholds', 'high_latency_ms')
        packet_loss_threshold = self.config.getfloat('Thresholds', 'packet_loss_percent')
        low_download = self.config.getint('Thresholds', 'low_download_mbps')

        if status == 'online':
            if latency and latency > high_latency:
                self.send_notification(
                    "⚠️ High Latency Detected",
                    f"Current latency: {latency:.0f}ms (threshold: {high_latency}ms)"
                )
            if packet_loss > packet_loss_threshold:
                self.send_notification(
                    "⚠️ Packet Loss Detected",
                    f"Current packet loss: {packet_loss:.1f}% (threshold: {packet_loss_threshold}%)"
                )
            if download and download < low_download:
                try:
                    self.messenger.send_text("slow_internet")
                except Exception as e:
                    print(f"Error sending TCP message: {e}")
                self.send_notification(
                    "⚠️ Slow Download Speed",
                    f"Current speed: {download:.1f} Mbps (threshold: {low_download} Mbps)"
                )
        
        self.last_status = status
        if for_telegram:
            return builder.getvalue()
        else:
            print(builder.getvalue())

    def start_continuous(self):
        if not self.running:
            self.running = True
            self.running_thread = threading.Thread(target=self.run_continuous)
            self.running_thread.start()
            self.messenger.set_text_callback(self.on_message_received)
            self.tcp_thread = threading.Thread(target=self.messenger.connect)
            self.tcp_thread.start()

    def run_continuous(self):
        interval = self.config.getint('Settings', 'interval_minutes')
        print(f"Starting continuous monitoring (every {interval} minutes)")
        print("Press Ctrl+C to stop")
        try:
            while True:
                if not __debug__:
                    self.start_test()
                time.sleep(interval * 60)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped manually.")
            self.send_notification(
                "🛑 Internet Monitor Stopped",
                "Monitoring has been stopped"
            )

    def on_message_received(self, message):
        if message['type'] == 'text':
            if message['title'] == 'speed_test_results_report':
                content = self.reporting.generate_report(1, for_telegram=True)
                self.messenger.send_text("speed_test_results_report", content, chatId=message['chatId'], messageId=message['messageId'])
            elif message['title'] == 'speed_test_results_graph':
                graph_path = self.reporting.plot_graphs(1, for_telegram=True)
                self.messenger.send_image(graph_path, "speed_test_results_graph", chatId=message['chatId'], messageId=message['messageId'])
            elif message['title'] == 'speed_test_start':
                content = self.start_test(for_telegram=True, simple_test=True)
                self.messenger.send_text("speed_test_start", content, chatId=message['chatId'], messageId=message['messageId'])

    def generate_report(self, days=1):
        print(self.reporting.generate_report(days))

    def plot_graphs(self, days=1):
        self.reporting.plot_graphs(days)
