## Monitoring Stack
- Prometheus
- Blackbox Exporter
- Grafana

## Run
docker compose up -d

## URLs
Grafana: http://localhost:3000  
Prometheus: http://localhost:9090  


### Infrastructure issue
DNS or core infrastructure failure  
All systems are unreachable

### Network (Transport) issue
Infrastructure is healthy, but ports or connectivity fail  
Network problem

### Application issue
Infrastructure and network are healthy, but the application returns errors  
Application problem

## Why Layer Separation
Separating monitoring by layer helps identify the root cause faster:
Infrastructure → DNS, core services  
Transport → Network, ports, connectivity  
Application → APIs, web services  


### Upload changes
git add .  
git commit -m "update dashboard / config"  
git push  

### Update project on another machine
git pull
