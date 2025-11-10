# glove_thread.py

import subprocess

def read_from_glove_thread(output_queue, status_queue, c_exe_path, glove_port):
    try:
        process = subprocess.Popen(
            [c_exe_path, glove_port],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        status_queue.put("connected")

        while True:
            output_line = process.stdout.readline()
            if not output_line:
                status_queue.put("disconnected")
                break
            output_queue.put(output_line.strip())

    except FileNotFoundError:
        status_queue.put("error_not_found")
    except Exception as e:
        status_queue.put(f"error_{str(e)}")
    finally:
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()
