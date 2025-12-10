from InternetMonitor import InternetMonitor 
if __name__ == "__main__":
    monitor = InternetMonitor()

    print("Internet Monitor with Notifications")
    print("="*50)
    print("1. Run continuous monitoring")
    print("2. Run single test")
    print("3. Generate report")
    print("4. Generate graphs")
    
    if __debug__:
        choice = '1'
    else:   
        choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        monitor.start_continuous()
    elif choice == '2':
        monitor.start_test(simple_test=True)
    elif choice == '3':        
        monitor.generate_report(int(input("Enter number of days for report (default 1): ") or 1))
    elif choice == '4':
        monitor.plot_graphs(int(input("Enter number of days for graph (default 1): ") or 1))
    else:
        print("Invalid choice")