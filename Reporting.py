import matplotlib.pyplot as plt
import matplotlib.dates as DateFormatter
import sqlite3
import statistics
from datetime import datetime

class Reporting:
    def __init__(self, db_name="internet_monitor.db"):
        self.db_name = db_name

    def generate_report(self, days=1):
        hours = days * 24
        """Generate statistics report for the last N hours"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM network_logs 
            WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp DESC
        ''', (hours,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print(f"No data found for the last {hours} hours")
            return
        
        print(f"\n{'='*60}")
        print(f"Network Statistics - Last {hours} Hours")
        print(f"{'='*60}")
        print(f"Total measurements: {len(rows)}")
        
        # Filter valid measurements
        latencies = [r[2] for r in rows if r[2] is not None]
        downloads = [r[4] for r in rows if r[4] is not None]
        uploads = [r[5] for r in rows if r[5] is not None]
        packet_losses = [r[3] for r in rows if r[3] is not None]
        online_count = sum(1 for r in rows if r[6] == 'online')
        
        if latencies:
            print(f"\nPing Latency:")
            print(f"  Average: {statistics.mean(latencies):.2f} ms")
            print(f"  Min: {min(latencies):.2f} ms")
            print(f"  Max: {max(latencies):.2f} ms")
        
        if packet_losses:
            print(f"\nPacket Loss:")
            print(f"  Average: {statistics.mean(packet_losses):.2f}%")
            print(f"  Max: {max(packet_losses):.2f}%")
        
        if downloads:
            print(f"\nDownload Speed:")
            print(f"  Average: {statistics.mean(downloads):.2f} Mbps")
            print(f"  Min: {min(downloads):.2f} Mbps")
            print(f"  Max: {max(downloads):.2f} Mbps")
        
        if uploads:
            print(f"\nUpload Speed:")
            print(f"  Average: {statistics.mean(uploads):.2f} Mbps")
            print(f"  Min: {min(uploads):.2f} Mbps")
            print(f"  Max: {max(uploads):.2f} Mbps")
        
        uptime = (online_count / len(rows)) * 100
        print(f"\nUptime: {uptime:.2f}% ({online_count}/{len(rows)} measurements)")
        print(f"{'='*60}\n")
    
    def plot_graphs(self, days=1):
        hours = days * 24
        """Generate visualization graphs"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, ping_latency, packet_loss, download_speed, upload_speed
            FROM network_logs 
            WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp ASC
        ''', (hours,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print(f"No data to plot for the last {hours} hours")
            return
        
        timestamps = [datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') for r in rows]
        latencies = [r[1] for r in rows]
        packet_losses = [r[2] for r in rows]
        downloads = [r[3] for r in rows]
        uploads = [r[4] for r in rows]
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Network Performance - Last {hours} Hours', fontsize=16)
        
        # Ping Latency
        axes[0, 0].plot(timestamps, latencies, marker='o', linestyle='-', markersize=3)
        axes[0, 0].set_title('Ping Latency')
        axes[0, 0].set_ylabel('Latency (ms)')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        
        # Packet Loss
        axes[0, 1].plot(timestamps, packet_losses, marker='o', linestyle='-', 
                       markersize=3, color='orange')
        axes[0, 1].set_title('Packet Loss')
        axes[0, 1].set_ylabel('Loss (%)')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        
        # Download Speed
        axes[1, 0].plot(timestamps, downloads, marker='o', linestyle='-', 
                       markersize=3, color='green')
        axes[1, 0].set_title('Download Speed')
        axes[1, 0].set_ylabel('Speed (Mbps)')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        
        # Upload Speed
        axes[1, 1].plot(timestamps, uploads, marker='o', linestyle='-', 
                       markersize=3, color='red')
        axes[1, 1].set_title('Upload Speed')
        axes[1, 1].set_ylabel('Speed (Mbps)')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        
        plt.tight_layout()
        filename = f'network_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Graph saved as '{filename}'")
        plt.show()