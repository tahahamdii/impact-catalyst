def save_report(collection, report_data):
    try:
        collection.insert_one(report_data)
        print("Report saved successfully!")
    except Exception as e:
        print(f"Error saving report: {e}")