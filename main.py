from InternetMonitor import InternetMonitor 
from Reporting import Reporting
if __name__ == "__main__":
    monitor = InternetMonitor()
    reporting = Reporting()
    
    print("Internet Monitor with Notifications")
    print("="*50)
    print("1. Run continuous monitoring (every 10 minutes)")
    print("2. Run single test")
    print("3. Generate report (amount of days asked next)")
    print("4. Generate graphs (amount of days asked next)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        monitor.run_continuous()
    elif choice == '2':
        monitor.start_test(simple_test=True)
    elif choice == '3':        
        reporting.generate_report(input("Enter number of days for report (default 1): ") or 1)
    elif choice == '4':
        reporting.plot_graphs(input("Enter number of days for graph (default 1): ") or 1)
    else:
        print("Invalid choice")