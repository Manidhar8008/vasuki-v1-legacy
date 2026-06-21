def run_agent():
    print("VASUKI AGENT STARTED...")

    while True:
        try:
            print("Loop tick started")

            files = get_unprocessed_files()
            print("Files found:", len(files))

            for file_path, ext in files:
                print("Processing:", file_path)

        except Exception as e:
            print("AGENT ERROR:", e)

        time.sleep(5)
