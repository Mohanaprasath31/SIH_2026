"""Small offline demo dataset used only when Supabase is unavailable."""

CAMERAS = [
    {"camera_id": "demo-camera-001", "name": "North Junction", "location": "POINT(78.4867 17.3850)", "road": "Central Avenue", "direction": "Northbound", "zone": "Zone A", "status": "active"},
    {"camera_id": "demo-camera-002", "name": "Civic Center", "location": "POINT(78.4767 17.3950)", "road": "Civic Road", "direction": "Southbound", "zone": "Zone A", "status": "active"},
    {"camera_id": "demo-camera-003", "name": "East Interchange", "location": "POINT(78.4967 17.3750)", "road": "Ring Road", "direction": "Eastbound", "zone": "Zone B", "status": "active"},
    {"camera_id": "demo-camera-004", "name": "West Gate", "location": "POINT(78.4667 17.3650)", "road": "West Link", "direction": "Westbound", "zone": "Zone B", "status": "active"},
    {"camera_id": "demo-camera-005", "name": "South Terminal", "location": "POINT(78.5067 17.3550)", "road": "Terminal Road", "direction": "Southbound", "zone": "Zone C", "status": "active"},
]

OBSERVATIONS = [
    {"observation_id": "demo-observation-001", "camera_id": "demo-camera-001", "plate_number": "DEMO-001", "timestamp": "2026-09-20T08:00:00+00:00", "location": "POINT(78.4867 17.3850)", "ocr_confidence": 0.98, "vehicle_type": "Car", "direction": "Northbound"},
    {"observation_id": "demo-observation-002", "camera_id": "demo-camera-002", "plate_number": "DEMO-002", "timestamp": "2026-09-20T09:00:00+00:00", "location": "POINT(78.4767 17.3950)", "ocr_confidence": 0.97, "vehicle_type": "SUV", "direction": "Southbound"},
    {"observation_id": "demo-observation-003", "camera_id": "demo-camera-003", "plate_number": "DEMO-003", "timestamp": "2026-09-20T10:00:00+00:00", "location": "POINT(78.4967 17.3750)", "ocr_confidence": 0.96, "vehicle_type": "Truck", "direction": "Eastbound"},
    {"observation_id": "demo-observation-004", "camera_id": "demo-camera-004", "plate_number": "DEMO-004", "timestamp": "2026-09-20T11:00:00+00:00", "location": "POINT(78.4667 17.3650)", "ocr_confidence": 0.99, "vehicle_type": "Motorcycle", "direction": "Westbound"},
    {"observation_id": "demo-observation-005", "camera_id": "demo-camera-005", "plate_number": "DEMO-005", "timestamp": "2026-09-20T12:00:00+00:00", "location": "POINT(78.5067 17.3550)", "ocr_confidence": 0.95, "vehicle_type": "Bus", "direction": "Southbound"},
]

WATCHLIST = [
    {"plate_number": "DEMO-001", "category": "Review Required", "priority": "High", "status": "Active", "validity": None},
    {"plate_number": "DEMO-002", "category": "Review Required", "priority": "Medium", "status": "Active", "validity": None},
    {"plate_number": "DEMO-003", "category": "Review Required", "priority": "Low", "status": "Active", "validity": None},
    {"plate_number": "DEMO-004", "category": "Review Required", "priority": "High", "status": "Active", "validity": None},
    {"plate_number": "DEMO-005", "category": "Review Required", "priority": "Medium", "status": "Active", "validity": None},
]

ALERTS = [
    {"alert_id": f"demo-alert-{index:03d}", "plate_number": item["plate_number"], "camera_id": OBSERVATIONS[index - 1]["camera_id"], "alert_type": item["category"], "timestamp": OBSERVATIONS[index - 1]["timestamp"], "severity": item["priority"], "confidence": OBSERVATIONS[index - 1]["ocr_confidence"], "status": "New", "created_at": OBSERVATIONS[index - 1]["timestamp"]}
    for index, item in enumerate(WATCHLIST, 1)
]
