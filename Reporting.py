import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3, statistics, os, io
from datetime import datetime


class Reporting:
    def __init__(self, db_name="internet_monitor.db"):
        self.db_name = db_name
        
    def generate_report(self, days=1, for_telegram=False):
        builder = io.StringIO()
        hours = days * 24
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
            builder.write(f"No data found for the last {hours} hours \n")
            return
        
        if for_telegram:
            builder.write("\n")
        else:
            builder.write(f"\n{'='*60}\n")
        builder.write(f"Network Statistics - Last {hours} Hours\n")
        if for_telegram:
            builder.write("\n")
        else:
            builder.write(f"\n{'='*60}\n")

        builder.write(f"Total measurements: {len(rows)}\n")
        
        # Filter valid measurements
        latencies = [r[2] for r in rows if r[2] is not None]
        downloads = [r[4] for r in rows if r[4] is not None]
        uploads = [r[5] for r in rows if r[5] is not None]
        packet_losses = [r[3] for r in rows if r[3] is not None]
        online_count = sum(1 for r in rows if r[6] == 'online')
        
        if latencies:
            builder.write(f"\nPing Latency:\n")
            builder.write(f"  Average: {statistics.mean(latencies):.2f} ms\n")
            builder.write(f"  Min: {min(latencies):.2f} ms\n")
            builder.write(f"  Max: {max(latencies):.2f} ms\n")
        
        if packet_losses:
            builder.write(f"\nPacket Loss:\n")
            builder.write(f"  Average: {statistics.mean(packet_losses):.2f}%\n")
            builder.write(f"  Max: {max(packet_losses):.2f}%\n")
        
        if downloads:
            builder.write(f"\nDownload Speed:\n")
            builder.write(f"  Average: {statistics.mean(downloads):.2f} Mbps\n")
            builder.write(f"  Min: {min(downloads):.2f} Mbps\n")
            builder.write(f"  Max: {max(downloads):.2f} Mbps\n")
        
        if uploads:
            builder.write(f"\nUpload Speed:")
            builder.write(f"  Average: {statistics.mean(uploads):.2f} Mbps\n")
            builder.write(f"  Min: {min(uploads):.2f} Mbps\n")
            builder.write(f"  Max: {max(uploads):.2f} Mbps\n")
        
        uptime = (online_count / len(rows)) * 100
        builder.write(f"\nUptime: {uptime:.2f}% ({online_count}/{len(rows)} measurements)\n")
        if for_telegram:
            builder.write("\n")
        else:
            builder.write(f"\n{'='*60}\n")

        return builder.getvalue()
    
    def plot_graphs(self, days=1, for_telegram=False):
        hours = days * 24
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
        
        fig, ax1 = plt.subplots(figsize=(16, 8))
        fig.suptitle(f'Network Performance - Last {hours} Hours', fontsize=16, y=0.98)
        
        def format_date_labels(timestamps):
            labels = []
            last_date = None
            for ts in timestamps:
                current_date = ts.strftime('%m/%d')
                if current_date != last_date:
                    labels.append(f"{current_date}\n{ts.strftime('%H:%M')}")
                    last_date = current_date
                else:
                    labels.append(ts.strftime('%H:%M'))
            return labels
        
        x_labels = format_date_labels(timestamps)
        x_positions = range(len(timestamps))
        
        color1 = 'tab:blue'
        ax1.set_xlabel('Time', fontsize=11)
        ax1.set_ylabel('Ping Latency (ms)', color=color1, fontsize=11)
        line1 = ax1.plot(x_positions, latencies, color=color1, marker='o', linestyle='-', 
                        markersize=4, linewidth=2, label='Ping Latency (ms)')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        ax2 = ax1.twinx()
        color2 = 'tab:green'
        color3 = 'tab:red'
        ax2.set_ylabel('Speed (Mbps)', fontsize=11)
        line2 = ax2.plot(x_positions, downloads, color=color2, marker='s', linestyle='-', 
                        markersize=4, linewidth=2, label='Download (Mbps)')
        line3 = ax2.plot(x_positions, uploads, color=color3, marker='^', linestyle='-', 
                        markersize=4, linewidth=2, label='Upload (Mbps)')
        
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        color4 = 'tab:orange'
        ax3.set_ylabel('Packet Loss (%)', color=color4, fontsize=11)
        line4 = ax3.plot(x_positions, packet_losses, color=color4, marker='D', linestyle='-', 
                        markersize=4, linewidth=2, label='Packet Loss (%)')
        ax3.tick_params(axis='y', labelcolor=color4)
        ax3.set_ylim(0, 100)  # Fixed range: 0% to 100%
        ax3.set_yticks([0, 25, 50, 75, 100])
        
        tick_positions = x_positions[::max(1, len(x_positions)//15)]
        tick_labels = [x_labels[i] for i in range(0, len(x_labels), max(1, len(x_labels)//15))]
        ax1.set_xticks(tick_positions)
        ax1.set_xticklabels(tick_labels, rotation=0, ha='center')
        
        lines = line1 + line2 + line3 + line4
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.9)
        
        plt.tight_layout()
        filename = f'network_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        self.cleanup_old_reports()
        if for_telegram:
            return filename
        else:
            plt.show()

    def cleanup_old_reports(self, max_reports=10):
        import glob        
        report_files = glob.glob('network_report_*.png')        
        if len(report_files) > max_reports:
            report_files.sort(key=os.path.getmtime)
            files_to_delete = len(report_files) - max_reports
            for i in range(files_to_delete):
                try:
                    os.remove(report_files[i])
                    print(f"🗑️  Deleted old report: {report_files[i]}")
                except Exception as e:
                    print(f"⚠️  Could not delete {report_files[i]}: {e}")