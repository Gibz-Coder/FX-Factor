# Continuous Forex Trading Dashboard

## ✅ Yes, This App Runs Continuously!

The dashboard is designed to run 24/7 with automatic data refresh. Here are your options:

---

## **Option 1: Production Mode (Recommended) 🚀**

Run both the dashboard AND background scheduler with automatic data refresh:

```powershell
cd d:\PythonProject\web_scraper
C:/Python312/python.exe start_app.py
```

This will:

- ✓ Start Streamlit dashboard on `http://localhost:8501`
- ✓ Start background scheduler for automatic data refresh
- ✓ Refresh economic calendar every **30 minutes**
- ✓ Refresh news articles every **15 minutes**
- ✓ Refresh prices every **5 minutes**
- ✓ Monitor and auto-restart if processes die
- ✓ Log all activities to `logs/scheduler.log`

**Press Ctrl+C to stop**

---

## **Option 2: Dashboard Only (Quick Test)**

If you just want the dashboard without automatic refresh:

```powershell
cd d:\PythonProject\web_scraper
C:/Python312/python.exe -m streamlit run dashboard.py
```

Access: `http://localhost:8501`

---

## **Option 3: Scheduler Only (Background Worker)**

Run data refresh in the background without dashboard:

```powershell
cd d:\PythonProject\web_scraper
C:/Python312/python.exe scheduler.py
```

Logs go to `logs/scheduler.log`

---

## **Monitoring & Status**

### Check Scheduler Activity

```powershell
Get-Content logs/scheduler.log -Tail 50 -Wait
```

### View Last Update Times

```powershell
Get-Content data/refresh_log.json
```

### Kill Running Processes

```powershell
# Kill all Python processes
Get-Process python | Stop-Process -Force

# Or specifically:
Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.Name -like "*streamlit*"} | Stop-Process -Force
```

---

## **Refresh Schedule**

| Data Source       | Interval | Purpose                                       |
| ----------------- | -------- | --------------------------------------------- |
| Economic Calendar | 30 min   | Latest events from ForexFactory               |
| News Articles     | 15 min   | Current market sentiment from Reuters         |
| Price Data        | 5 min    | Latest EURUSD, GBPUSD, GOLDUSD, USDJPY prices |

---

## **Architecture**

```
┌─────────────────────────────────────────────┐
│     start_app.py (Main Manager)             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  Process 1: Streamlit Dashboard        │ │
│  │  Port: 8501                            │ │
│  │  Status: LIVE                          │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  Process 2: APScheduler                │ │
│  │  Tasks: 3 (calendar, news, prices)     │ │
│  │  Status: RUNNING                       │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  Auto-restart on process failure            │
└─────────────────────────────────────────────┘
```

---

## **Dashboard Features (Always-On)**

Once running, the dashboard displays:

### 📅 **Upcoming Economic Events**

- Auto-updates every 30 minutes
- Shows impact, forecast, previous values
- AI-generated trading signals (BUY/SELL/HOLD)

### 💡 **Trading Signals**

- Real-time sentiment for EURUSD, GBPUSD, GOLDUSD, USDJPY
- Confidence levels
- Source attribution

### 📰 **Market News**

- Latest articles updated every 15 minutes
- Organized by currency pair
- Rapid-fire market intelligence

### 📊 **Volatility Forecast**

- Based on upcoming events
- Color-coded (Low → High → Very High)
- Event counting per pair

---

## **Customization**

### Change Refresh Intervals

Edit `scheduler.py`, lines 63-89:

```python
# Change from 30 minutes to 60 minutes
self.scheduler.add_job(
    self.refresh_calendar,
    trigger=IntervalTrigger(minutes=60),  # ← Edit here
    ...
)
```

### Add/Remove Trading Pairs

Edit `dashboard.py`, line 68:

```python
default=['EURUSD', 'GBPUSD', 'GOLDUSD', 'USDJPY', 'AUDUSD']
```

### Change Timezone

Edit `scheduler.py`, line 47:

```python
'-a', 'timezone=America/New_York',  # ← Change here
```

---

## **Troubleshooting**

### Dashboard won't start

```powershell
# Clear Streamlit cache
Remove-Item $env:APPDATA\.streamlit -Recurse -Force
C:/Python312/python.exe start_app.py
```

### Scheduler not running

```powershell
# Check logs
Get-Content logs/scheduler.log -Tail 100
```

### Port 8501 already in use

```powershell
# Find and kill process using port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### NumPy compatibility issues

```powershell
# Downgrade NumPy if needed
C:/Python312/python.exe -m pip install "numpy<2"
```

---

## **Production Deployment**

### Windows Task Scheduler

Create a scheduled task to auto-start on boot:

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Python312\python.exe" -Argument "d:\PythonProject\web_scraper\start_app.py" -WorkingDirectory "d:\PythonProject\web_scraper"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "ForexTradingDashboard" -Description "Continuous Forex Trading Dashboard with Background Scheduler"
```

### Docker Deployment

```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start_app.py"]
```

---

## **Key Files**

| File                  | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `start_app.py`        | Main entry point (starts both dashboard + scheduler) |
| `scheduler.py`        | Background task scheduler                            |
| `dashboard.py`        | Streamlit UI                                         |
| `realtime_manager.py` | Data loading & caching                               |
| `event_analyzer.py`   | Probability predictions                              |
| `logs/scheduler.log`  | Activity log                                         |

---

## **Summary**

✅ **The app runs continuously** with automatic data refresh  
✅ **Production-ready** with process monitoring and auto-restart  
✅ **Fully customizable** refresh intervals and trading pairs  
✅ **Zero downtime** design with graceful error handling

**Start with:** `python start_app.py` 🚀
